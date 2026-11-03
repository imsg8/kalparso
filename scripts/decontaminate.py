"""Remove synthetic rows whose text matches a human test entry (ignoring case and punctuation), so no human sentence
is ever seen in training. Applied to the generator's output to make data/v3.
Usage: python -I scripts/decontaminate.py <generated dir> <out dir> [data/human/test_human.jsonl]"""
import json, os, re, sys
src, dst = sys.argv[1], sys.argv[2]
human = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "human", "test_human.jsonl")
norm = lambda t: " ".join(re.sub(r"[^\w\s]", " ", t.lower()).split())
H = {norm(json.loads(l)["text"]) for l in open(human)}
os.makedirs(dst, exist_ok=True)
for name in ("train", "dev", "test_synth"):
    rows = [json.loads(l) for l in open(f"{src}/{name}.jsonl")]
    kept = [r for r in rows if norm(r["text"]) not in H]
    with open(f"{dst}/{name}.jsonl", "w") as f:
        for r in kept: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(name, len(rows), "->", len(kept))
