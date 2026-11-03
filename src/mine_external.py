"""Mine real human-written Hinglish from external CSVs for time expressions (reads CSV text only).
For parallel corpora, the English translation gives a free tense label for kal/parso:
'yesterday' -> past, 'tomorrow' -> future.
Usage: python -I mine_external.py <csv> <hinglish_col> [english_col] [out.jsonl]"""
import csv, json, re, sys
from collections import Counter

csv.field_size_limit(10**8)
TIME = re.compile(r"\b(kal|kl|parso\w*|narso\w*|aaj|baje|bje|subah|subha|shaam|sham|raat|dopahar|dopehar|"
                  r"somvar|mangalvar|budhvar|guruvar|shukravar|shanivar|ravivar|itvaar|agle|pichle|"
                  r"ghante|ghanta|tareekh|tarikh|saade|sava|paune|dedh|dhai)\b", re.I)
AMBIG = re.compile(r"\b(kal|kl|parso\w*|narso\w*)\b", re.I)

src, col = sys.argv[1], sys.argv[2]
en_col = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "-" else None
out = sys.argv[4] if len(sys.argv) > 4 else None
rows = list(csv.DictReader(open(src, encoding="utf-8", errors="replace")))
hits, words, tense = [], Counter(), Counter()
for i, r in enumerate(rows):
    t = (r.get(col) or "").strip()
    if not TIME.search(t): continue
    words.update(w.lower() for w in TIME.findall(t))
    rec = {"src": src.split("/")[-2], "row": i, "text": t}
    if en_col:
        e = (r.get(en_col) or "").lower()
        rec["english"] = r.get(en_col)
        if AMBIG.search(t):
            lab = ("past" if re.search(r"\b(yesterday|day before)\b", e) else
                   "future" if re.search(r"\b(tomorrow|day after)\b", e) else "unclear")
            rec["silver_direction"] = lab; tense[lab] += 1
    hits.append(rec)
print(f"{src.split('/')[-2]}: {len(rows)} rows, {len(hits)} with time words ({100 * len(hits) / max(len(rows), 1):.1f}%)")
print("  top words:", words.most_common(12))
if en_col: print("  kal/parso tense from translation:", dict(tense))
if out:
    with open(out, "w") as f:
        for h in hits: f.write(json.dumps(h, ensure_ascii=False) + "\n")
