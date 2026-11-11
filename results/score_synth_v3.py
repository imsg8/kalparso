import glob, sys, statistics, re
from datetime import datetime
sys.path.insert(0, "src")
from evaluate import load, score
from ground import ground_entry
gold = load("data/v3/test_synth.jsonl")
T = [g for g in gold.values() if g["date"]]
def dt(p, rows): return 100*sum((p.get(r["id"],{}).get("date"),p.get(r["id"],{}).get("time"))==(r["date"],r["time"]) for r in rows)/len(rows)
def dt_all(p): return 100*sum((p.get(k,{}).get("date"),p.get(k,{}).get("time"))==(g["date"],g["time"]) for k,g in gold.items())/len(gold)
for m in ("muril","xlmr","mdistil"):
    res = {"full":[], "dt_all":[], "dt_timed":[], "type":[], "past":[], "re_dt_all":[], "re_full":[]}
    for f in sorted(glob.glob(f"results/kaggle_train_v3/A2_{m}_v3_phinc_s*.test_synth.jsonl")):
        p = load(f); s = score(gold, p)
        res["full"].append(s["all"]["full"]); res["type"].append(s["all"]["type"]); res["past"].append(s["past"]["full"])
        res["dt_all"].append(dt_all(p)); res["dt_timed"].append(dt(p, T))
        rp = {}
        for k, v in p.items():
            g = gold[k]; d, t = ground_entry([tuple(x) for x in v["spans"]], v.get("direction") or "future", datetime.fromisoformat(g["anchor"]), v.get("type"), g["text"])
            rp[k] = {**v, "date": d, "time": t}
        res["re_dt_all"].append(dt_all(rp)); res["re_full"].append(score(gold, rp)["all"]["full"])
    f = lambda xs: f"{statistics.mean(xs):.1f}±{statistics.stdev(xs):.1f}"
    print(m, len(res["full"]), "seeds |", " ".join(f"{k} {f(v)}" for k, v in res.items()))
# rules on v3 synth for reference
