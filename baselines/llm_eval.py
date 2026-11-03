"""Untrained LLM baselines through Ollama, in four prompt modes. Same spec, same anchor, JSON-schema constrained,
greedy decoding. Runs on the Kaggle GPU (accuracy) and on the desktop CPU (latency).
  few    spec conventions + 6 worked examples, the model writes {type, date, time}
  zero   spec conventions only, no examples
  spans  the model writes {type, direction, spans}; our grounder computes the date (reading vs arithmetic test)
  think  as few, with thinking on (qwen3 only), on a sample
Usage: python llm_eval.py MODEL MODE in.jsonl out.jsonl [limit] [workers]"""
import json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (os.path.join(HERE, "..", "src"), HERE, os.environ.get("KP_SRC", "")):
    if p: sys.path.insert(0, p)
from ground import ground_entry
from run_llm import SYSTEM, SHOTS

# v2: the same conventions our grounder uses after the human dev-split analysis, so the comparison stays fair
SYSTEM2 = SYSTEM.replace("A time with no day = today, or tomorrow if already passed.",
    "A clock time with no day = the next time that clock reading comes round (am or pm, whichever is sooner, but never "
    "1:00-5:59 am unless raat/am is said); with a day, 1-7 = pm and 8-11 = am, except wake-up/alarm entries = am. "
    "kal raat 2 baje / aaj raat 12 baje = after midnight, so the next calendar day. 'Sunday hai' / 'Monday hai aaj' "
    "names today. 'next to next Friday' = the Friday after the coming one. 'next week X' = X in next calendar week. "
    "'N hafte baad' = N weeks. 'end of month/week' = its last day; 'is saal' deadline = 31 Dec. "
    "'15 tareekh' on the 15th = today. 'agle mahine 22 ko' = 22nd of next month.")
OLLAMA = os.environ.get("OLLAMA", "http://localhost:11434")
SCHEMA = {"type": "object", "properties": {"type": {"type": "string", "enum": ["reminder", "note", "goal"]},
          "date": {"type": ["string", "null"]}, "time": {"type": ["string", "null"]}}, "required": ["type", "date", "time"]}
SPAN_SCHEMA = {"type": "object", "properties": {
    "type": {"type": "string", "enum": ["reminder", "note", "goal"]},
    "direction": {"type": "string", "enum": ["future", "past"]},
    "spans": {"type": "array", "items": {"type": "object", "properties": {
        "label": {"type": "string", "enum": ["DAY", "WD", "DATE", "TIME", "PART", "DUR"]},
        "text": {"type": "string"}}, "required": ["label", "text"]}}},
    "required": ["type", "direction", "spans"]}
SPAN_SYSTEM = """You read one dictated planner entry (Hinglish or English) and mark its time expressions. Return JSON
{"type","direction","spans"}. You do NOT compute dates; a program does that from your spans.
type: "reminder" (to be told about later), "note" (fact, idea or past event), "goal" (long-term aim, no date).
direction: "past" if the time words refer to something that already happened (verb tha, kiya, gaya, hui, bola...), else "future".
spans: copy the exact words from the entry, each with a label:
  DAY  aaj, kal, parso, narso, today, tomorrow, yesterday, day after tomorrow
  WD   a weekday with its modifier (agle somvar, next Friday, pichle Monday, Sunday)
  DATE a day of the month, with month if said (15 tareekh, 3 Nov)
  TIME a clock time (5 baje, saade 7, 4:30 pm, paune 9)
  PART subah, dopahar, shaam, raat, morning, evening, night
  DUR  an offset from now (2 ghante baad, in 20 min, 3 din baad, 2 din pehle)
No time words: spans = []."""
SPAN_SHOTS = [
    ("kal subah saade 7 baje gym jaana", {"type": "reminder", "direction": "future", "spans": [
        {"label": "DAY", "text": "kal"}, {"label": "PART", "text": "subah"}, {"label": "TIME", "text": "saade 7 baje"}]}),
    ("kal Rahul se baat hui, project ka scope badh gaya", {"type": "note", "direction": "past", "spans": [
        {"label": "DAY", "text": "kal"}]}),
    ("agle somvar paune 9 dentist", {"type": "reminder", "direction": "future", "spans": [
        {"label": "WD", "text": "agle somvar"}, {"label": "TIME", "text": "paune 9"}]}),
    ("dedh ghante baad Maama ko call karna", {"type": "reminder", "direction": "future", "spans": [
        {"label": "DUR", "text": "dedh ghante baad"}]}),
    ("life mein ek baar Japan jaana hai", {"type": "goal", "direction": "future", "spans": []}),
    ("wifi password router ke peeche likha hai", {"type": "note", "direction": "future", "spans": []}),
]


def messages(mode, r):
    now = f"Now: {r['anchor']} ({r['weekday']})"
    if mode == "spans":
        m = [{"role": "system", "content": SPAN_SYSTEM}]
        for t, y in SPAN_SHOTS:
            m += [{"role": "user", "content": f"Entry: {t}"}, {"role": "assistant", "content": json.dumps(y)}]
        return m + [{"role": "user", "content": f"Entry: {r['text']}"}]
    m = [{"role": "system", "content": SYSTEM2 if mode in ("few2", "think2") else SYSTEM}]
    if mode != "zero":
        for a, t, y in SHOTS:
            m += [{"role": "user", "content": f"Now: {a}\nEntry: {t}"}, {"role": "assistant", "content": json.dumps(y)}]
    return m + [{"role": "user", "content": f"{now}\nEntry: {r['text']}"}]


def call(model, mode, msgs):
    think = os.environ.get("KP_THINK") or mode in ("think", "think2")  # KP_THINK: think level for reasoning-only models (gpt-oss: "low")
    body = {"model": model, "messages": msgs, "stream": False, "think": think, "keep_alive": "30m",
            "format": SPAN_SCHEMA if mode == "spans" else SCHEMA,
            "options": {"temperature": 0, "seed": 0, "num_ctx": 4096 if think else 2048,
                        "num_predict": 3000 if think else (160 if mode == "spans" else 48)}}
    req = urllib.request.Request(f"{OLLAMA}/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=900))


def one(model, mode, r):
    t0 = time.perf_counter()
    try:
        out = call(model, mode, messages(mode, r))
        y = json.loads(out["message"]["content"])
        if mode == "spans":
            spans = [(s["label"], s["text"]) for s in y.get("spans", []) if s.get("text")]
            d, t = ground_entry(spans, y.get("direction", "future"), datetime.fromisoformat(r["anchor"]), y.get("type"), r["text"])
            y = {"type": y.get("type"), "date": d, "time": t, "direction": y.get("direction"), "spans": spans}
        y["eval_count"] = out.get("eval_count"); y["prompt_eval_count"] = out.get("prompt_eval_count")
    except Exception as e:
        y = {"type": None, "date": None, "time": None, "err": str(e)[:120]}
    y["ms"] = (time.perf_counter() - t0) * 1000
    return {"id": r["id"], **y}


if __name__ == "__main__":
    model, mode, src, dst = sys.argv[1:5]
    limit = int(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[5] != "-" else None
    workers = int(sys.argv[6]) if len(sys.argv) > 6 else 1
    rows = [json.loads(l) for l in open(src)]
    if limit: rows = rows[::max(len(rows) // limit, 1)][:limit]   # evenly spaced sample, same for every model
    one(model, "few", {"id": "warm", "anchor": "2026-01-01T09:00", "weekday": "Thursday", "text": "warmup"})
    t0 = time.time()
    with open(dst, "w") as f, ThreadPoolExecutor(workers) as ex:
        for i, y in enumerate(ex.map(lambda r: one(model, mode, r), rows)):
            f.write(json.dumps(y, ensure_ascii=False) + "\n"); f.flush()
            if i % 100 == 0: print(model, mode, i, f"{time.time() - t0:.0f}s", flush=True)
    print("done", model, mode, len(rows), f"{time.time() - t0:.0f}s", flush=True)
