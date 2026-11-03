"""Real-world tense test: PHINC tweets with kal/parso whose human English translation says yesterday/tomorrow.
Compares route A's learned tense head with the rule heuristic. Usage: python tense_real.py data/mined/phinc.jsonl"""
import json, os, sys
import numpy as np, onnxruntime as ort
from transformers import AutoTokenizer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, f"{ROOT}/src")
from rules import direction

rows = [r for r in map(json.loads, open(sys.argv[1])) if r.get("silver_direction") in ("past", "future")]
gold = [r["silver_direction"] for r in rows]
print(f"n={len(rows)} (past {gold.count('past')}, future {gold.count('future')}); always-future baseline "
      f"{100 * gold.count('future') / len(gold):.1f}%")
pred = [direction(r["text"]) for r in rows]
print(f"  rules tense        {100 * np.mean([p == g for p, g in zip(pred, gold)]):5.1f}%")
out = {"rules": pred}
for m in ("muril", "xlmr", "mdistil"):
    d = f"{ROOT}/results/kaggle_a/routeA_{m}_onnx"
    meta = json.load(open(f"{d}/meta.json")); tok = AutoTokenizer.from_pretrained(d)
    sess = ort.InferenceSession(f"{d}/model.onnx", providers=["CPUExecutionProvider"])
    pred = []
    for r in rows:
        enc = tok(r["text"], truncation=True, max_length=meta["maxlen"], return_tensors="np")
        _, _, di = sess.run(None, {"input_ids": enc["input_ids"].astype("int64"), "attention_mask": enc["attention_mask"].astype("int64")})
        pred.append(meta["dirs"][int(di[0].argmax())])
    out[m] = pred
    acc = np.mean([p == g for p, g in zip(pred, gold)])
    pa = np.mean([p == g for p, g in zip(pred, gold) if g == "past"]); fa = np.mean([p == g for p, g in zip(pred, gold) if g == "future"])
    print(f"  {m:8} learned   {100 * acc:5.1f}%   (past recall {100 * pa:.0f}%, future recall {100 * fa:.0f}%)")
json.dump({"gold": gold, "texts": [r["text"] for r in rows], **out}, open(f"{ROOT}/results/tense_real_phinc.json", "w"), ensure_ascii=False)
