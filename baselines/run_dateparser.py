"""dateparser baseline (off-the-shelf, hi+en). It finds dates only, so type comes from a majority rule
(reminder if a date is found, else note). Usage: python run_dateparser.py in.jsonl out.jsonl"""
import json, sys, time
from datetime import datetime
from dateparser.search import search_dates

SETTINGS = {"PREFER_DATES_FROM": "future", "RETURN_AS_TIMEZONE_AWARE": False}

src, dst = sys.argv[1], sys.argv[2]
with open(dst, "w") as f:
    for r in map(json.loads, open(src)):
        anchor = datetime.fromisoformat(r["anchor"])
        t0 = time.perf_counter()
        try:
            hits = search_dates(r["text"], languages=["en", "hi"], settings={**SETTINGS, "RELATIVE_BASE": anchor})
        except Exception:
            hits = None
        ms = (time.perf_counter() - t0) * 1000
        date = tm = None
        if hits:
            txt, dt = hits[0]
            date = dt.date().isoformat()
            # dateparser fills the anchor's clock when no time is given; treat that as no time
            if (dt.hour, dt.minute) != (anchor.hour, anchor.minute) and (dt.hour, dt.minute) != (0, 0):
                tm = dt.strftime("%H:%M")
        f.write(json.dumps({"id": r["id"], "type": "reminder" if date else "note", "date": date, "time": tm, "ms": ms}) + "\n")
