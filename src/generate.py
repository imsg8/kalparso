"""Synthetic Hinglish planner entries with span-level labels.
Gold date/time come from ground.py applied to the gold spans, so labels follow spec.md by construction.
Frames and actions are split into train/held-out pools so test_synth shares no wording with train."""
import json, os, random, sys
from datetime import datetime, timedelta

from lexicon import DAY, WEEKDAY, WD_NEXT, WD_PREV, MONTH, TAREEKH, PART, NUM, BAJE, SAADE, SAVA, PAUNE, DEDH, DHAI
from ground import ground_entry

V2 = True  # v2/v3 phrase families (weeks, next-to-next, deadlines, night hours, weekday statements, clauses); data/v1 and data/v2 are archived snapshots

DEVA = lambda vs: [v for v in vs if any("ऀ" <= ch <= "ॿ" for ch in v)]
LATIN = lambda vs: [v for v in vs if not DEVA([v])]


class G:
    def __init__(self, rng, noisy):
        self.r, self.noisy = rng, noisy

    def sp(self, vs):
        """Pick a spelling: clean form, or a variant / Devanagari form when noisy."""
        lat, dev = LATIN(vs), DEVA(vs)
        if not self.noisy: return lat[0]
        if dev and self.r.random() < 0.06: return self.r.choice(dev)
        return lat[0] if self.r.random() < 0.5 else self.r.choice(lat)

    def hour_word(self, h):
        if self.noisy and h in NUM and self.r.random() < 0.25:
            return self.r.choice(NUM[h] + (["sat"] if h == 7 and V2 else []))
        return str(h)

    # ---- time slots: each returns a list of (text, label|None)
    def day(self, past=False, english=False):
        if english:
            c = self.r.choice(["yesterday", "day before yesterday"] if past else ["today", "tomorrow", "tomorrow", "day after tomorrow"])
        else:
            c = self.r.choice(["kal", "kal", "parso", "aaj"] + (["yesterday"] if past else ["narso", "tomorrow"]))
        return [(self.sp(DAY[c]), "DAY")]

    def wd(self, past=False, english=False):
        i = self.r.randrange(7)
        names = [v for v in LATIN(WEEKDAY[i]) if v.isalpha()]
        en = [n for n in names if n.endswith("day")][0]
        hi = names[0]
        name = en if english else (self.sp([hi] + WEEKDAY[i][1:]) if self.r.random() < 0.6 else en.capitalize())
        mod = self.r.random()
        if past:
            pre = ("last " if english else self.sp(WD_PREV) + " ") if mod < 0.4 else ""
        else:
            pre = ("next " if english else self.sp(WD_NEXT) + " ") if mod < 0.35 else ""
        out = [(pre + name, "WD")]
        if not english and self.r.random() < 0.7: out.append(("ko", None))
        if english: out.insert(0, ("on", None)) if not pre and self.r.random() < 0.6 else None
        return out

    def date(self, english=False):
        d = self.r.randint(1, 28)
        mo = self.r.randint(1, 12)
        mname = self.r.choice(MONTH[mo]).capitalize()
        f = self.r.random()
        if english or f < 0.4: txt = self.r.choice([f"{d} {mname}", f"{mname} {d}", f"{d}th {mname}"])
        elif f < 0.75: txt = f"{d} {self.sp(TAREEKH)}"
        else: txt = f"{d} {mname}"
        out = [(txt, "DATE")]
        if english: out.insert(0, ("on", None))
        if not english and self.r.random() < 0.7: out.append(("ko", None))
        return out

    def part(self, english=False):
        c = self.r.choice(list(PART))
        if english:
            en = {"subah": "morning", "dopahar": "afternoon", "shaam": "evening", "raat": "night"}[c]
            return c, [("at" if c == "raat" else "in the", None), (en, "PART")]
        out = [(self.sp(PART[c]), "PART")]
        if self.r.random() < 0.4: out.append(("ko", None))
        return c, out

    def time(self, part=None, english=False):
        rng = {"subah": (6, 11), "dopahar": (12, 4), "shaam": (4, 8), "raat": (8, 11), None: (1, 12)}[part]
        lo, hi = rng
        h = self.r.choice(list(range(lo, 13)) + list(range(1, hi + 1))) if lo > hi else self.r.randint(lo, hi)
        m = self.r.choice([0, 0, 0, 15, 30, 30, 45, 10, 20, 40, 50])
        if english:
            ap = "am" if (part == "subah" or (part is None and 8 <= h <= 11)) else "pm"
            txt = f"{h}:{m:02d} {ap}" if m else f"{h} {ap}"
            return [("at", None), (txt, "TIME")]
        f = self.r.random()
        if m == 30 and h == 1 and f < 0.5: txt = self.sp(DEDH) + (" " + self.sp(BAJE) if self.r.random() < 0.7 else "")
        elif m == 30 and h == 2 and f < 0.5: txt = self.sp(DHAI) + (" " + self.sp(BAJE) if self.r.random() < 0.7 else "")
        elif m == 30 and f < 0.6: txt = f"{self.sp(SAADE)} {self.hour_word(h)}" + (" " + self.sp(BAJE) if self.r.random() < 0.6 else "")
        elif m == 15 and f < 0.5: txt = f"{self.sp(SAVA)} {self.hour_word(h)}" + (" " + self.sp(BAJE) if self.r.random() < 0.6 else "")
        elif m == 45 and f < 0.5: txt = f"{self.sp(PAUNE)} {self.hour_word(h % 12 + 1)}" + (" " + self.sp(BAJE) if self.r.random() < 0.6 else "")
        elif m == 0: txt = f"{self.hour_word(h)} {self.sp(BAJE)}" if self.r.random() < 0.75 else f"{h} {'am' if part == 'subah' else 'pm'}" if part else f"{self.hour_word(h)} {self.sp(BAJE)}"
        else: txt = f"{h}:{m:02d}" + (" " + self.sp(BAJE) if self.r.random() < 0.3 else "")
        return [(txt, "TIME")]

    def dur(self, past=False, english=False):
        if past:
            n = self.r.randint(2, 6)
            return [(f"{n} days ago" if english else f"{self.hour_word(n)} {self.sp(['din'])} {self.sp(['pehle', 'pahle'])}", "DUR")]
        f = self.r.random()
        if english:
            txt = self.r.choice([f"in {self.r.randint(2, 5)} hours", f"in {self.r.choice([10, 15, 20, 30, 45])} minutes",
                                 "in half an hour", f"in {self.r.randint(2, 10)} days"])
        elif f < 0.3: txt = f"{self.hour_word(self.r.randint(1, 5))} {self.sp(['ghante', 'ghanta', 'ghanton'])} {self.sp(['baad', 'mein'])}"
        elif f < 0.55: txt = f"{self.r.choice([10, 15, 20, 30, 40, 45])} {self.sp(['min', 'minute', 'minat'])} {self.sp(['baad', 'mein'])}"
        elif f < 0.7: txt = f"{self.sp(['aadhe', 'adhe'])} {self.sp(['ghante'])} {self.sp(['mein', 'baad'])}"
        elif f < 0.8: txt = f"{self.sp(DEDH)} {self.sp(['ghante'])} {self.sp(['baad', 'mein'])}"
        else: txt = f"{self.hour_word(self.r.randint(2, 10))} {self.sp(['din'])} {self.sp(['baad'])}"
        return [(txt, "DUR")]

    # ---- v2 phrase families, found in the human dev split
    def wd_name(self, i, english=False):
        names = [v for v in LATIN(WEEKDAY[i]) if v.isalpha()]
        en = [n for n in names if n.endswith("day")][0]
        return en if english else (self.sp([names[0]] + WEEKDAY[i][1:]) if self.r.random() < 0.5 else en.capitalize())

    def v2(self, past, english, anchor):
        r, c = self.r, self.r.choice
        if english:
            k = c(["weeks", "tonight", "noon", "at", "eom"] if not past else ["weeks_ago", "lastweek"])
            if k == "weeks": return [(f"in {r.randint(1, 4)} weeks", "DUR")]
            if k == "tonight": return [("tonight", "DAY"), ("at", None), (str(r.randint(8, 11)), "TIME")]
            if k == "noon": return [(c(["tomorrow", "today"]), "DAY"), ("at", None), ("noon", "TIME")]
            if k == "at": return [("at", None), (str(r.randint(1, 11)), "TIME")]
            if k == "eom": return [("by the", None), (c(["end of the month", "end of this week", "end of the year"]), "DATE")]
            if k == "weeks_ago": return [(f"{r.randint(1, 3)} weeks ago", "DUR")]
            return [("last week", None), ("on", None), (self.wd_name(r.randrange(7), True), "WD")][1:] if False else \
                [("last week " + self.wd_name(r.randrange(7), True), "WD")]
        if past:
            k = c(["kalraat", "kalraat", "weeks_ago", "prevweek", "nko", "today_wd"])
            if k == "kalraat":
                return [(self.sp(DAY["kal"]), "DAY"), (self.sp(PART["raat"]), "PART"),
                        (f"{c([12, 1, 2, 3, 2])} {self.sp(BAJE)}", "TIME"), (c(["tak", "", "ke baad"]), None)]
            if k == "weeks_ago": return [(f"{self.hour_word(r.randint(1, 3))} {c(['hafte', 'hafta'])} {c(['pehle', 'pahle'])}", "DUR")]
            if k == "prevweek": return [(f"{c(['pichle hafte', 'last week'])} {self.wd_name(r.randrange(7))}", "WD"), ("ko", None)]
            if k == "nko": return [(str(r.randint(13, 28)), "DATE"), ("ko", None)]
            return [(self.wd_name(anchor.weekday()), "WD"), ("ko", None)]
        k = c(["weeks", "weeks", "next2", "nextweek", "eom", "eom", "monthrel", "nko", "raat12", "statement", "statement",
               "bare", "bare", "tareekh_today"])
        if k == "weeks": return [(f"{self.hour_word(r.randint(1, 4))} {c(['hafte', 'hafta', 'week'])} {c(['baad', 'mein'])}", "DUR")]
        if k == "next2": return [(f"{c(['next to next', 'agle ke agle'])} {self.wd_name(r.randrange(7))}", "WD"), ("ko", None)]
        if k == "nextweek": return [(f"{c(['next week ke', 'next week', 'agle hafte'])} {self.wd_name(r.randrange(7))}", "WD")]
        if k == "eom":
            return [(c(["end of month", "is mahine ke end", "month end", "end of this week", "hafte ke end"]), "DATE"), ("tak", None)]
        if k == "monthrel":
            return [(f"{c(['agle mahine', 'next month'])} {r.randint(1, 28)}" + c([" tareekh", ""]), "DATE"), ("ko", None)]
        if k == "nko":
            out = [(str(r.randint(13, 28)), "DATE"), (c(["ko", "ki"]), None)]
            if r.random() < 0.4: out += [(self.sp(PART["raat"]), "PART"), (f"{r.randint(8, 11)} {self.sp(BAJE)}", "TIME")]
            return out
        if k == "raat12":
            return ([(self.sp(DAY["aaj"]), "DAY")] if r.random() < 0.6 else []) + \
                [(self.sp(PART["raat"]), "PART"), (f"12 {self.sp(BAJE)}", "TIME"), (c(["se pehle", "", "tak"]), None)]
        if k == "statement":
            st = [(self.wd_name(anchor.weekday()), "WD"), (c(["hai", "hai,", "है"]), None)]
            if r.random() < 0.4: st.insert(0, (self.sp(DAY["aaj"]), "DAY"))
            nxt = c([[(f"{self.hour_word(r.randint(1, 11))} {self.sp(BAJE)}", "TIME")],
                     [(self.sp(PART["shaam"]), "PART"), (f"{r.randint(5, 8)} {self.sp(BAJE)}", "TIME")],
                     [(self.sp(DAY["kal"]), "DAY")]])
            return st + nxt
        if k == "tareekh_today": return [(f"{anchor.day} {self.sp(TAREEKH)}", "DATE"), ("ko", None)]
        h = r.randint(1, 12)
        return [(c([f"{self.hour_word(h)} {self.sp(BAJE)}", f"{c(['saade', 'sava'])} {h}", f"{h}:{c(['05', '15', '30'])}"]), "TIME")]

    def when(self, past=False, english=False):
        """Compose a time phrase from the combos in spec.md."""
        r = self.r.random
        combos = (["day", "day_part", "wd", "dur", "day_time"] if past
                  else ["day", "day_part", "day_part_time", "day_time", "wd", "wd_part", "wd_time", "date", "date_time",
                        "time", "part", "part_time", "dur", "dur"])
        c = self.r.choice(combos)
        segs, part = [], None
        head = c.split("_")[0]
        if head == "day": segs += self.day(past, english)
        elif head == "wd": segs += self.wd(past, english)
        elif head == "date": segs += self.date(english)
        elif head == "dur": return self.dur(past, english)
        if "part" in c:
            part, ps = self.part(english)
            segs += ps
        if c.endswith("time"):
            segs += self.time(part, english)
        return segs


# ---------- content pools (train | held-out) ----------
ACT_HI = ["gym jaana", "Maama ko call karna", "dentist ka appointment", "electricity bill pay karna", "doodh lana",
          "Rahul ko 500 rupaye wapas karne", "laundry uthani", "car service karwani", "medicine leni", "flight ka check-in karna",
          "report submit karni", "client ke saath call", "haircut karwana", "passport office jaana", "rent transfer karna",
          "Simar ko birthday wish karna", "Ankit ke saath meeting", "Prags ko airport se pick karna", "groceries order karni",
          "gas cylinder book karna", "doctor se milna", "assignment submit karna", "standup call", "interview ki taiyari",
          "yoga class", "PG ka rent dena", "match dekhna", "movie ki tickets book karni", "AC repair wale ko bulana",
          "2 kg aata lana", "plants ko paani dena", "Kunal ko file bhejni", "bank jaana", "train ki ticket book karni",
          "dawai ka order", "presentation banana", "mail ka reply karna", "cake order karna", "Rahul ka birthday hai",
          "Nani se baat karni", "shoes return karne", "insurance renew karna", "tax ke documents bhejne", "bike ki service"]
ACT_HI_TEST = ["salon ki booking", "Ankit ko 2000 bhejne", "cylinder change karna", "pharmacy se dawai lani",
               "visa ke documents print karne", "Mausi ko call karna", "electrician ko bulana", "keys duplicate karwani",
               "Prags ke saath dinner", "mobile recharge karna"]
ACT_EN = ["call the bank", "pay the credit card bill", "go to the gym", "pick up the laundry", "book the cab",
          "submit the report", "call Maama", "buy groceries", "renew the car insurance", "send the invoice",
          "water the plants", "book train tickets", "take my medicine", "reply to the client", "join the standup",
          "pay the rent", "order the cake", "prepare for the interview", "return the shoes", "call Simar"]
ACT_EN_TEST = ["file the expense report", "call the plumber", "pick up Prags", "pay the maid", "book a doctor visit"]

PAST_HI = ["Rahul se baat hui, project ka scope badh gaya", "gym gaya tha, leg day kiya", "Maama ke ghar dinner kiya",
           "naya cafe try kiya, coffee achi thi", "interview diya, theek gaya", "kharcha zyada ho gaya tha",
           "Ankit ne bola deadline shift hogi", "app ka ek idea aaya tha", "client ne payment kar di thi",
           "Simar se video call hui", "match dekha, India jeet gaya", "doctor ne bola vitamin D kam hai",
           "Prags ke saath movie dekhi", "landlord se rent ki baat hui", "server down ho gaya tha",
           "naya laptop order kiya", "5 km run kiya", "Kunal ke saath lunch kiya", "bike ka tyre puncture hua",
           "presentation achi gayi"]
PAST_HI_TEST = ["meeting cancel ho gayi thi", "Nani se mila", "neend achi nahi aayi", "naya phone mila"]
PAST_EN = ["met Rahul for coffee", "went to the dentist", "had a long call with Simar", "finished the report",
           "paid the electricity bill", "watched the match with Prags", "ran 5 km"]
PAST_EN_TEST = ["missed the standup", "cooked dinner at home"]

NOTE = ["wifi password router ke peeche likha hai", "Prags ko sushi pasand hai", "book recommendation Atomic Habits",
        "app idea: expense split for flatmates", "Maama ka address Sector 21 hai",
        "car ki insurance policy number glovebox mein hai", "best biryani wali jagah Jama Masjid ke paas",
        "the spare key is with the guard", "idea: dark mode for the journal", "Kunal prefers mornings for calls",
        "AC ka filter har mahine saaf karna padta hai", "gym ka locker number 42 hai"]
NOTE_TEST = ["Simar ka size medium hai", "the router admin page is 192.168.1.1", "chai patti Assam wali achi lagti hai"]

GOAL = ["life mein ek baar Japan jaana hai", "is saal 10 kg kam karna", "apna startup shuru karna", "guitar seekhna hai",
        "ek marathon daudna hai", "parents ke liye ghar khareedna", "French seekhni hai", "har roz journal likhna",
        "become a better listener", "save enough to travel for a year", "100 books padhni hain", "fluent Spanish bolni hai",
        "apni khud ki app launch karni hai", "learn to swim"]
GOAL_TEST = ["Ladakh bike pe jaana hai", "run a half marathon someday", "khud ka studio banana hai"]

FRAME_R = ["{W} {A}", "{A} {W}", "{W} {A} yaad dilana", "yaad dilana {W} {A}", "{W} {A} hai", "{A}, {W}",
           "{W} yaad dila dena ki {A} hai", "please {W} {A}", "{W} mujhe {A} yaad dilana", "{W} {A} karna hai yaar"]
FRAME_R_TEST = ["{A} hai {W}, bhoolna mat", "{W} ke liye reminder: {A}", "yaar {W} {A} mat bhoolna"]
FRAME_RE = ["remind me {W} to {E}", "remind me to {E} {W}", "{E} {W}"]
FRAME_RE_TEST = ["don't forget to {E} {W}"]
FRAME_P = ["{W} {P}", "{P} {W}", "{W} {P} yaar"]
FRAME_P_TEST = ["btw {W} {P}"]
FRAME_PE = ["{W} I {P}", "{P} {W}"]
FRAME_N = ["{N}", "note: {N}", "{N} note kar lo"]
FRAME_N_TEST = ["yaad rakhne ke liye: {N}"]
FRAME_G = ["{G}", "goal: {G}", "life goal: {G}", "mera goal hai {G}"]
FRAME_G_TEST = ["zindagi mein {G}"]
FILLERS = ["um", "matlab", "achha", "okay so", "haan", "yaar", "so"]


def fill(frame, slots):
    """frame with {W}/{A}/... -> list of segments."""
    segs, i = [], 0
    import re
    for m in re.finditer(r"\{(\w)\}", frame):
        if frame[i:m.start()].strip(): segs.append((frame[i:m.start()].strip(), None))
        v = slots[m.group(1)]
        segs += v if isinstance(v, list) else [(v, None)]
        i = m.end()
    if frame[i:].strip(): segs.append((frame[i:].strip(), None))
    return segs


# v3: compositional clauses (train pool only), so the tense head learns verb forms instead of memorising phrases
OBJ = ["Rahul se", "Maama ke saath", "doctor ke paas", "office", "bank", "market", "Simar ke ghar", "gym", "mall",
       "Ankit ko", "landlord se", "client ke saath", "bhaiya ko", "Nani ke yahan", "college", "airport", "station",
       "PG wale ko", "boss se", "dentist ke paas", "team ke saath", "Papa ko", "Mummy ke saath", "cousins ke saath"]
THING = ["meeting", "call", "payment", "order", "booking", "report", "movie", "match", "party", "class", "interview",
         "parcel", "bill", "form", "exam", "presentation", "dinner", "lunch", "trip", "appointment", "delivery", "EMI"]
V_PAST = ["gaya tha", "gayi thi", "gaye the", "gaya", "mila", "mili thi", "mile the", "baat hui", "baat hui thi",
          "jhagda hua", "milna hua"]
T_PAST = ["ho gayi thi", "ho gaya", "cancel ho gayi", "kar di thi", "kiya tha", "kar liya", "miss ho gayi", "khatam hui",
          "aa gaya tha", "mil gaya", "bhej diya tha", "pay kar diya", "book kiya tha", "reh gayi thi", "late ho gayi thi",
          "achi gayi", "postpone ho gayi thi", "dekhi thi", "attend ki thi", "submit kiya"]
V_FUT = ["jaana hai", "jaana", "milna hai", "baat karni hai", "jaana padega", "chalna hai", "milenge", "jaunga",
         "jaungi", "pahunchna hai", "nikalna hai"]
T_FUT = ["hai", "karni hai", "karna hai", "book karni hai", "pay karna", "bhejna hai", "submit karna hai", "cancel karni hai",
         "reschedule karni hai", "attend karni hai", "dekhni hai", "confirm karni hai", "hogi", "hoga", "shuru hogi",
         "check karna", "yaad se karna"]


def clause(rng, past):
    if rng.random() < 0.5:
        return f"{rng.choice(OBJ)} {rng.choice(V_PAST if past else V_FUT)}"
    return f"{rng.choice(THING)} {rng.choice(T_PAST if past else T_FUT)}"


MORNING_ACT = ["uthna hai", "alarm laga dena", "uthke gym jaana", "breakfast pe Papa se baat"]
GOAL_V2 = ["is saal 20 kg deadlift badhana hai", "is saal 3 naye shehar ghoomne hai", "is saal ka target 5 lakh bachana",
           "end of the year tak French seekhni hai"]


def make(rng, held_out):
    noisy = rng.random() < 0.5
    g = G(rng, noisy)
    anchor = datetime(2026, 1, 1, 0) + timedelta(days=rng.randrange(730), minutes=rng.randrange(24 * 60))
    when = lambda past=False, english=False: g.v2(past, english, anchor) if V2 and rng.random() < 0.25 \
        else g.when(past, english)
    pick = lambda tr, te: rng.choice(te if held_out else tr)
    u = rng.random()
    english = False
    if u < 0.50:
        typ, direction = "reminder", "future"
        if rng.random() < 0.2:
            english = True
            segs = fill(pick(FRAME_RE, FRAME_RE_TEST), {"W": when(False, True), "E": pick(ACT_EN, ACT_EN_TEST)})
        elif V2 and rng.random() < 0.06:
            h = rng.randint(5, 8)
            segs = fill(rng.choice(["{W} {A}", "{A} {W}"]), {"W": [(f"{g.hour_word(h)} {g.sp(BAJE)}", "TIME")] if rng.random() < 0.5
                        else [(g.sp(DAY["kal"]), "DAY"), (f"{g.hour_word(h)} {g.sp(BAJE)}", "TIME")], "A": rng.choice(MORNING_ACT)})
        else:
            act = clause(rng, False) if V2 and not held_out and rng.random() < 0.5 else pick(ACT_HI, ACT_HI_TEST)
            segs = fill(pick(FRAME_R, FRAME_R_TEST), {"W": when(), "A": act})
    elif u < 0.72:
        typ, direction = "note", "past"
        if rng.random() < 0.2:
            english = True
            segs = fill(rng.choice(FRAME_PE), {"W": when(True, True), "P": pick(PAST_EN, PAST_EN_TEST)})
        else:
            pp = clause(rng, True) if V2 and not held_out and rng.random() < 0.6 else pick(PAST_HI, PAST_HI_TEST)
            segs = fill(pick(FRAME_P, FRAME_P_TEST), {"W": when(True), "P": pp})
    elif u < 0.86:
        typ, direction = "note", "future"
        segs = fill(pick(FRAME_N, FRAME_N_TEST), {"N": pick(NOTE, NOTE_TEST)})
    else:
        typ, direction = "goal", "future"
        if V2 and rng.random() < 0.25:
            gl = rng.choice(GOAL_V2); cut = "end of the year" if gl.startswith("end") else "is saal"
            segs = [(cut, "DATE"), (gl[len(cut) + 1:], None)]
        else:
            segs = fill(pick(FRAME_G, FRAME_G_TEST), {"G": pick(GOAL, GOAL_TEST)})

    if noisy and rng.random() < 0.3:
        segs.insert(0 if rng.random() < 0.7 else rng.randrange(len(segs) + 1), (rng.choice(FILLERS), None))
    # surface noise is applied per segment, before offsets, so spans stay aligned
    if noisy:
        lower, nocomma = rng.random() < 0.4, rng.random() < 0.3
        segs = [((t.lower() if lower else t).replace(",", "") if nocomma else (t.lower() if lower else t), lab)
                for t, lab in segs]
    else:
        segs[0] = (segs[0][0][0].upper() + segs[0][0][1:], segs[0][1])
    segs = [(t, lab) for t, lab in segs if t]
    text, spans = "", []
    for t, lab in segs:
        if text and not t.startswith((",", ":")): text += " "
        s = len(text); text += t
        if lab: spans.append({"start": s, "end": len(text), "label": lab})
    if not noisy and rng.random() < 0.5: text += "."
    gold_spans = [(s["label"], text[s["start"]:s["end"]]) for s in spans]
    d, t = ground_entry(gold_spans, direction, anchor, typ, text)
    if spans and d is None and typ != "goal": return None
    if d and typ != "goal":  # a reminder must point forward and a past note backward
        when = datetime.fromisoformat(f"{d}T{t or ('23:59' if direction == 'future' else '00:00')}")
        if (direction == "future") != (when >= anchor.replace(second=0)):
            return None
    low = text.lower()
    amb = any(s["label"] == "DAY" and any(w in low[s["start"]:s["end"]] for w in ("kal", "kl", "pars", "nars", "कल", "परसों", "नरसों"))
              for s in spans) or any(s["label"] == "WD" and not any(m in low[s["start"]:s["end"]] for m in ("agl", "next", "pich", "last", "aane"))
                                     for s in spans)
    return {"text": text, "anchor": anchor.strftime("%Y-%m-%dT%H:%M"), "weekday": anchor.strftime("%A"),
            "type": typ, "direction": direction, "date": d, "time": t, "spans": spans,
            "flags": {"noisy": noisy, "english": english, "ambiguous": bool(amb)}}


def main(out_dir, n_train=30000, n_dev=2000, n_test=2000, seed=13):
    os.makedirs(out_dir, exist_ok=True)
    rng = random.Random(seed)
    seen = set()
    for name, n, held in [("train", n_train, False), ("dev", n_dev, False), ("test_synth", n_test, True)]:
        with open(f"{out_dir}/{name}.jsonl", "w") as f:
            k = 0
            while k < n:
                ex = make(rng, held)
                if ex is None: continue
                key = (ex["text"].lower(), ex["anchor"])
                if key in seen: continue
                seen.add(key); k += 1
                ex["id"] = f"{name}-{k:05d}"
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
        print(name, n)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../data")
