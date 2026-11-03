"""Run the rules-only baseline. Usage: python run_rules.py ../data/test_synth.jsonl ../results/rules.test_synth.jsonl"""
import json, sys, time
from datetime import datetime
sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/src")
from rules import predict

src, dst = sys.argv[1], sys.argv[2]
with open(dst, "w") as f:
    for r in map(json.loads, open(src)):
        t0 = time.perf_counter()
        p = predict(r["text"], datetime.fromisoformat(r["anchor"]))
        ms = (time.perf_counter() - t0) * 1000
        f.write(json.dumps({"id": r["id"], "type": p["type"], "date": p["date"], "time": p["time"], "ms": ms}) + "\n")
