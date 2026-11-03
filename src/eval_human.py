"""Score predictions on the human test set (data/human/test_human.jsonl), with bootstrap CIs and McNemar tests.
- Out-of-scope rows (ranges, months, festivals) are left out of date/time scores; type is scored on all rows.
- "by D" deadlines are scored on the date only.
- Late-night rows accept the speaker-day answer or the strict calendar answer ("either", the headline);
  "speaker" and "strict" report each convention alone.
Usage: python eval_human.py gold.jsonl pred.jsonl [pred2.jsonl ...]   (prints a table)
       python eval_human.py --json gold.jsonl pred.jsonl ...          (prints JSON)"""
import json, random, re, statistics, sys
from datetime import date as Date
from math import comb

KAL = re.compile(r"\b(kal|call|cal)\b|कल", re.I)
PARSO = re.compile(r"\b(parso|parson|parsoun|parsun|narso|narson)\b|परसों|नरसों", re.I)


def load(p):
    return {r["id"]: r for r in map(json.loads, open(p))}


def offset(g):
    return (Date.fromisoformat(g["date"]) - Date.fromisoformat(g["anchor"][:10])).days if g["date"] else None


def dt_ok(g, p, conv="either"):
    """Date (and time, unless a deadline) correct under a late-night convention."""
    def match(d, t):
        return p.get("date") == d and (g["kind"] == "by" or p.get("time") == t)
    if not g["late_night"] or conv == "speaker": return match(g["date"], g["time"])
    if conv == "strict": return match(g["date_strict"], g["time_strict"])
    return match(g["date"], g["time"]) or match(g["date_strict"], g["time_strict"])


def subsets(gold):
    rows = list(gold.values())
    ins = [g for g in rows if g["kind"] != "out_of_scope"]
    dated = [g for g in ins if g["date"]]
    return {
        "all": ins, "dated": dated, "undated": [g for g in ins if not g["date"]],
        "kal_tomorrow": [g for g in dated if KAL.search(g["text"]) and g["direction"] == "future" and offset(g) in (0, 1)],
        "kal_yesterday": [g for g in dated if KAL.search(g["text"]) and g["direction"] == "past" and offset(g) in (-1, 0)],
        "parso_narso": [g for g in dated if PARSO.search(g["text"])],
        "past": [g for g in dated if g["direction"] == "past"],
        "ambiguous": [g for g in ins if g["flags"]["ambiguous"]],
        "noisy": [g for g in ins if g["flags"]["noisy"]],
        "english": [g for g in ins if g["flags"]["english"]],
        "devanagari": [g for g in ins if g["flags"]["devanagari"]],
        "self_correction": [g for g in ins if g["flags"]["self_correction"]],
        "late_night": [g for g in ins if g["late_night"]],
        "part_only": [g for g in ins if g["part_only"]],
        "deadline": [g for g in ins if g["kind"] == "by"],
    }


def correct(g, p, conv="either"):
    return p.get("type") == g["type"] and dt_ok(g, p, conv)


def boot(xs, n=2000, seed=0):
    if not xs: return (0.0, 0.0)
    rnd = random.Random(seed); k = len(xs)
    ms = sorted(sum(xs[rnd.randrange(k)] for _ in range(k)) / k for _ in range(n))
    return 100 * ms[int(0.025 * n)], 100 * ms[int(0.975 * n)]


def score(gold, pred, ci=True):
    S = subsets(gold); out = {}
    for name, rows in S.items():
        dt = [dt_ok(g, pred.get(g["id"], {})) for g in rows]
        full = [correct(g, pred.get(g["id"], {})) for g in rows]
        out[name] = {"n": len(rows), "datetime": 100 * sum(dt) / max(len(rows), 1),
                     "full": 100 * sum(full) / max(len(rows), 1)}
        if ci and name in ("all", "dated", "kal_yesterday", "kal_tomorrow", "past"):
            out[name]["datetime_ci"] = boot(dt); out[name]["full_ci"] = boot(full)
    a = S["all"]
    out["all"]["date_only"] = 100 * sum(pred.get(g["id"], {}).get("date") == (g["date"]) or
                                        (g["late_night"] and pred.get(g["id"], {}).get("date") == g["date_strict"])
                                        for g in a) / len(a)
    for conv in ("speaker", "strict"):
        out["all"][f"datetime_{conv}"] = 100 * sum(dt_ok(g, pred.get(g["id"], {}), conv) for g in a) / len(a)
    every = list(gold.values())
    out["type_acc"] = 100 * sum(pred.get(g["id"], {}).get("type") == g["type"] for g in every) / len(every)
    f1s = []
    for c in ("reminder", "note", "goal"):
        tp = sum(1 for g in every if g["type"] == c and pred.get(g["id"], {}).get("type") == c)
        fp = sum(1 for g in every if g["type"] != c and pred.get(g["id"], {}).get("type") == c)
        fn = sum(1 for g in every if g["type"] == c and pred.get(g["id"], {}).get("type") != c)
        f1s.append(2 * tp / max(2 * tp + fp + fn, 1))
    out["type_macroF1"] = 100 * sum(f1s) / 3
    ms = sorted(p["ms"] for p in pred.values() if "ms" in p)
    if ms:
        q = lambda f: ms[min(int(f * len(ms)), len(ms) - 1)]
        out["latency_ms"] = {"median": statistics.median(ms), "p95": q(0.95), "p99": q(0.99), "mean": statistics.mean(ms)}
    out["coverage"] = 100 * sum(1 for g in every if g["id"] in pred) / len(every)
    return out


def mcnemar(gold, pa, pb, subset="all"):
    """Exact two-sided McNemar on per-row datetime correctness. Returns (b, c, p): b = A right & B wrong."""
    rows = subsets(gold)[subset]
    b = sum(dt_ok(g, pa.get(g["id"], {})) and not dt_ok(g, pb.get(g["id"], {})) for g in rows)
    c = sum(dt_ok(g, pb.get(g["id"], {})) and not dt_ok(g, pa.get(g["id"], {})) for g in rows)
    n = b + c
    if n == 0: return b, c, 1.0
    p = sum(comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n * 2
    return b, c, min(p, 1.0)


COLS = ("all", "dated", "kal_tomorrow", "kal_yesterday", "parso_narso", "past", "noisy", "english", "late_night")


def table(name, s):
    line = f"{name:34} " + " ".join(f"{s[k]['datetime']:6.1f}" for k in COLS)
    line += f" | full {s['all']['full']:5.1f} type {s['type_acc']:5.1f}"
    lat = s.get("latency_ms")
    if lat: line += f" | {lat['median']:9.1f} ms med {lat['p95']:9.1f} p95"
    if s["coverage"] < 100: line += f" | cov {s['coverage']:.0f}%"
    return line


if __name__ == "__main__":
    args = sys.argv[1:]; as_json = args[0] == "--json"
    if as_json: args = args[1:]
    gold = load(args[0])
    res = {p.split("/")[-1].replace(".jsonl", ""): score(gold, load(p)) for p in args[1:]}
    if as_json: print(json.dumps(res, indent=1)); sys.exit()
    S = subsets(gold)
    print(f"{'system (date+time %)':34} " + " ".join(f"{k[:6]:>6}" for k in COLS))
    print(f"{'n':34} " + " ".join(f"{len(S[k]):6d}" for k in COLS))
    for k, s in res.items(): print(table(k, s))
