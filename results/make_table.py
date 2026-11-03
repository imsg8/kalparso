"""Main results table (markdown) for a split. Seeds are averaged (mean ± sd).
Usage: python make_table.py test_synth [gold_split, e.g. test_synth_300 to score on the LLM sample]"""
import glob, json, os, re, statistics, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, f"{ROOT}/src")
from evaluate import score, load

split = sys.argv[1]
gold = load(f"{ROOT}/data/{sys.argv[2] if len(sys.argv) > 2 else split}.jsonl")
R = f"{ROOT}/results"
systems = {"dateparser": [f"{R}/dateparser.{split}.jsonl"], "Rules (shares generator lexicon)": [f"{R}/rules.{split}.jsonl"]}
for f in sorted(glob.glob(f"{R}/llm/llm_*.jsonl")):
    systems[f"Few-shot {os.path.basename(f)[4:-6]}"] = [f]
for f in sorted(glob.glob(f"{R}/kaggle_a/routeA_*_s*.{split}.jsonl")):
    k = re.search(r"routeA_(.+)_s\d+", f).group(1)
    name = f"A: {k.replace('-rulesdir', '')} + grounder" + (" (rule tense)" if "rulesdir" in k else "")
    systems.setdefault(name, []).append(f)
for f in sorted(glob.glob(f"{R}/kaggle_b/routeB_*.{split}.jsonl")):
    k = "writes spans, grounder dates" if "_ir." in f else "writes the date itself"
    systems[f"B: Qwen3-0.6B LoRA, {k}"] = [f]


def timed(p, rows):
    return 100 * sum((p.get(r["id"], {}).get("date"), p.get(r["id"], {}).get("time")) == (r["date"], r["time"]) for r in rows) / len(rows)


T = [r for r in gold.values() if r["date"]]
TA = [r for r in T if r["flags"]["ambiguous"]]
fmt = lambda xs: f"{statistics.mean(xs):.1f}" + (f" ± {statistics.stdev(xs):.1f}" if len(xs) > 1 else "")
print(f"| System | n | Full match | Type | Date+time (timed, n={len(T)}) | Date+time, kal/parso/weekday (n={len(TA)}) | Past | Median ms (CPU) |")
print("|---|---|---|---|---|---|---|---|")
for name, files in systems.items():
    ss, tt, ta, ms = [], [], [], []
    for f in files:
        p = {k: v for k, v in load(f).items() if k in gold}
        g = {k: v for k, v in gold.items() if k in p}
        s = score(g, p); ss.append(s)
        tt.append(timed(p, [r for r in T if r["id"] in p])); ta.append(timed(p, [r for r in TA if r["id"] in p]))
        if "latency_ms" in s: ms.append(s["latency_ms"]["median"])
    n = len(ss[0]) and len([1 for _ in g])
    lat = f"{statistics.mean(ms):,.0f}" if ms and statistics.mean(ms) > 50 else "see sweep"
    print(f"| {name} | {n} | {fmt([s['all']['full'] for s in ss])} | {fmt([s['all']['type'] for s in ss])} | {fmt(tt)} | {fmt(ta)} "
          f"| {fmt([s['past']['full'] for s in ss])} | {lat} |")
