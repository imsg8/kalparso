"""CPU latency on the test desktop (i7-9700, no GPU). One entry at a time, end to end (tokenize -> model -> spans ->
ground), as the Planner would call it. Reports cold start, then median/p95 over warm calls.
Usage:
  python latency.py onnx  MODEL_DIR  data.jsonl  out.jsonl [threads] [model.int8.onnx|model.onnx]
  python latency.py ollama MODEL_NAME data.jsonl out.jsonl [abs|ir]
  python latency.py rules  -          data.jsonl out.jsonl"""
import json, os, statistics, sys, time, urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src")); sys.path.insert(0, HERE)
from ground import ground, ground_entry

mode, model, src, dst = sys.argv[1:5]
rows = [json.loads(l) for l in open(src)]
lat, preds = [], []


def onnx_runner(d, threads, fname):
    import numpy as np, onnxruntime as ort
    from transformers import AutoTokenizer
    t0 = time.perf_counter()
    meta = json.load(open(f"{d}/meta.json"))
    tok = AutoTokenizer.from_pretrained(d)
    so = ort.SessionOptions(); so.intra_op_num_threads = threads; so.inter_op_num_threads = 1
    sess = ort.InferenceSession(f"{d}/{fname}", so, providers=["CPUExecutionProvider"])
    labels, types, dirs = meta["labels"], meta["types"], meta["dirs"]

    def run(r):
        enc = tok(r["text"], return_offsets_mapping=True, truncation=True, max_length=meta["maxlen"], return_tensors="np")
        tg, ty, di = sess.run(None, {"input_ids": enc["input_ids"].astype("int64"),
                                     "attention_mask": enc["attention_mask"].astype("int64")})
        spans, cur = [], None
        for (s, e), t in zip(enc["offset_mapping"][0].tolist(), tg[0].argmax(-1).tolist()):
            if s == e: continue
            lab = labels[t]
            if lab == "O": cur = None; continue
            p, l = lab.split("-")
            if p == "B" or cur is None or cur[0] != l or s > cur[2] + 1: cur = [l, s, e]; spans.append(cur)
            else: cur[2] = e
            spans = spans
        spans = [(l, r["text"][s:e]) for l, s, e in spans]
        typ, dirn = types[int(ty[0].argmax())], dirs[int(di[0].argmax())]
        d_, t_ = ground_entry(spans, dirn, datetime.fromisoformat(r["anchor"]), typ, r["text"])
        return {"type": typ, "date": d_, "time": t_, "direction": dirn, "spans": spans}
    return run, time.perf_counter() - t0


def ollama_runner(name, kind):
    sys.path.insert(0, os.path.join(HERE, "..", "kaggle"))
    TYPES = ["reminder", "note", "goal"]

    def run(r):
        p = f"Now: {r['anchor'].replace('T', ' ')} {r['weekday'][:3]}\nEntry: {r['text']}\nOut:"
        body = {"model": name, "prompt": p, "raw": True, "stream": False, "keep_alive": "15m",
                "options": {"temperature": 0, "num_predict": 40, "num_ctx": 512, "stop": ["\n"]}}
        req = urllib.request.Request("http://localhost:11434/api/generate", json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
        out = json.load(urllib.request.urlopen(req, timeout=300))["response"]
        return parse(out, r, kind)

    def parse(out, r, kind):
        parts = out.strip().split(" ", 2)
        typ = {"R": "reminder", "N": "note", "G": "goal"}.get(parts[0] if parts else "", "note")
        if kind == "abs":
            return {"type": typ, "date": parts[1] if len(parts) > 1 and parts[1] != "-" else None,
                    "time": parts[2].split()[0] if len(parts) > 2 and parts[2] != "-" else None}
        dirn = "past" if len(parts) > 1 and parts[1] == "P" else "future"
        spans = [tuple(reversed([x.strip() for x in c.rsplit("=", 1)])) for c in (parts[2].split(" ; ") if len(parts) > 2 and parts[2] != "-" else []) if "=" in c]
        d_, t_ = ground_entry(spans, dirn, datetime.fromisoformat(r["anchor"]), typ, r["text"])
        return {"type": typ, "date": d_, "time": t_}
    t0 = time.perf_counter(); run(rows[0]); return run, time.perf_counter() - t0


if mode == "onnx":
    run, setup = onnx_runner(model, int(sys.argv[5]) if len(sys.argv) > 5 else 4,
                             sys.argv[6] if len(sys.argv) > 6 else "model.int8.onnx")
elif mode == "ollama":
    run, setup = ollama_runner(model, sys.argv[5] if len(sys.argv) > 5 else "abs")
else:
    from rules import predict
    t0 = time.perf_counter(); predict("kal 5 baje", datetime.now())
    run, setup = (lambda r: {k: v for k, v in predict(r["text"], datetime.fromisoformat(r["anchor"])).items()
                             if k in ("type", "date", "time")}), time.perf_counter() - t0

t0 = time.perf_counter(); first = run(rows[0]); cold = (time.perf_counter() - t0 + setup) * 1000
with open(dst, "w") as f:
    for r in rows:
        t0 = time.perf_counter(); p = run(r); ms = (time.perf_counter() - t0) * 1000
        lat.append(ms); f.write(json.dumps({"id": r["id"], **p, "ms": ms}, ensure_ascii=False) + "\n")
lat.sort()
print(json.dumps({"mode": mode, "model": model, "n": len(lat), "cold_ms": round(cold, 1),
                  "median_ms": round(statistics.median(lat), 2), "p95_ms": round(lat[int(0.95 * (len(lat) - 1))], 2),
                  "mean_ms": round(statistics.mean(lat), 2)}))
