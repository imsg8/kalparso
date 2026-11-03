# Label spec: Hinglish planner capture (v0.1, 30 Oct 2026)

Task: given one planner entry (Roman Hinglish, English, sometimes a Devanagari word) and the moment it was written (the *anchor*), output:

| Field | Values |
|---|---|
| `type` | `reminder` (something to be told about later), `note` (an observation, fact or past event), `goal` (a long-term aim with no date) |
| `date` | `YYYY-MM-DD` or `null` |
| `time` | `HH:MM` (24 h) or `null` |

## Intermediate representation (IR)

Every system may predict the final date/time directly, or predict the IR and let the shared grounder (`src/ground.py`) compute it.

- **Spans**, each with a label:
  - `DAY`: aaj, kal, parso, narso, today, tomorrow, yesterday, day after tomorrow
  - `WD`: a weekday, with an optional modifier (agle/next, pichle/last, is/this)
  - `DATE`: a day of the month, with an optional month (15 tareekh, 15 Nov)
  - `TIME`: a clock time (5 baje, saade 5, 5:30 pm, paune 9)
  - `PART`: a part of the day (subah, dopahar, shaam, raat)
  - `DUR`: an offset from now (2 ghante baad, in 20 min, 3 din baad, 2 din pehle)
- **Direction**: `future` or `past`. This is what settles the ambiguous words: kal = +1 or -1, parso = +2 or -2, narso = +3 or -3, and bare weekdays.

## Grounding conventions (all systems are told these)

1. **Direction.** With no tense marker, the entry is read as future (it is a planner).
2. **Weekdays.** A bare weekday means the next one after today (1 to 7 days ahead), or the last one before today if the direction is past. "agle X" means X in next calendar week (weeks start on Monday). "pichle X" means X in the previous calendar week.
3. **Day of month.** "15 tareekh" means the next 15th after today (the previous one if past). "15 Nov" means the next 15 Nov.
4. **Parts of the day with no clock time.** subah 09:00, dopahar 13:00, shaam 18:00, raat 21:00.
5. **Clock hours.**
   - With am/pm, use that.
   - subah h: h am. dopahar h: pm for h up to 6. shaam h: pm. raat h: pm for 7 to 11.
   - A bare hour: 1 to 7 means pm, 8 to 11 means am, 12 means noon.
6. **Hindi fractions.** saade h = h:30, sava h = h:15, paune h = (h-1):45, dedh = 1:30, dhai = 2:30.
7. **A time with no day.** In the future direction it is today, or tomorrow if that time has already passed. In the past direction it is today, or yesterday if that time is still to come.
8. **Offsets.** "N ghante/min baad", "in N hours" means anchor + N, so it sets both date and time. "N din baad" or "N din pehle" sets the date only.
9. **Goals have no date or time.** Notes with no time words have no date or time.

## Metrics

- Type accuracy and macro-F1.
- Date exact match and time exact match (`null` must match `null`).
- **Full match:** type, date and time all correct.
- Reported separately for: the ambiguous subset (kal/parso/narso/bare weekday), the noisy subset (spelling variants), and English-only entries.
- Latency per entry on the i7-9700 (median and 95th percentile; cold and warm).

## Data splits

- `train` / `dev`: synthetic, generated from template families A.
- `test_synth`: synthetic, from **held-out** template families and held-out actions (no overlap in wording).
- `test_human`: typed by one person (the first author), part of it paraphrased from real planning messages, and labelled by the same author. **This is the headline test set.**
