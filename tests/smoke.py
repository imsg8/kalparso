"""Smoke test: the rules engine and the scorer reproduce the reported Rules v2 number (85.7% on 706 held-out entries),
the shipped predictions score as reported, and a few hand-checked entries ground correctly. Usage: python tests/smoke.py"""
import os, sys
from datetime import datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from eval_human import load, score
from rules import predict

gold = load(f"{ROOT}/data/human/human_test.jsonl")
rules = {g["id"]: predict(g["text"], datetime.fromisoformat(g["anchor"])) for g in gold.values()}
s = score(gold, rules, ci=False)["all"]
assert s["n"] == 706, s["n"]
assert abs(s["datetime"] - 85.694) < 0.01, s["datetime"]

muril = load(f"{ROOT}/results/kaggle_train_v3/A2_muril_v3_phinc_s13.test_human.jsonl")
m = score(gold, muril, ci=False)["all"]["datetime"]
assert 85 < m < 87.5, m

A = datetime(2026, 10, 31, 14, 0)  # Saturday
for text, date, time in [("parso shaam saade 5 baje dentist", "2026-11-02", "17:30"),
                         ("kal subah paune 9 baje meeting", "2026-11-01", "08:45"),
                         ("2 ghante baad Rahul ko call karna", "2026-10-31", "16:00")]:
    p = predict(text, A)
    assert (p["date"], p["time"]) == (date, time), (text, p)
print(f"ok: rules {s['datetime']:.1f}% on {s['n']} entries, MuRIL seed 13 {m:.1f}%, hand checks pass")
