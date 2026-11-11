"""Collect every system's predictions on the held-out human test split, score them, and write
results/REPORT.md and results/report.json. Missing runs are skipped.
Usage: python results/report.py"""
import glob, json, os, statistics, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from eval_human import load, score, mcnemar, subsets, dt_ok

GOLD = load(f"{ROOT}/data/human/human_test.jsonl")
DEV = load(f"{ROOT}/data/human/human_dev.jsonl")
R = f"{ROOT}/results"
# total params (B), active params (B), family
LLM = {"qwen3.5_0.8b": (0.8, 0.8), "qwen3.5_4b": (4.0, 4.0), "qwen3_8b": (8.2, 8.2), "llama3.1_8b": (8.0, 8.0),
       "gemma3_12b": (12.2, 12.2), "gemma4_26b": (25.8, 3.8), "qwen3_30b-a3b": (30.5, 3.3), "gemma3_27b": (27.4, 27.4),
       "qwen3_32b": (32.8, 32.8), "gpt-oss_20b": (20.9, 3.6)}
ENC = {"muril": 0.237, "xlmr": 0.278, "mdistil": 0.135}


def sub(pred, ids):
    return {k: v for k, v in pred.items() if k in ids}


def regrounded(path):
    """LLM span-mode rows carry their spans: re-ground with the current grounder so every system shares it."""
    from datetime import datetime
    from ground import ground_entry
    out = {}
    for k, p in load(path).items():
        if k not in GOLD or "spans" not in p: out[k] = p; continue
        g = GOLD[k]
        d, t = ground_entry([tuple(s) for s in p["spans"]], p.get("direction") or "future",
                            datetime.fromisoformat(g["anchor"]), p.get("type"), g["text"])
        out[k] = {**p, "date": d, "time": t}
    return out


systems = {}  # name -> list of pred dicts (one per seed, seed 13 first)
seed13_first = lambda paths: sorted(paths, key=lambda p: ("_s13." not in p, p))
meta = {}
add = lambda name, preds, **m: (systems.setdefault(name, []).append(preds), meta.setdefault(name, m))

for f, name in [("rules", "Rules v1 (spec conventions)"), ("rules_v2", "Rules v2"), ("dateparser", "dateparser"),
                ("duckling_en_US", "Duckling (en_US)"), ("duckling_hi_IN", "Duckling (hi_IN)")]:
    if os.path.exists(f"{R}/human/{f}.jsonl"): add(name, load(f"{R}/human/{f}.jsonl"), kind="rule", params=0)
for m in ENC:
    for suf, label in [("_fp32", "v1 data, v1 grounder"), ("_fp32_g2", "v1 data, v2 grounder")]:
        p = f"{R}/human/A_{m}{suf}.jsonl"
        if os.path.exists(p): add(f"{m} ({label})", load(p), kind="ours_v1", params=ENC[m])
    for p in seed13_first(glob.glob(f"{R}/kaggle_train_v3/A2_{m}_v3_phinc_s*.test_human.jsonl")):
        add(f"KalParso-{m}", load(p), kind="ours", params=ENC[m])
        rd = {k: {**v, **v["rulesdir"]} for k, v in load(p).items() if "rulesdir" in v}
        add(f"KalParso-{m} (rule tense)", rd, kind="ours_ablate", params=ENC[m])
    for tag, label in (("v2", "v2 data"), ("v3", "v3 data, no PHINC")):
        for p in sorted(glob.glob(f"{R}/v2/A2_{m}_{tag}_s*.test_human.jsonl")) + sorted(glob.glob(f"{R}/kaggle_ablate/A2_{m}_{tag}_s*.test_human.jsonl")):
            add(f"{m} ({label})", load(p), kind="ours_ablate", params=ENC[m])
if os.path.exists(f"{R}/kaggle_routeb_v3/routeB3_qwen06_ir.test_human.jsonl"):
    add("Qwen3-0.6B + LoRA, writes spans (v3)", load(f"{R}/kaggle_routeb_v3/routeB3_qwen06_ir.test_human.jsonl"), kind="routeB", params=0.6)
for p in seed13_first(glob.glob(f"{R}/v2/cascade_muril_gemma4_s*.test_human.jsonl")):
    add("Cascade: KalParso-muril, gemma4:26b on rules disagreement", load(p), kind="cascade", params=0.237)
for p in seed13_first(glob.glob(f"{R}/v2/cascade_muril_gemma4few2_s*.test_human.jsonl")):
    add("Cascade: KalParso-muril, gemma4:26b (few2) on rules disagreement", load(p), kind="cascade", params=0.237)
for p in sorted(glob.glob(f"{R}/llm/*.test_human.jsonl")):
    base = os.path.basename(p)[:-len(".test_human.jsonl")]
    tag, mode = base.rsplit(".", 1)
    if tag not in LLM: continue
    preds = regrounded(p) if mode == "spans" else load(p)
    add(f"{tag} [{mode}]", preds, kind="llm", mode=mode, params=LLM[tag][0], active=LLM[tag][1], tag=tag)

ids = set(GOLD)
rows = []
for name, runs in systems.items():
    g_eff = GOLD
    if meta[name]["kind"] == "llm" and len(set(runs[0]) & ids) < 0.9 * len(ids):  # sampled run: score its own rows
        g_eff = {k: v for k, v in GOLD.items() if k in runs[0]}
        meta[name]["sample"] = len(g_eff)
    sc = [score(g_eff, sub(p, ids), ci=True) for p in runs]
    if sc[0]["coverage"] < 50 and meta[name]["kind"] != "llm": continue
    agg = lambda f: [f(s) for s in sc]
    mean = lambda xs: statistics.mean(xs); sd = lambda xs: statistics.stdev(xs) if len(xs) > 1 else 0.0
    if meta[name].get("sample"): name_shown = f"{name} (sample n={meta[name]['sample']})"
    row = {"name": name, **meta[name], "seeds": len(sc),
           "dt": mean(agg(lambda s: s["all"]["datetime"])), "dt_sd": sd(agg(lambda s: s["all"]["datetime"])),
           "dt_ci": sc[0]["all"]["datetime_ci"], "full": mean(agg(lambda s: s["all"]["full"])),
           "type": mean(agg(lambda s: s["type_acc"])), "coverage": sc[0]["coverage"]}
    for k in ("kal_tomorrow", "kal_yesterday", "parso_narso", "past", "noisy", "english", "devanagari", "late_night",
              "self_correction", "deadline", "undated"):
        row[k] = mean(agg(lambda s: s[k]["datetime"]))
    lat = [s["latency_ms"]["median"] for s in sc if "latency_ms" in s]
    row["ms_median"] = mean(lat) if lat else None
    rows.append(row)
rows.sort(key=lambda r: -r["dt"])

# McNemar: best KalParso seed-13 run vs every other system (first run of each)
best = next((r for r in rows if r["name"] == "KalParso-muril"), None) or next((r for r in rows if r["kind"] == "ours"), None)
if best:
    A = systems[best["name"]][0]
    for r in rows:
        if r is best: continue
        if r.get("sample"): continue
        b, c, p = mcnemar(GOLD, sub(A, ids), sub(systems[r["name"]][0], ids))
        r["mcnemar"] = {"ours_only": b, "them_only": c, "p": p}

# stress / efficiency
stress = {}
for p in glob.glob(f"{R}/stress/*.json"):
    try: stress[os.path.basename(p)[:-5]] = json.load(open(p))
    except Exception: pass

json.dump({"rows": rows, "stress": stress, "n_test": len(GOLD), "n_scored": len(subsets(GOLD)["all"])},
          open(f"{R}/report.json", "w"), indent=1, default=str)


def fmt(x, d=1):
    return "-" if x is None else f"{x:.{d}f}"


L = ["# KalParso results on the held-out human test split", "",
     f"Gold: {len(GOLD)} entries, {len(subsets(GOLD)['all'])} scored for date+time (out-of-scope rows excluded). "
     "Date+time = the date and the clock time both right (deadlines on the date). Mean over seeds where several exist; "
     "95% bootstrap CI from the first run.", "",
     "| System | Params | Date+time % (95% CI) | Full % | Type % | kal=tomorrow | kal=yesterday | parso/narso | Past | Noisy | English | McNemar p vs ours |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    pr = f"{r['params']:.3g}B" + (f" ({r['active']:.1f}B act.)" if r.get("active") and r["active"] < r["params"] else "") \
        if r.get("params") else "-"
    sd = f" ± {r['dt_sd']:.1f}" if r["seeds"] > 1 else ""
    mc = r.get("mcnemar"); mcs = "-" if not mc else (f"{mc['p']:.1e}" if mc["p"] < 0.001 else f"{mc['p']:.3f}")
    L.append(f"| {r['name']}{' (sample n=' + str(r['sample']) + ')' if r.get('sample') else ''} | {pr} | {r['dt']:.1f}{sd} ({r['dt_ci'][0]:.1f}-{r['dt_ci'][1]:.1f}) | {r['full']:.1f} | "
             f"{r['type']:.1f} | {r['kal_tomorrow']:.1f} | {r['kal_yesterday']:.1f} | {r['parso_narso']:.1f} | "
             f"{r['past']:.1f} | {r['noisy']:.1f} | {r['english']:.1f} | {mcs} |")
S = subsets(GOLD)
L += ["", "Subset sizes: " + ", ".join(f"{k} {len(v)}" for k, v in S.items()), ""]
if stress:
    L += ["## CPU efficiency (homelab i7-9700, 35 W cap, no GPU)", "",
          "| System | Load s | File MB | Median ms | p95 | p99 | CPU-s/entry | J/entry above idle | Peak cores | Spike >1 core ms | Thru @1 | @4 | @8 | Sustained drift (last/first 30 s) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, s in sorted(stress.items()):
        si, sp, c = s.get("single", {}), s.get("spike", {}), s.get("conc", {})
        thr = lambda n: fmt(c.get(str(n), c.get(n, {})).get("throughput_per_s"), 2) if c else "-"
        L.append(f"| {k} | {fmt(s.get('load_s'))} | {fmt(s.get('model_file_mb'), 0)} | {fmt(si.get('median_ms'))} | "
                 f"{fmt(si.get('p95_ms'))} | {fmt(si.get('p99_ms'))} | {fmt(si.get('cpu_s_per_entry'), 3)} | "
                 f"{fmt(si.get('joules_above_idle_per_entry'), 2)} | {fmt(sp.get('peak_cores'), 2)} | {fmt(sp.get('above_1core_ms'), 0)} | "
                 f"{thr(1)} | {thr(4)} | {thr(8)} | {fmt((s.get('sustain') or {}).get('first_vs_last_window'), 3)} |")
open(f"{R}/REPORT.md", "w").write("\n".join(L) + "\n")
print("\n".join(L))
