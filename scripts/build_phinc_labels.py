"""PHINC weak tense labels: a Hinglish tweet gets 'past' or 'future' from its English translation's verbs and time words
(rows with both or neither are dropped), then the two classes are balanced. These rows train the tense head only.
Usage: python -I scripts/build_phinc_labels.py <PHINC csv> data/v3/phinc_dir.jsonl"""
import csv, json, re, sys, collections, random
csv.field_size_limit(10**8)
src, dst = sys.argv[1], sys.argv[2]
PAST = re.compile(r"\b(was|were|did|had|went|yesterday|ago|came|saw|said|told|got|made|took|gave|met|happened|watched|ate|called)\b", re.I)
FUT = re.compile(r"\b(will|won't|shall|tomorrow|going to|gonna|'ll|next week|next month)\b", re.I)
out, c = [], collections.Counter()
for r in csv.DictReader(open(src, encoding="utf-8", errors="replace")):
    t, e = (r.get("Sentence") or "").strip(), (r.get("English_Translation") or "").strip()
    if not t or not e or len(t) > 200: continue
    t = re.sub(r"@\w+|https?://\S+|#\w+", "", t).strip()
    if len(t.split()) < 3: continue
    p, f = bool(PAST.search(e)), bool(FUT.search(e))
    if p == f: continue
    d = "past" if p else "future"; c[d] += 1
    out.append({"text": t, "direction": d, "dir_only": True})
random.Random(0).shuffle(out)
k = min(c.values())  # balance the two classes
bal = [x for x in out if x["direction"] == "past"][:k] + [x for x in out if x["direction"] == "future"][:k]
with open(dst, "w") as fh:
    for x in bal: fh.write(json.dumps(x, ensure_ascii=False) + "\n")
print(c, "kept", len(bal))
