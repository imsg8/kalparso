"""Rules-only baseline: lexicon span finder + past-marker tense heuristic + keyword type rules, then ground.py.
Also used as route A's fallback span finder."""
from ground import kinds, ground_entry
from lexicon import PAST_MARKERS

NUMLIKE = ("NUM", "AADHA", "DEDH", "DHAI")
UNITS = ("HOUR_UNIT", "MIN_UNIT", "DAY_UNIT", "WEEK_UNIT")
GOAL_KW = ("goal", "life mein", "zindagi", "seekh", "someday", "learn to", "become", "ek baar", "is saal", "shuru karna", "bolni hai", "launch karni")
REMIND_KW = ("remind", "yaad dila", "don't forget", "bhoolna mat", "reminder")


def find_spans(text):
    ks = kinds(text)
    spans, i, n = [], 0, len(ks)
    k = lambda j: ks[j][0] if 0 <= j < n else None
    raw = lambda a, b: " ".join(str(x[2]) for x in ks[a:b])
    while i < n:
        t = k(i)
        # offsets: "N ghante baad", "in 2 hours", "3 din pehle", "aadhe ghante mein"
        j = i + 1 if t == "AFTER" and k(i + 1) in NUMLIKE else i
        if k(j) in NUMLIKE and k(j + 1) in UNITS:
            end = j + 2 + (1 if k(j + 2) in ("AFTER", "BEFORE") else 0)
            if j > i or k(j + 2) in ("AFTER", "BEFORE"):
                spans.append(("DUR", raw(i, end))); i = end; continue
        if t == "AFTER" and k(i + 1) == "WORD" and ks[i + 1][2] in ("half",):
            pass
        # clock times
        if t in ("SAADE", "SAVA", "PAUNE") and k(i + 1) == "NUM":
            end = i + 2 + (1 if k(i + 2) in ("BAJE", "AMPM") else 0)
            spans.append(("TIME", raw(i, end))); i = end; continue
        if t in ("DEDH", "DHAI") and k(i + 1) not in UNITS:
            end = i + 1 + (1 if k(i + 1) == "BAJE" else 0)
            spans.append(("TIME", raw(i, end))); i = end; continue
        if t == "CLOCK":
            end = i + 1 + (1 if k(i + 1) in ("BAJE", "AMPM") else 0)
            spans.append(("TIME", raw(i, end))); i = end; continue
        if t == "NUM" and k(i + 1) in ("BAJE", "AMPM"):
            spans.append(("TIME", raw(i, i + 2))); i += 2; continue
        if t == "NUM" and k(i - 1) == "WORD" and ks[i - 1][2] in ("at", "pe", "by") and 1 <= ks[i][1] <= 12 \
                and k(i + 1) not in UNITS:
            spans.append(("TIME", raw(i, i + 1))); i += 1; continue
        if t == "PERIOD_END":
            spans.append(("DATE", raw(i, i + 1))); i += 1; continue
        if t == "MONTH_REL" and k(i + 1) == "NUM":
            end = i + 2 + (1 if k(i + 2) == "TAREEKH" else 0)
            spans.append(("DATE", raw(i, end))); i = end; continue
        if t == "MONTH" and k(i + 1) == "WORD" and ks[i + 1][2] in ("mein", "me") and k(i + 2) == "NUM":
            spans.append(("DATE", raw(i, i + 3))); i += 3; continue
        # dates
        if t == "NUM" and isinstance(ks[i][1], int) and 1 <= ks[i][1] <= 31:
            nxt = i + 1 + (1 if k(i + 1) == "WORD" and ks[i + 1][2] in ("th", "st", "nd", "rd") else 0)
            if k(nxt) in ("MONTH", "TAREEKH"):
                spans.append(("DATE", raw(i, nxt + 1))); i = nxt + 1; continue
            if ks[i][1] >= 13 and k(i + 1) == "WORD" and ks[i + 1][2] in ("ko", "ki") and k(i + 2) not in UNITS + ("BAJE",):
                spans.append(("DATE", raw(i, i + 1))); i += 1; continue
        if t == "MONTH" and k(i + 1) == "NUM":
            spans.append(("DATE", raw(i, i + 2))); i += 2; continue
        # weekdays with modifiers
        if t in ("WD_NEXT", "WD_PREV", "WD_THIS", "WD_NEXT2") and k(i + 1) == "WD":
            spans.append(("WD", raw(i, i + 2))); i += 2; continue
        if t == "WD":
            spans.append(("WD", raw(i, i + 1))); i += 1; continue
        if t == "DAY":
            spans.append(("DAY", raw(i, i + 1))); i += 1; continue
        if t == "PART":
            spans.append(("PART", raw(i, i + 1))); i += 1; continue
        i += 1
    # "in half an hour" / "aadhe ghante": AADHA then unit, handled above; English "half an hour"
    return spans


def direction(text):
    low = " " + text.lower() + " "
    return "past" if any(f" {m} " in low for m in PAST_MARKERS) else "future"


def predict(text, anchor):
    spans = find_spans(text)
    d = direction(text)
    low = text.lower()
    if any(w in low for w in GOAL_KW) and not spans: typ = "goal"
    elif d == "past" and spans: typ = "note"
    elif spans or any(w in low for w in REMIND_KW): typ = "reminder"
    else: typ = "note"
    date, time = ground_entry(spans, d, anchor, typ, text)
    return {"type": typ, "date": date, "time": time, "spans": spans, "direction": d}
