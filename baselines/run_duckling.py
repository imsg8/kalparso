"""Duckling (Meta's rule-based parser, rasa/duckling image) as a baseline. Takes the first time value it finds.
Usage: python run_duckling.py in.jsonl out.jsonl [locale] [url]"""
import json, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta

src, dst = sys.argv[1:3]
loc = sys.argv[3] if len(sys.argv) > 3 else "en_US"
url = sys.argv[4] if len(sys.argv) > 4 else "http://localhost:8000/parse"
IST = timezone(timedelta(hours=5, minutes=30))
with open(dst, "w") as f:
    for r in map(json.loads, open(src)):
        ref = int(datetime.fromisoformat(r["anchor"]).replace(tzinfo=IST).timestamp() * 1000)
        body = urllib.parse.urlencode({"locale": loc, "text": r["text"], "reftime": ref, "tz": "Asia/Kolkata",
                                       "dims": '["time","duration"]'}).encode()
        t0 = time.perf_counter()
        out = json.load(urllib.request.urlopen(url, body, timeout=30))
        ms = (time.perf_counter() - t0) * 1000
        date = tm = None
        for e in out:
            if e["dim"] != "time": continue
            v = e["value"]
            if v.get("type") == "interval": v = v.get("from") or v.get("to") or {}
            if "value" not in v: continue
            dt = datetime.fromisoformat(v["value"])
            date = dt.date().isoformat()
            if v.get("grain") in ("hour", "minute", "second"): tm = dt.strftime("%H:%M")
            break
        f.write(json.dumps({"id": r["id"], "type": "reminder" if date else "note", "date": date, "time": tm, "ms": ms}) + "\n")
