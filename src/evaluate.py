"""Score a predictions file against gold. Usage: python evaluate.py gold.jsonl pred.jsonl [pred2.jsonl ...]
Prediction rows: {"id", "type", "date", "time", "ms"(optional)}."""
import json, sys, statistics


def load(p):
    return {r["id"]: r for r in map(json.loads, open(p))}


def score(gold, pred):
    def acc(rows, f):
        return 100 * sum(f(g, pred.get(g["id"], {})) for g in rows) / max(len(rows), 1)
    typ = lambda g, p: p.get("type") == g["type"]
    dat = lambda g, p: p.get("date") == g["date"]
    tim = lambda g, p: p.get("time") == g["time"]
    full = lambda g, p: typ(g, p) and dat(g, p) and tim(g, p)
    rows = list(gold.values())
    subsets = {"all": rows,
               "ambiguous": [g for g in rows if g["flags"].get("ambiguous")],
               "noisy": [g for g in rows if g["flags"].get("noisy")],
               "english": [g for g in rows if g["flags"].get("english")],
               "past": [g for g in rows if g["direction"] == "past" and g["date"]],
               "timed": [g for g in rows if g["date"]]}
    out = {k: {"n": len(v), "type": acc(v, typ), "date": acc(v, dat), "time": acc(v, tim), "full": acc(v, full)}
           for k, v in subsets.items()}
    # macro-F1 over types
    f1s = []
    for c in ("reminder", "note", "goal"):
        tp = sum(1 for g in rows if g["type"] == c and pred.get(g["id"], {}).get("type") == c)
        fp = sum(1 for g in rows if g["type"] != c and pred.get(g["id"], {}).get("type") == c)
        fn = sum(1 for g in rows if g["type"] == c and pred.get(g["id"], {}).get("type") != c)
        f1s.append(2 * tp / max(2 * tp + fp + fn, 1))
    out["all"]["type_macroF1"] = 100 * sum(f1s) / 3
    ms = sorted(p["ms"] for p in pred.values() if "ms" in p)
    if ms:
        out["latency_ms"] = {"median": statistics.median(ms), "p95": ms[int(0.95 * (len(ms) - 1))], "mean": statistics.mean(ms)}
    out["coverage"] = 100 * sum(1 for g in rows if g["id"] in pred) / len(rows)
    return out


def table(name, s):
    lat = s.get("latency_ms", {})
    line = f"{name:28} " + " ".join(f"{s[k]['full']:6.1f}" for k in ("all", "ambiguous", "noisy", "english", "past"))
    line += f" | type {s['all']['type']:5.1f} date {s['all']['date']:5.1f} time {s['all']['time']:5.1f}"
    if lat: line += f" | {lat['median']:8.1f} ms med {lat['p95']:8.1f} p95"
    if s["coverage"] < 100: line += f" | cov {s['coverage']:.0f}%"
    return line


if __name__ == "__main__":
    gold = load(sys.argv[1])
    print(f"{'system':28} {'full':>6} {'ambig':>6} {'noisy':>6} {'eng':>6} {'past':>6}")
    for p in sys.argv[2:]:
        print(table(p.split("/")[-1].replace(".jsonl", ""), score(gold, load(p))))
