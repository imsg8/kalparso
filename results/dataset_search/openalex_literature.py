"""Run the literature queries that Semantic Scholar still refused (HTTP 429) against the OpenAlex works search
instead: top 50 per query by relevance, with title, year and venue. Usage: python openalex_literature.py <in.json> <out.json>"""
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
out = {"date": time.strftime("%Y-%m-%d"), "service": "OpenAlex works search", "rerun_of": sys.argv[1].split("/")[-1], "queries": failed, "literature": {}}
for q in failed:
    s = get(f"https://api.openalex.org/works?search={urllib.parse.quote(q)}&per-page=50&select=title,publication_year,primary_location")
    out["literature"][q] = [{"t": x.get("title"), "y": x.get("publication_year"),
                             "v": (((x.get("primary_location") or {}).get("source")) or {}).get("display_name")} for x in s["results"]] if "results" in s else s
    print(q, len(out["literature"][q]) if isinstance(out["literature"][q], list) else out["literature"][q], flush=True)
    time.sleep(5)
json.dump(out, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
