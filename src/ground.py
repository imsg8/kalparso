"""Deterministic grounder: labelled spans + direction + anchor -> (date, time).
Implements the conventions in spec.md. Shared by gold generation, the rules baseline and route A."""
import re
from datetime import datetime, timedelta, date as Date

from lexicon import (INDEX, DAY_OFFSET, DAY_MAG, PART_DEFAULT)

TOK = re.compile(r"\d{1,2}[:.]\d{2}|\d+|[a-z]+(?:'[a-z]+)?|[ऀ-ॿ]+")


def tokens(s):
    return TOK.findall(s.lower())


def lookup(tok):
    return INDEX.get(tok)


def kinds(s):
    """[(kind, canonical, raw)] for each token; multiword variants matched greedily."""
    toks, out, i = tokens(s), [], 0
    while i < len(toks):
        for n in (4, 3, 2, 1):
            phrase = " ".join(toks[i:i + n])
            hit = lookup(phrase) if len(toks[i:i + n]) == n else None
            if hit:
                out.append((hit[0], hit[1], phrase)); i += n; break
        else:
            t = toks[i]
            if re.fullmatch(r"\d{1,2}[:.]\d{2}", t): out.append(("CLOCK", t.replace(".", ":"), t))
            elif t == "noon": out.append(("CLOCK", "12:00", t))
            elif t == "midnight": out.append(("CLOCK", "00:00", t))
            elif t.isdigit(): out.append(("NUM", int(t), t))
            elif t in ("am", "pm"): out.append(("AMPM", t, t))
            else: out.append(("WORD", t, t))
            i += 1
    for j in range(len(out) - 1):  # informal spelling writes "saat baje" as "sat baje": a weekday never takes baje
        if out[j][0] == "WD" and out[j][2] == "sat" and out[j + 1][0] == "BAJE":
            out[j] = ("NUM", 7, "sat")
    return out


def number(ks):
    for k, c, _ in ks:
        if k == "NUM": return c
    return None


def parse_clock(ks):
    """TIME span -> (hour 1-12 or 0-23, minute, ampm or None)."""
    h = m = None; ampm = None
    for k, c, _ in ks:
        if k == "CLOCK":
            hh, mm = c.split(":"); h, m = int(hh), int(mm)
        elif k == "AMPM": ampm = c
    if h is None:
        n = number(ks)
        names = {k for k, _, _ in ks}
        if "DEDH" in names: h, m = 1, 30
        elif "DHAI" in names: h, m = 2, 30
        elif n is not None:
            h, m = n, 0
            if "SAADE" in names: m = 30
            elif "SAVA" in names: m = 15
            elif "PAUNE" in names: h, m = (n - 1) or 12, 45
    return h, m, ampm


def to24(h, m, ampm, part):
    if h is None or not (0 <= h <= 23 and 0 <= (m or 0) <= 59): return None  # model spans can be junk
    if ampm == "pm": return (h % 12 + 12, m)
    if ampm == "am": return (h % 12, m)
    if h > 12: return (h, m)
    if part == "subah": return (h % 12, m)
    if part == "dopahar": return (h + 12 if h <= 6 else h, m)
    if part == "shaam": return (h % 12 + 12, m)
    if part == "raat": return (h + 12 if 7 <= h <= 11 else h % 12, m)
    if 1 <= h <= 7: return (h + 12, m)
    return (h, m)


def add_months(d, n):
    y, mo = d.year + (d.month - 1 + n) // 12, (d.month - 1 + n) % 12 + 1
    return y, mo


def safe_date(y, mo, d, step):
    """Date(y, mo, d); if that day does not exist (29 Feb, 31 Apr), move month by month in direction step."""
    for _ in range(12):
        try: return Date(y, mo, d)
        except ValueError: y, mo = add_months(Date(y, mo, 1), step)
    return None


MORNING_CUE = re.compile(r"\b(uth|uthna|uthke|alarm|wake|nashta|breakfast|jogging|morning walk)\b", re.I)
SLEEP_HOURS = range(1, 6)  # a bare "3 baje" is not read as 03:00 unless raat/am says so


def is_statement(raw, text):
    """'Sunday hai, ...' / 'शनिवार है' names today; it is not a time reference."""
    return bool(text and re.search(re.escape(raw) + r"[\s,]*(?:\S+\s+)?(?:hai|है|hain)(?=$|[\s,.!?])", text, re.I))


def ground(spans, direction, anchor, text=None):
    """spans: [(label, text)]; direction: 'future'|'past'; anchor: datetime; text: the whole entry (optional,
    used for weekday statements and morning cues). Returns (date_str|None, time_str|None)."""
    sign = -1 if direction == "past" else 1
    by = {}
    for lab, txt in spans:
        by.setdefault(lab, []).append(kinds(txt))
    today = anchor.date()
    day = None; hm = None; dt_override = None; end_day = None; part = None

    for ks in by.get("DAY", []):
        c = next((c for k, c, _ in ks if k == "DAY"), None)
        if c is None: continue
        off = DAY_OFFSET[c]
        if off is None: off = sign * DAY_MAG[c]
        day = today + timedelta(days=off)
        if c == "tonight": part = "raat"

    for ks in by.get("WD", []):
        hit = next(((c, r) for k, c, r in ks if k == "WD"), None)
        if hit is None: continue
        wd, raw = hit
        names = {k for k, _, _ in ks}
        monday = today - timedelta(days=today.weekday())
        if wd == today.weekday() and not names & {"WD_NEXT", "WD_PREV", "WD_NEXT2"} and is_statement(raw, text):
            day = day or today; continue
        if "WD_NEXT2" in names: day = today + timedelta(days=(((wd - today.weekday()) % 7) or 7) + 7)
        elif "WD_NEXT" in names: day = monday + timedelta(days=7 + wd)
        elif "WD_PREV" in names: day = monday + timedelta(days=-7 + wd)
        elif sign > 0: day = today + timedelta(days=((wd - today.weekday()) % 7) or 7)
        else: day = today - timedelta(days=(today.weekday() - wd) % 7)

    for ks in by.get("DATE", []):
        names = {k for k, _, _ in ks}
        pe = next((c for k, c, _ in ks if k == "PERIOD_END"), None)
        if pe:
            if pe == "week": end_day = today + timedelta(days=6 - today.weekday())
            elif pe == "year": end_day = Date(today.year, 12, 31)
            else: end_day = safe_date(*add_months(today, 1), 1, 1) - timedelta(days=1)
            continue
        d = number(ks)
        mo = next((c for k, c, _ in ks if k == "MONTH"), None)
        rel = next((c for k, c, _ in ks if k == "MONTH_REL"), None)
        if d is None or not 1 <= d <= 31: continue
        if mo:
            cand = safe_date(today.year, mo, d, sign)
            if sign > 0 and cand < today: cand = safe_date(today.year + 1, mo, d, 1)
            if sign < 0 and cand > today: cand = safe_date(today.year - 1, mo, d, -1)
        elif rel is not None:
            cand = safe_date(*add_months(today, rel), d, 1)
        elif sign > 0:
            cand = safe_date(*((today.year, today.month) if d >= today.day else add_months(today, 1)), d, 1)
        else:
            cand = safe_date(*((today.year, today.month) if d <= today.day else add_months(today, -1)), d, -1)
        day = cand or day

    for ks in by.get("DUR", []):
        names = {k for k, _, _ in ks}
        n = number(ks)
        if "DEDH" in names: n = 1.5
        elif "DHAI" in names: n = 2.5
        elif "AADHA" in names and n is None: n = 0.5
        if n is None: n = 1
        sgn = -1 if "BEFORE" in names else 1
        if not 0 < n <= 1000: continue
        if "WEEK_UNIT" in names: day = today + timedelta(days=sgn * 7 * int(n))
        elif "DAY_UNIT" in names: day = today + timedelta(days=sgn * int(n))
        elif names & {"HOUR_UNIT", "MIN_UNIT"}:
            mins = n * 60 if "HOUR_UNIT" in names else n
            dt_override = anchor + timedelta(minutes=sgn * mins)

    for ks in by.get("PART", []):
        part = next((c for k, c, _ in ks if k == "PART"), part)
    bare = None
    for ks in by.get("TIME", []):
        h, m, ampm = parse_clock(ks)
        got = to24(h, m, ampm, part)
        if got:
            hm = got
            bare = (h, m) if ampm is None and part is None and h is not None and 1 <= h <= 12 else None
    if hm is None and part:
        hm = PART_DEFAULT[part]

    if dt_override is not None:
        dt_override = dt_override.replace(second=0, microsecond=0)
        return dt_override.date().isoformat(), dt_override.strftime("%H:%M")

    if bare and text and MORNING_CUE.search(text) and bare[0] <= 11:
        hm = (bare[0] % 12, bare[1])
    elif bare and day is None:
        # no day said: the nearest matching clock reading (am or pm), skipping small-hours readings
        cands = []
        for d in (today - timedelta(days=1), today, today + timedelta(days=1)):
            for hh in {bare[0] % 12, bare[0] % 12 + 12}:
                if hh in SLEEP_HOURS: continue
                cands.append(datetime(d.year, d.month, d.day, hh, bare[1]))
        a0 = anchor.replace(second=0, microsecond=0)
        pick = min((c for c in cands if c > a0), default=None) if sign > 0 else \
            max((c for c in cands if c <= a0), default=None)
        if pick:
            return pick.date().isoformat(), pick.strftime("%H:%M")
    if day is not None and hm is not None and part == "raat" and hm[0] < 5:
        day = day + timedelta(days=1)  # "kal raat 2 baje", "aaj raat 12 baje": the night runs past midnight
    if day is None and hm is None and end_day is not None:
        day = end_day

    if day is None and hm is not None:
        t = anchor.replace(hour=hm[0], minute=hm[1], second=0, microsecond=0)
        if sign > 0: day = today if t > anchor else today + timedelta(days=1)
        else: day = today if t <= anchor else today - timedelta(days=1)

    return (day.isoformat() if day else None,
            f"{hm[0]:02d}:{hm[1]:02d}" if hm else None)


def ground_entry(spans, direction, anchor, typ, text=None):
    """Grounding as every system calls it: goals keep a date only for a deadline ("is saal", "end of month")."""
    if not spans: return None, None
    if typ == "goal" and not any(k == "PERIOD_END" for lab, t in spans if lab == "DATE" for k, _, _ in kinds(t)):
        return None, None
    try:
        return ground(spans, direction, anchor, text)
    except Exception:
        return None, None


if __name__ == "__main__":
    a = datetime(2026, 10, 30, 21, 15)  # Friday night
    tests = [
        ([("DAY", "kal"), ("PART", "subah"), ("TIME", "saade 7 baje")], "future", ("2026-10-31", "07:30")),
        ([("DAY", "kal")], "past", ("2026-10-29", None)),
        ([("DAY", "parso"), ("PART", "shaam")], "future", ("2026-11-01", "18:00")),
        ([("WD", "agle somvar")], "future", ("2026-11-02", None)),
        ([("WD", "friday")], "future", ("2026-11-06", None)),
        ([("TIME", "5 baje")], "future", ("2026-10-31", "17:00")),
        ([("DUR", "2 ghante baad")], "future", ("2026-10-30", "23:15")),
        ([("DUR", "dedh ghante mein")], "future", ("2026-10-30", "22:45")),
        ([("DATE", "15 tareekh")], "future", ("2026-11-15", None)),
        ([("DATE", "3 nov"), ("TIME", "4:30 pm")], "future", ("2026-11-03", "16:30")),
        ([("TIME", "paune 9"), ("PART", "raat")], "future", ("2026-10-31", "20:45")),
        ([("DUR", "3 din pehle")], "past", ("2026-10-27", None)),
        ([("DAY", "परसों")], "future", ("2026-11-01", None)),
    ]
    bad = 0
    for sp, d, want in tests:
        got = ground(sp, d, a)
        if got != want: bad += 1; print("FAIL", sp, d, got, want)
    print(f"{len(tests) - bad}/{len(tests)} ok")
