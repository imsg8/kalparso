"""Shared vocabulary: canonical forms and the informal spelling variants of each."""

# canonical -> variants (first variant is the clean spelling)
DAY = {
    "aaj": ["aaj", "aj", "aaj", "आज"],
    "kal": ["kal", "kal", "kl", "kall", "कल"],
    "parso": ["parso", "parson", "parsoon", "parsu", "parsho", "परसों"],
    "narso": ["narso", "narson", "narsoon", "नरसों"],
    "today": ["today"],
    "tomorrow": ["tomorrow", "tmrw", "tomorow"],
    "yesterday": ["yesterday"],
    "day after tomorrow": ["day after tomorrow", "day after"],
    "day before yesterday": ["day before yesterday"],
    "tonight": ["tonight"],
}
# offset in days; None = ambiguous, sign comes from direction
DAY_OFFSET = {"aaj": 0, "today": 0, "kal": None, "parso": None, "narso": None,
              "tomorrow": 1, "yesterday": -1, "day after tomorrow": 2, "day before yesterday": -2, "tonight": 0}
DAY_MAG = {"kal": 1, "parso": 2, "narso": 3}

WEEKDAY = {  # index 0 = Monday
    0: ["somvar", "somvaar", "sombar", "monday", "mon", "सोमवार"],
    1: ["mangalvar", "mangalwar", "mangal", "tuesday", "tues", "मंगलवार"],
    2: ["budhvar", "budhwar", "budh", "wednesday", "wed", "बुधवार"],
    3: ["guruvar", "guruwar", "veervar", "brihaspativar", "thursday", "thurs", "गुरुवार"],
    4: ["shukravar", "shukrawar", "shukra", "friday", "fri", "शुक्रवार"],
    5: ["shanivar", "shaniwar", "shani", "saturday", "sat", "शनिवार"],
    6: ["ravivar", "raviwar", "itvaar", "itwar", "sunday", "sun", "रविवार"],
}
WD_NEXT = ["agle", "agli", "next", "aane wale", "अगले", "next week", "next week ke", "agle hafte", "agle week"]
WD_PREV = ["pichle", "pichhle", "last", "पिछले", "pichle hafte", "last week", "pichle week"]
WD_NEXT2 = ["next to next", "agle ke agle", "next ke next"]  # the occurrence after the coming one
WD_THIS = ["is", "this", "iss"]

MONTH = {
    1: ["january", "jan"], 2: ["february", "feb"], 3: ["march", "mar"], 4: ["april", "apr"],
    5: ["may"], 6: ["june", "jun"], 7: ["july", "jul"], 8: ["august", "aug"],
    9: ["september", "sept", "sep"], 10: ["october", "oct"], 11: ["november", "nov"], 12: ["december", "dec"],
}
MONTH_REL = {1: ["agle mahine", "next month", "agle month", "aane wale mahine"],
             0: ["is mahine", "iss mahine", "this month"]}
# deadlines: the last day of the period
PERIOD_END = {"month": ["end of month", "end of the month", "month end", "mahine ke end", "is mahine ke end",
                        "iss mahine ke end", "mahine ke aakhir", "month ke end", "end of this month"],
              "week": ["end of this week", "end of the week", "end of week", "hafte ke end", "is hafte ke end"],
              "year": ["is saal", "iss saal", "this year", "saal ke end", "end of the year", "end of year", "year end"]}
TAREEKH = ["tareekh", "tarikh", "tareek", "taarikh", "date"]

PART = {
    "subah": ["subah", "subha", "suba", "subeh", "morning", "सुबह"],
    "dopahar": ["dopahar", "dopehar", "dupahar", "dophar", "afternoon", "दोपहर"],
    "shaam": ["shaam", "sham", "shyam", "shaam", "evening", "शाम"],
    "raat": ["raat", "rat", "raat", "night", "रात"],
}
PART_DEFAULT = {"subah": (9, 0), "dopahar": (13, 0), "shaam": (18, 0), "raat": (21, 0)}

NUM = {  # Hindi and English number words
    1: ["ek", "one"], 2: ["do", "two"], 3: ["teen", "three"], 4: ["char", "chaar", "four"],
    5: ["paanch", "panch", "five"], 6: ["chhe", "che", "chheh", "six"], 7: ["saat", "seven"],
    8: ["aath", "aat", "eight"], 9: ["nau", "nine"], 10: ["das", "dus", "ten"],
    11: ["gyarah", "gyara", "eleven"], 12: ["barah", "bara", "twelve"],
    14: ["fourteen"], 15: ["pandrah", "fifteen"], 20: ["bees", "twenty"], 30: ["tees", "thirty"],
    45: ["paintalis", "forty five"],
}
BAJE = ["baje", "baje", "bje", "bajey", "baaje", "o'clock", "बजे"]
SAADE = ["saade", "saadhe", "sade", "saadey"]
SAVA = ["sava", "sawa", "savaa"]
PAUNE = ["paune", "pone", "pauney"]
DEDH = ["dedh", "dhedh", "derh"]
DHAI = ["dhai", "dhaai", "dhaayi", "adhai"]
AADHA = ["aadha", "aadhe", "adha", "adhe", "half an", "half"]

HOUR_UNIT = ["ghante", "ghanta", "ghanton", "hours", "hour", "hrs", "hr"]
MIN_UNIT = ["minute", "minutes", "min", "mins", "minat"]
DAY_UNIT = ["din", "days", "day"]
WEEK_UNIT = ["hafte", "hafta", "hafton", "week", "weeks", "wk"]
AFTER = ["baad", "mein", "me", "in", "later", "बाद"]
BEFORE = ["pehle", "pahle", "ago", "पहले"]

PAST_MARKERS = ["tha", "thi", "bola", "boli", "ran", "kiya", "kiye", "ki thi", "gaya", "gayi", "gaye", "hua", "hui", "hue",
                "diya", "di thi", "aaya", "aayi", "mila", "mili", "dekha", "dekhi", "khaya", "liya", "li thi",
                "was", "were", "went", "did", "met", "had", "called", "ago", "pehle", "yesterday"]


def build_index():
    """variant (lowercased) -> (kind, canonical)."""
    idx = {}
    def add(kind, canon, vs):
        for v in vs:
            idx.setdefault(v.lower(), (kind, canon))
    for c, vs in DAY.items(): add("DAY", c, vs)
    for c, vs in WEEKDAY.items(): add("WD", c, vs)
    for c, vs in MONTH.items(): add("MONTH", c, vs)
    for c, vs in PART.items(): add("PART", c, vs)
    for c, vs in NUM.items(): add("NUM", c, vs)
    for c, vs in MONTH_REL.items(): add("MONTH_REL", c, vs)
    for c, vs in PERIOD_END.items(): add("PERIOD_END", c, vs)
    for kind, vs in [("BAJE", BAJE), ("SAADE", SAADE), ("SAVA", SAVA), ("PAUNE", PAUNE), ("DEDH", DEDH),
                     ("DHAI", DHAI), ("AADHA", AADHA), ("HOUR_UNIT", HOUR_UNIT), ("MIN_UNIT", MIN_UNIT),
                     ("DAY_UNIT", DAY_UNIT), ("WEEK_UNIT", WEEK_UNIT), ("WD_NEXT2", WD_NEXT2), ("AFTER", AFTER), ("BEFORE", BEFORE), ("WD_NEXT", WD_NEXT),
                     ("WD_PREV", WD_PREV), ("WD_THIS", WD_THIS), ("TAREEKH", TAREEKH)]:
        add(kind, kind, vs)
    return idx


INDEX = build_index()
