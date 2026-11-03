# Route A (KalParso): encoder span tagger + type + tense heads, then the deterministic grounder (ground_entry).
# Runs on Kaggle (CUDA) or locally (MPS/CPU). The released models: KP_DATA=v3 KP_PHINC=1.
# Env: KP_MODELS=muril,xlmr,mdistil  KP_SEEDS=13,42,7,1,2  KP_DATA=v1|v2|v3 (default v2)  KP_PHINC=1 (add data/v3/phinc_dir.jsonl)
#      KP_NTRAIN=30000  KP_EPOCHS=3  KP_CLEAN=1 (drop noisy rows)  KP_TAG=run name  KP_OUT=output dir
#      KP_ONNX=1 (export the first seed)  KP_SAVE=1 (save weights .pt + training history .pkl/.json)
import glob, json, os, pickle, random, sys, time
import numpy as np, torch, torch.nn as nn
from datetime import datetime
from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup

KAG = os.path.exists("/kaggle/input")
SRC = os.path.dirname(glob.glob("/kaggle/input/**/ground.py", recursive=True)[0]) if KAG else \
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC)
from ground import ground_entry
from rules import direction as rules_direction

E = os.environ.get
DATA_KIND = E("KP_DATA", "v2")
ROOT = os.path.dirname(glob.glob(f"/kaggle/input/**/{DATA_KIND}/train.jsonl", recursive=True)[0]) if KAG else \
    os.path.join(SRC, "..", "data", DATA_KIND)
HUMAN = os.path.dirname(glob.glob("/kaggle/input/**/human_test.jsonl", recursive=True)[0]) if KAG else \
    os.path.join(SRC, "..", "data", "human")
OUT = E("KP_OUT", "/kaggle/working" if KAG else os.path.join(SRC, "..", "results", "v2"))
os.makedirs(OUT, exist_ok=True)
ALL = {"muril": ("google/muril-base-cased", 5e-5), "xlmr": ("FacebookAI/xlm-roberta-base", 3e-5),
       "mdistil": ("distilbert/distilbert-base-multilingual-cased", 5e-5)}
MODELS = {k: ALL[k] for k in E("KP_MODELS", "muril,xlmr,mdistil").split(",")}
SEEDS = [int(x) for x in E("KP_SEEDS", "13,42,7,1,2").split(",")]
EPOCHS, BS, MAXLEN = int(E("KP_EPOCHS", 3)), int(E("KP_BS", 32)), 64
NTRAIN = int(E("KP_NTRAIN", 30000))
TAG = E("KP_TAG", DATA_KIND + (f"_n{NTRAIN}" if NTRAIN < 30000 else "") + ("_phinc" if E("KP_PHINC") else ""))
LABELS = ["O"] + [f"{p}-{l}" for l in ["DAY", "WD", "DATE", "TIME", "PART", "DUR"] for p in "BI"]
TYPES, DIRS = ["reminder", "note", "goal"], ["future", "past"]
dev = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
amp = dev.type == "cuda"


def load(p):
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else []


def clean(r):  # v2clean: noise ablation keeps only clean-spelling rows
    return not r["flags"].get("noisy")


SPLITS = {"train": load(f"{ROOT}/train.jsonl"), "dev": load(f"{ROOT}/dev.jsonl"),
          "test_synth": load(f"{ROOT}/test_synth.jsonl"), "test_human": load(f"{HUMAN}/test_human.jsonl")}
if DATA_KIND == "v2clean" or E("KP_CLEAN"): SPLITS["train"] = [r for r in SPLITS["train"] if clean(r)]
SPLITS["train"] = random.Random(0).sample(SPLITS["train"], min(NTRAIN, len(SPLITS["train"])))
if E("KP_PHINC") and os.path.exists(f"{ROOT}/phinc_dir.jsonl"):
    SPLITS["train"] += load(f"{ROOT}/phinc_dir.jsonl")
if E("SMOKE"): SPLITS = {k: v[:300] for k, v in SPLITS.items()}; EPOCHS = 1
print(dev, ROOT, {k: len(v) for k, v in SPLITS.items()}, TAG, flush=True)


def encode(tok, r):
    enc = tok(r["text"], return_offsets_mapping=True, truncation=True, max_length=MAXLEN)
    labs = []
    for s, e in enc["offset_mapping"]:
        if s == e: labs.append(-100); continue
        lab = "O"
        for sp in r.get("spans", []):
            if s >= sp["start"] and e <= sp["end"]:
                lab = ("B-" if s == sp["start"] else "I-") + sp["label"]; break
        labs.append(LABELS.index(lab))
    if r.get("dir_only"):  # weakly labelled real text: trains the tense head only
        labs = [-100] * len(labs)
    return {"ids": enc["input_ids"], "tags": labs, "type": TYPES.index(r["type"]) if r.get("type") in TYPES else -100,
            "dir": DIRS.index(r.get("direction", "future"))}


def batches(rows, shuffle):
    idx = list(range(len(rows)))
    if shuffle: random.shuffle(idx)
    for i in range(0, len(idx), BS):
        b = [rows[j] for j in idx[i:i + BS]]
        L = max(len(x["ids"]) for x in b)
        ids = torch.tensor([x["ids"] + [0] * (L - len(x["ids"])) for x in b])
        att = torch.tensor([[1] * len(x["ids"]) + [0] * (L - len(x["ids"])) for x in b])
        tags = torch.tensor([x["tags"] + [-100] * (L - len(x["tags"])) for x in b])
        yield ids.to(dev), att.to(dev), tags.to(dev), torch.tensor([x["type"] for x in b]).to(dev), \
            torch.tensor([x["dir"] for x in b]).to(dev)


class Tagger(nn.Module):
    def __init__(self, name):
        super().__init__()
        self.enc = AutoModel.from_pretrained(name)
        h = self.enc.config.hidden_size
        self.drop = nn.Dropout(0.1)
        self.tag, self.typ, self.dir = nn.Linear(h, len(LABELS)), nn.Linear(h, 3), nn.Linear(h, 2)

    def forward(self, input_ids, attention_mask):
        x = self.drop(self.enc(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state)
        return self.tag(x), self.typ(x[:, 0]), self.dir(x[:, 0])


def decode_spans(text, offsets, tag_ids):
    spans, cur = [], None
    for (s, e), t in zip(offsets, tag_ids):
        if s == e: continue
        lab = LABELS[t]
        if lab == "O": cur = None; continue
        p, l = lab.split("-")
        if p == "B" or cur is None or cur[0] != l or s > cur[2] + 1:
            cur = [l, s, e]; spans.append(cur)
        else:
            cur[2] = e
    return [(l, text[s:e]) for l, s, e in spans]


@torch.no_grad()
def predict(model, tok, rows):
    model.eval(); out = []
    for i in range(0, len(rows), 128):
        b = rows[i:i + 128]
        enc = tok([r["text"] for r in b], return_offsets_mapping=True, truncation=True, max_length=MAXLEN,
                  padding=True, return_tensors="pt")
        tg, ty, di = model(enc["input_ids"].to(dev), enc["attention_mask"].to(dev))
        pdir = di.softmax(-1)[:, 1].cpu().tolist()
        tg, ty, di = tg.argmax(-1).cpu().tolist(), ty.argmax(-1).cpu().tolist(), di.argmax(-1).cpu().tolist()
        for r, offs, t, y, d, pd in zip(b, enc["offset_mapping"].tolist(), tg, ty, di, pdir):
            spans = decode_spans(r["text"], offs, t)
            typ, a = TYPES[y], datetime.fromisoformat(r["anchor"])
            date, tm = ground_entry(spans, DIRS[d], a, typ, r["text"])
            rd = rules_direction(r["text"])
            date_r, tm_r = ground_entry(spans, rd, a, typ, r["text"])
            out.append({"id": r["id"], "type": typ, "date": date, "time": tm, "direction": DIRS[d], "p_past": round(pd, 4),
                        "spans": spans, "rulesdir": {"date": date_r, "time": tm_r, "direction": rd}})
    return out


def quick(preds, rows):
    g = {r["id"]: r for r in rows}
    ok = [p["type"] == g[p["id"]]["type"] and p["date"] == g[p["id"]]["date"] and p["time"] == g[p["id"]]["time"] for p in preds]
    return 100 * sum(ok) / max(len(ok), 1)


summary = {}
for short, (name, lr) in MODELS.items():
    tok = AutoTokenizer.from_pretrained(name)
    train = [encode(tok, r) for r in SPLITS["train"]]
    for si, seed in enumerate(SEEDS):
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
        model = Tagger(name).to(dev)
        opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
        steps = EPOCHS * (len(train) // BS + 1)
        sch = get_linear_schedule_with_warmup(opt, int(0.06 * steps), steps)
        scaler = torch.amp.GradScaler("cuda", enabled=amp)
        ce = nn.CrossEntropyLoss(ignore_index=-100)
        hist = {"model": name, "seed": seed, "lr": lr, "bs": BS, "epochs": EPOCHS, "ntrain": len(train), "data": DATA_KIND,
                "step": [], "loss": [], "loss_tag": [], "loss_type": [], "loss_dir": [], "lr_curve": [], "epoch_dev_full": [],
                "epoch_time_s": []}
        t0, step = time.time(), 0
        for ep in range(EPOCHS):
            model.train()
            for ids, att, tags, ty, di in batches(train, True):
                with torch.autocast(dev.type, dtype=torch.float16, enabled=amp):
                    a, b, c = model(ids, att)
                    lt, ly, ld = ce(a.reshape(-1, a.size(-1)).float(), tags.reshape(-1)), ce(b.float(), ty), ce(c.float(), di)
                    loss = lt + ly + ld
                opt.zero_grad(); scaler.scale(loss).backward(); scaler.unscale_(opt)
                nn.utils.clip_grad_norm_(model.parameters(), 1.0); scaler.step(opt); scaler.update(); sch.step()
                step += 1
                if step % 25 == 0:
                    for k, v in (("step", step), ("loss", loss.item()), ("loss_tag", lt.item()), ("loss_type", ly.item()),
                                 ("loss_dir", ld.item()), ("lr_curve", sch.get_last_lr()[0])):
                        hist[k].append(v)
            dv = quick(predict(model, tok, SPLITS["dev"][:1000]), SPLITS["dev"][:1000])
            hist["epoch_dev_full"].append(dv); hist["epoch_time_s"].append(time.time() - t0)
            print(short, seed, "epoch", ep, f"loss {loss.item():.4f} dev_full {dv:.1f} {time.time() - t0:.0f}s", flush=True)
        run = f"A2_{short}_{TAG}_s{seed}"
        for split in ["dev", "test_synth", "test_human"]:
            if not SPLITS[split]: continue
            preds = predict(model, tok, SPLITS[split])
            with open(f"{OUT}/{run}.{split}.jsonl", "w") as f:
                for p in preds: f.write(json.dumps(p, ensure_ascii=False) + "\n")
            if split != "test_human": summary[f"{run}/{split}"] = quick(preds, SPLITS[split])
        print(run, {k: round(v, 1) for k, v in summary.items() if k.startswith(run)}, flush=True)
        if E("KP_SAVE", "1") == "1":
            wd = f"{OUT}/weights"; os.makedirs(wd, exist_ok=True)
            torch.save({k: v.half().cpu() for k, v in model.state_dict().items()}, f"{wd}/{run}.pt")
            pickle.dump(hist, open(f"{wd}/{run}.history.pkl", "wb"))
            json.dump(hist, open(f"{wd}/{run}.history.json", "w"))
        if si == 0 and E("KP_ONNX", "1") == "1":
            d = f"{OUT}/{run}_onnx"; os.makedirs(d, exist_ok=True)
            tok.save_pretrained(d)
            model.eval().cpu()
            dummy = tok(["kal shaam 5 baje gym"], return_tensors="pt")
            kw = dict(input_names=["input_ids", "attention_mask"], output_names=["tags", "type", "dir"],
                      dynamic_axes={"input_ids": {0: "b", 1: "t"}, "attention_mask": {0: "b", 1: "t"},
                                    "tags": {0: "b", 1: "t"}, "type": {0: "b"}, "dir": {0: "b"}}, opset_version=17)
            try:
                torch.onnx.export(model, (dummy["input_ids"], dummy["attention_mask"]), f"{d}/model.onnx", dynamo=False, **kw)
                from onnxruntime.quantization import quantize_dynamic, QuantType
                quantize_dynamic(f"{d}/model.onnx", f"{d}/model.int8.onnx", weight_type=QuantType.QInt8)
            except Exception as e:
                print("onnx export failed", e)
            json.dump({"labels": LABELS, "types": TYPES, "dirs": DIRS, "maxlen": MAXLEN}, open(f"{d}/meta.json", "w"))
            model.to(dev)
        del model
        if amp: torch.cuda.empty_cache()
        json.dump(summary, open(f"{OUT}/summary_{TAG}.json", "w"), indent=1)
print("done", flush=True)
