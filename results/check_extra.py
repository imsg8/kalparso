"""Numbers in the paper that results/report.py does not print: the v1 tense figure, the int8 accuracy of the
seed-13 models, and how far the LLM answers timed on the CPU agree with the GPU runs. Usage: python results/check_extra.py"""
import glob, json, os, statistics, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R = f"{ROOT}/results"
sys.path.insert(0, f"{ROOT}/src")
from eval_human import load, dt_ok, subsets

# Tense figure (a): v1 encoders on the 484 ambiguous entries of the v1 Synth-Test, learned head against rule tense, 3 seeds
gold = load(f"{ROOT}/data/v1/test_synth.jsonl"); amb = [g for g in gold.values() if g["flags"]["ambiguous"]]
hit = lambda p, rows: 100 * sum((p.get(g["id"], {}).get("date"), p.get(g["id"], {}).get("time")) == (g["date"], g["time"]) for g in rows) / len(rows)
print(f"Tense figure (a), date+time on {len(amb)} ambiguous v1 Synth-Test entries, mean of 3 seeds")
for m in ("muril", "xlmr", "mdistil"):
    f = lambda tag: statistics.mean(hit(load(p), amb) for p in glob.glob(f"{R}/kaggle_a/routeA_{m}{tag}_s*.test_synth.jsonl"))
    print(f"  {m:8} learned tense {f(''):.1f}   rule tense {f('-rulesdir'):.1f}")

# Tense figure (b): 120 PHINC tweets (texts not redistributed)
t = json.load(open(f"{R}/tense_real_phinc.json")); g = t["gold"]; npast = g.count("past")
print(f"Tense figure (b), {len(g)} PHINC tweets ({npast} past): always future {100 * (len(g) - npast) / len(g):.1f}% accuracy")
for k in ("rules", "muril", "xlmr", "mdistil"):
    acc = 100 * sum(a == b for a, b in zip(g, t[k])) / len(g); rec = 100 * sum(a == b == "past" for a, b in zip(g, t[k])) / npast
    print(f"  {k:8} accuracy {acc:.1f}   past recall {rec:.1f}")

# int8 against fp32, seed 13, on Human-Test
H = load(f"{ROOT}/data/human/human_test.jsonl"); S = subsets(H)["all"]
acc = lambda p: 100 * sum(dt_ok(x, p.get(x["id"], {})) for x in S) / len(S)
print(f"Seed 13 on the {len(S)} scored Human-Test entries, fp32 and dynamic int8")
for m in ("xlmr", "mdistil", "muril"):
    print(f"  {m:8} fp32 {acc(load(f'{R}/kaggle_train_v3/A2_{m}_v3_phinc_s13.test_human.jsonl')):.1f}   "
          f"int8 {acc(load(f'{R}/int8/A2_{m}_v3_phinc_s13.int8.test_human.jsonl')):.1f}")

# LLM answers timed on the CPU against the GPU accuracy runs (v2 prompt), and Ollama's token counts
key = lambda r: (r.get("type"), r.get("date"), r.get("time")); n = same = 0; prompt = []
print("LLM requests timed on the CPU against the GPU run")
for p in sorted(glob.glob(f"{R}/stress/llmcpu_*.preds.jsonl")):
    tag = os.path.basename(p)[len("llmcpu_"):-len(".preds.jsonl")]
    cpu = [json.loads(l) for l in open(p)]; gpu = load(f"{R}/llm/{tag}.few2.test_human.jsonl")
    s = sum(key(r) == key(gpu[r["id"]]) for r in cpu); n += len(cpu); same += s; prompt += [r["prompt_eval_count"] for r in cpu]
    out = [r["eval_count"] for r in cpu]
    print(f"  {tag:14} {s:2d} of {len(cpu):2d} identical   output tokens {min(out)} to {max(out)}")
print(f"  all models: {same} of {n} identical, prompt {min(prompt)} to {max(prompt)} tokens")
