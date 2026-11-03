"""v1 few-shot LLM prompt (spec conventions, SYSTEM and SHOTS), imported by llm_eval.py for the "few" mode.
Also runs on its own through Ollama: the model returns JSON {type, date, time}.
Usage: python3 run_llm.py MODEL in.jsonl out.jsonl [limit]"""
import json, sys, time, urllib.request

OLLAMA = "http://localhost:11434"
SYSTEM = """You read one dictated planner entry (Hinglish or English) and return JSON {"type","date","time"}.
type: "reminder" (to be told about later), "note" (fact, idea or past event), "goal" (long-term aim, no date).
date: YYYY-MM-DD or null. time: HH:MM 24h or null.
Rules: kal = tomorrow (+1) for future/planned things, yesterday (-1) if the verb is past (tha, kiya, gaya, hui, bola...). parso = +2 or -2, narso = +3 or -3, same rule.
Bare weekday = next one after today (previous one if past). agle X = X in next calendar week (Mon-Sun). pichle X = X in previous calendar week.
"15 tareekh" = next 15th. subah/dopahar/shaam/raat alone = 09:00/13:00/18:00/21:00.
Bare hour: 1-7 = pm, 8-11 = am, 12 = noon. subah h = am; shaam h = pm; raat 7-11 = pm; dopahar 1-6 = pm.
saade h = h:30, sava h = h:15, paune h = (h-1):45, dedh = 1:30, dhai = 2:30.
A time with no day = today, or tomorrow if already passed. "2 ghante baad" = now + 2h (sets date and time). "3 din baad" = date only.
Goals and undated notes: date and time null."""
SHOTS = [
    ("2026-10-30T21:15 (Friday)", "kal subah saade 7 baje gym jaana", {"type": "reminder", "date": "2026-10-31", "time": "07:30"}),
    ("2026-10-30T21:15 (Friday)", "kal Rahul se baat hui, project ka scope badh gaya", {"type": "note", "date": "2026-10-29", "time": None}),
    ("2026-10-30T21:15 (Friday)", "agle somvar paune 9 dentist", {"type": "reminder", "date": "2026-11-02", "time": "08:45"}),
    ("2026-10-30T21:15 (Friday)", "dedh ghante baad Maama ko call karna", {"type": "reminder", "date": "2026-10-30", "time": "22:45"}),
    ("2026-10-30T21:15 (Friday)", "life mein ek baar Japan jaana hai", {"type": "goal", "date": None, "time": None}),
    ("2026-10-30T21:15 (Friday)", "wifi password router ke peeche likha hai", {"type": "note", "date": None, "time": None}),
]
SCHEMA = {"type": "object", "properties": {"type": {"type": "string", "enum": ["reminder", "note", "goal"]},
          "date": {"type": ["string", "null"]}, "time": {"type": ["string", "null"]}}, "required": ["type", "date", "time"]}


def messages(anchor, weekday, text):
    m = [{"role": "system", "content": SYSTEM}]
    for a, t, y in SHOTS:
        m += [{"role": "user", "content": f"Now: {a}\nEntry: {t}"}, {"role": "assistant", "content": json.dumps(y)}]
    m.append({"role": "user", "content": f"Now: {anchor} ({weekday})\nEntry: {text}"})
    return m


def call(model, msgs):
    body = {"model": model, "messages": msgs, "stream": False, "think": False, "format": SCHEMA, "keep_alive": "15m",
            "options": {"temperature": 0, "num_ctx": 2048, "num_predict": 48}}
    req = urllib.request.Request(f"{OLLAMA}/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=300))


if __name__ == "__main__":
    model, src, dst = sys.argv[1:4]
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else None
    rows = [json.loads(l) for l in open(src)][:limit]
    call(model, messages("2026-01-01T09:00", "Thursday", "warmup"))  # load weights; cold start reported separately
    with open(dst, "w") as f:
        for i, r in enumerate(rows):
            t0 = time.perf_counter()
            try:
                out = call(model, messages(r["anchor"], r["weekday"], r["text"]))
                y = json.loads(out["message"]["content"])
            except Exception as e:
                y = {"type": None, "date": None, "time": None, "err": str(e)[:80]}
            ms = (time.perf_counter() - t0) * 1000
            f.write(json.dumps({"id": r["id"], "type": y.get("type"), "date": y.get("date"), "time": y.get("time"), "ms": ms}) + "\n")
            f.flush()
            if i % 25 == 0: print(model, i, f"{ms:.0f} ms", flush=True)
