# Route B: small LLM (Qwen3-0.6B) + LoRA on v3 data, short prompt, compact output.
# Two targets: "abs" = the model writes the final date/time; "ir" = the model writes spans + tense and the
# deterministic grounder computes the date. Needs a GPU and internet (pip, llama.cpp for the GGUF export).
# Outputs: predictions, metrics, and an f16 GGUF per target for Ollama.

import subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "peft>=0.13", "gguf", "sentencepiece"], check=False)
# Kaggle ships torchao 0.10, which new peft rejects at import; route B does not use it
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)

import glob, json, os, random, time
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, get_cosine_schedule_with_warmup
from peft import LoraConfig, get_peft_model

SRC = next(iter(glob.glob("/kaggle/input/**/ground.py", recursive=True)), "../src/ground.py").rsplit("/", 1)[0]
DATA = os.path.dirname(next(iter(glob.glob("/kaggle/input/**/v3/train.jsonl", recursive=True)), "../data/v3/train.jsonl"))
HUMAN = os.path.dirname(next(iter(glob.glob("/kaggle/input/**/human_test.jsonl", recursive=True)), "../data/human/x"))
sys.path.insert(0, SRC)
from ground import ground_entry
from evaluate import score

OUT = "/kaggle/working" if os.path.exists("/kaggle/working") else "../results"
BASE = "Qwen/Qwen3-0.6B"
TARGETS = ["ir"]
EPOCHS, BS, MB, LR, SEED = 1, 32, 8, 2e-4, 13
TYPES = ["reminder", "note", "goal"]
dev = "cuda" if torch.cuda.is_available() else "cpu"
SPLITS = {s: [json.loads(l) for l in open(f"{DATA}/{s}.jsonl")] if os.path.exists(f"{DATA}/{s}.jsonl") else []
          for s in ["train", "dev", "test_synth"]}
SPLITS["test_human"] = [json.loads(l) for l in open(f"{HUMAN}/test_human.jsonl")] if os.path.exists(f"{HUMAN}/test_human.jsonl") else []
if os.environ.get("SMOKE"):  # tiny local run to catch bugs before spending GPU time
    SPLITS = {k: v[:96 if k == "train" else 16] for k, v in SPLITS.items()}; BS = 16
print({k: len(v) for k, v in SPLITS.items()})


def prompt(r):
    return f"Now: {r['anchor'].replace('T', ' ')} {r['weekday'][:3]}\nEntry: {r['text']}\nOut:"


def target(r, kind):
    t = "RNG"[TYPES.index(r["type"])]
    if kind == "abs":
        return f" {t} {r['date'] or '-'} {r['time'] or '-'}"
    spans = " ; ".join(f"{r['text'][s['start']:s['end']]}={s['label']}" for s in r["spans"])
    return f" {t} {'P' if r['direction'] == 'past' else 'F'} {spans or '-'}"


def parse(out, r, kind):
    out = out.strip().split("\n")[0]
    parts = out.split(" ", 2)
    typ = {"R": "reminder", "N": "note", "G": "goal"}.get(parts[0] if parts else "", "note")
    if kind == "abs":
        d = parts[1] if len(parts) > 1 and parts[1] != "-" else None
        t = parts[2].split()[0] if len(parts) > 2 and parts[2] != "-" else None
        return {"type": typ, "date": d, "time": t}
    dirn = "past" if len(parts) > 1 and parts[1] == "P" else "future"
    spans = []
    if len(parts) > 2 and parts[2] != "-":
        for chunk in parts[2].split(" ; "):
            if "=" in chunk:
                txt, lab = chunk.rsplit("=", 1)
                spans.append((lab.strip(), txt.strip()))
    d, t = ground_entry(spans, dirn, datetime.fromisoformat(r["anchor"]), typ, r["text"])
    return {"type": typ, "date": d, "time": t, "direction": dirn, "spans": spans}


metrics = {}
for kind in TARGETS:
    random.seed(SEED); torch.manual_seed(SEED)
    tok = AutoTokenizer.from_pretrained(BASE)
    tok.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.float32).to(dev)
    model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, task_type="CAUSAL_LM",
                                             target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                                             "gate_proj", "up_proj", "down_proj"]))
    rows = []
    for r in SPLITS["train"]:
        p, y = tok(prompt(r))["input_ids"], tok(target(r, kind))["input_ids"] + [tok.eos_token_id]
        rows.append((p + y, [-100] * len(p) + y))
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=LR)
    steps = EPOCHS * (len(rows) // BS + 1)
    sch = get_cosine_schedule_with_warmup(opt, int(0.05 * steps), steps)
    model.train(); t0 = time.time()
    for ep in range(EPOCHS):
        random.shuffle(rows)
        for i in range(0, len(rows), BS):
            opt.zero_grad()
            for j in range(i, min(i + BS, len(rows)), MB):  # micro-batches: the 152k-word output layer is large
                b = rows[j:j + MB]; L = max(len(x) for x, _ in b)
                ids = torch.tensor([[tok.pad_token_id] * (L - len(x)) + x for x, _ in b]).to(dev)
                lab = torch.tensor([[-100] * (L - len(y)) + y for _, y in b]).to(dev)
                att = (torch.arange(L)[None, :] >= torch.tensor([L - len(x) for x, _ in b])[:, None]).long().to(dev)
                with torch.autocast(dev, dtype=torch.float16, enabled=dev == "cuda"):
                    loss = model(input_ids=ids, attention_mask=att, labels=lab).loss
                (loss * len(b) / len(rows[i:i + BS])).backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); sch.step()
            if (i // BS) % 100 == 0: print(kind, ep, i // BS, f"loss {loss.item():.4f}", f"{time.time() - t0:.0f}s")

    model = model.merge_and_unload(); model.eval()
    for split in ["dev", "test_synth", "test_human"]:
        if not SPLITS[split]: continue
        preds = []
        for i in range(0, len(SPLITS[split]), 32):
            b = SPLITS[split][i:i + 32]
            enc = tok([prompt(r) for r in b], return_tensors="pt", padding=True).to(dev)
            with torch.no_grad():
                g = model.generate(**enc, max_new_tokens=40, do_sample=False, pad_token_id=tok.pad_token_id)
            for r, seq in zip(b, g[:, enc["input_ids"].shape[1]:]):
                preds.append({"id": r["id"], **parse(tok.decode(seq, skip_special_tokens=True), r, kind)})
        with open(f"{OUT}/routeB3_qwen06_{kind}.{split}.jsonl", "w") as f:
            for p in preds: f.write(json.dumps(p, ensure_ascii=False) + "\n")
        if split == "test_human": continue
        s = score({r["id"]: r for r in SPLITS[split]}, {p["id"]: p for p in preds})
        metrics[f"{kind}/{split}"] = s
        print(f"routeB {kind} {split}: full {s['all']['full']:.1f} ambig {s['ambiguous']['full']:.1f} "
              f"past {s['past']['full']:.1f} type {s['all']['type']:.1f}")

    if os.environ.get("SMOKE"):  # GGUF conversion runs on Kaggle only
        del model; continue
    hf = f"/tmp/qwen06_{kind}"
    model.save_pretrained(hf, safe_serialization=True); tok.save_pretrained(hf)
    subprocess.run(f"cp -r {hf} {OUT}/qwen06_{kind}_v3_merged", shell=True)
    del model; torch.cuda.empty_cache()
    if not os.path.exists("/tmp/llama.cpp"):
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/ggml-org/llama.cpp", "/tmp/llama.cpp"], check=True)
    env = {**os.environ, "PYTHONPATH": "/tmp/llama.cpp/gguf-py"}
    for q in ("f16", "q8_0"):
        subprocess.run([sys.executable, "/tmp/llama.cpp/convert_hf_to_gguf.py", hf, "--outtype", q,
                        "--outfile", f"{OUT}/qwen06_{kind}_v3.{q}.gguf"], check=False, env=env)
json.dump(metrics, open(f"{OUT}/routeB3_metrics.json", "w"), indent=1)
print("done")
