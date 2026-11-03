"""Out-of-domain check on NTX Hindi (formal Devanagari, Chen et al., 2023), zero-shot.
  python bench/eval_ntx.py [MODEL_DIR ...]          e.g. the three Hugging Face model folders
Reads data/external/ntx_hindi/ntxt-HI-t.jsonl (see scripts/fetch_external.md) and writes
  data/external/ntx_hindi/ntx_all.jsonl     469 sentences with at least one NTX result, gold span texts
  data/external/ntx_hindi/ntx_points.jsonl  140 sentences whose only result is one date, time or datetime
  results/human/ntx_span_detection.json     span P/R/F1 per system (relaxed overlap)
  results/human/ntx_grounding.json          grounding accuracy on the 140 single expressions
  results/human/ntxall_NAME.jsonl, ntx_NAME_points.jsonl   per-sentence predictions
The rules baseline always runs. Each MODEL_DIR is named by its folder (kalparso-muril -> muril)."""
import json, os, re, sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, f"{ROOT}/src")
from rules import find_spans, predict

D = f"{ROOT}/data/external/ntx_hindi"
POINT_TYPES = ("datetimeV2.date", "datetimeV2.datetime", "datetimeV2.time")


def parse(i, row):
    # the sentence is the last line of the instruction, and the anchor is the last reference date-time it states
    inp = row["inputs"]
    anchor = re.findall(r"संदर्भिक दिनांक-समय:\s*(\S+)", inp)
    return {"id": f"ntx-{i:04d}", "text": inp.rstrip().split("\n")[-1].strip(),
            "anchor": anchor[-1][:16] if anchor else None,
            "results": json.loads("{" + row["targets"] + "}")["Results"]}


def build():
    raw = [json.loads(l) for l in open(f"{D}/ntxt-HI-t.jsonl", encoding="utf-8")]
    P = [parse(i, r) for i, r in enumerate(raw)]
    every, points = [], []
    for o in P:
        if not o["results"]: continue
        every.append({"id": o["id"], "text": o["text"], "anchor": o["anchor"], "weekday": "Monday",
                      "gold_spans": [x.get("Text") for x in o["results"] if x.get("Text")]})
        pts = [x for x in o["results"] if x.get("TypeName") in POINT_TYPES]
        if len(pts) != 1 or len(o["results"]) != 1: continue
        x = pts[0]; vals = [v.get("value") for v in x["Resolution"]["values"] if v.get("value")]
        if vals:
            points.append({"id": o["id"], "text": o["text"], "anchor": o["anchor"], "weekday": "Monday",
                           "ntx_type": x["TypeName"].split(".")[1], "span": x["Text"], "gold_values": vals})
    for name, rows in (("ntx_all", every), ("ntx_points", points)):
        with open(f"{D}/{name}.jsonl", "w", encoding="utf-8") as f:
            for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(raw), every, points


def overlap(a, b, text):
    i, j = text.find(a), text.find(b)
    return i >= 0 and j >= 0 and i < j + len(b) and j < i + len(a)


def span_prf(G, spans_of):
    # a gold span is found if any predicted span overlaps it, and a predicted span is spurious if it overlaps none
    tp = fn = fp = 0
    for g in G:
        pred = spans_of(g)
        for s in g["gold_spans"]:
            if any(overlap(s, p, g["text"]) for p in pred): tp += 1
            else: fn += 1
        fp += sum(1 for p in pred if not any(overlap(s, p, g["text"]) for s in g["gold_spans"]))
    P, R = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
    return f"P {100*P:.1f} R {100*R:.1f} F1 {200*P*R/max(P+R,1e-9):.1f}"


def grounded(g, p):
    for v in g["gold_values"]:
        if g["ntx_type"] == "date" and p.get("date") == v: return True
        if g["ntx_type"] == "datetime" and p.get("date") == v[:10] and p.get("time") == v[11:16]: return True
        if g["ntx_type"] == "time" and p.get("time") == v[:5]: return True
    return False


def grounding(points, pred_of):
    by = {}
    for g in points: by.setdefault(g["ntx_type"], []).append(grounded(g, pred_of(g)))
    tot = [x for v in by.values() for x in v]
    return {"all": f"{100*sum(tot)/len(tot):.1f}% of {len(tot)}",
            **{k: f"{100*sum(v)/len(v):.0f}% of {len(v)}" for k, v in sorted(by.items())}}


if __name__ == "__main__":
    n, every, points = build()
    print(f"NTX: {n} sentences, {len(every)} with a result ({sum(len(g['gold_spans']) for g in every)} gold spans), "
          f"{len(points)} single date/time expressions")
    anchor = lambda g: datetime.fromisoformat(g["anchor"])
    systems = [("rules_v2", lambda t, a: {**predict(t, a), "spans": find_spans(t)})]
    if sys.argv[1:]:
        from kalparso import KalParso
    for d in sys.argv[1:]:
        systems.append((os.path.basename(os.path.normpath(d)).replace("kalparso-", ""), KalParso(d, "model.onnx", threads=4)))
    os.makedirs(f"{ROOT}/results/human", exist_ok=True)
    spans, ground = {}, {}
    for name, run in systems:
        out = {}
        for part, rows in (("all", every), ("points", points)):
            out[part] = {g["id"]: run(g["text"], anchor(g)) for g in rows}
            dst = f"{ROOT}/results/human/" + (f"ntxall_{name}.jsonl" if part == "all" else f"ntx_{name}_points.jsonl")
            with open(dst, "w", encoding="utf-8") as f:
                for k, p in out[part].items():
                    f.write(json.dumps({"id": k, "type": p["type"], "date": p["date"], "time": p["time"],
                                        "spans": [list(x) for x in p["spans"]]}, ensure_ascii=False) + "\n")
        spans[name] = span_prf(every, lambda g: [t for _, t in out["all"][g["id"]]["spans"]])
        ground[name] = grounding(points, lambda g: out["points"][g["id"]])
    json.dump(spans, open(f"{ROOT}/results/human/ntx_span_detection.json", "w"), indent=1)
    json.dump(ground, open(f"{ROOT}/results/human/ntx_grounding.json", "w"), indent=1)
    for k in spans: print(f"{k:10s} spans {spans[k]}   grounding {ground[k]}")
