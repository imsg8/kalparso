"""Rerun the literature queries that failed with HTTP 429 in search_2026-11-01.json, against the same
Semantic Scholar endpoint and fields, with longer back-off. Usage: python rerun_literature.py <in.json> <out.json>"""
import json, sys, time, urllib.parse, urllib.request
src = json.load(open(sys.argv[1]))
failed = [q for q, v in src["literature"].items() if isinstance(v, dict) and "error" in v]
def get(url):
    err = None
    for i in range(6):
        try:
            r = urllib.request.Request(url, headers={"User-Agent": "kalparso-search"})
            return json.load(urllib.request.urlopen(r, timeout=30))
        except Exception as e:
            err = str(e); time.sleep(10 * (i + 1))
    return {"error": err}
out = {"date": time.strftime("%Y-%m-%d"), "rerun_of": "search_2026-11-01.json", "queries": failed, "literature": {}}
for q in failed:
    s = get(f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(q)}&fields=title,year,venue&limit=50")
    out["literature"][q] = [{"t": x.get("title"), "y": x.get("year"), "v": x.get("venue")} for x in s.get("data", [])] if "data" in s else s
    print(q, len(out["literature"][q]) if isinstance(out["literature"][q], list) else out["literature"][q], flush=True)
    time.sleep(30)
json.dump(out, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
