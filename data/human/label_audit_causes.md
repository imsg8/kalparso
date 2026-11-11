# Label audit, cause per row

The 78 rows are the in-scope Human-Calib + Human-Test entries on which three systems agree with each other but not with the gold:
Rules v2, and MuRIL and XLM-R trained on v1 data with the v2 grounder (results/human/rules_v2.jsonl, A_muril_fp32_g2.jsonl, A_xlmr_fp32_g2.jsonl),
scored with src/eval_human.py (either late-night reading accepted). Recomputing that rule from those three files gives exactly these 78 ids.
No gold answer was changed. Causes (i) to (vi), numbered as in the paper's error analysis, are system errors (69 rows); the three gold-check causes are debatable gold answers (9 rows).
Two rows first filed as misspellings (sat for saat) are gold checks: every system read sat as 7, and the disagreement is am/pm.

## Counts

| cause | rows |
|---|---|
| (i) agle/next/pichle X: the gold means the coming (or most recent) X, the convention says calendar week | 8 |
| (ii) Two clauses with different times or tenses; the gold takes the date of the clause with the main event | 23 |
| (iii) Habitual, relative or festival phrase outside the span labels (har, roz/daily from, jab uthu, Diwali/Christmas/Holi, ek mahine baad, kal ke baad wala din) | 16 |
| (iv) Clock reading resolved by world knowledge (dinner at 8 = 20:00, flight/leave at 7 = 07:00, sleep at 1 = 01:00, fireworks) | 9 |
| (v) Month-name and period phrases (January ke end tak, end of next week, next month ki 10, October mein 17 tareekh) | 7 |
| (vi) Other system errors: past tense missed, late-night aaj, Devanagari weekday statement, 58 minute read as a clock | 6 |
| Gold check: weekday that names today resolved to today, against the bare-weekday rule | 2 |
| Gold check: bare hour 1-7 set to the morning with no morning cue, against the hour rule | 2 |
| Gold check: part-of-day default dropped or added, or past event left undated | 5 |
| total | 78 |

## Rows

| id | cause | entry | gold | systems | why |
|---|---|---|---|---|---|
| human-0023 | iii | sava 10 baje subah bank jaana hai Saturday ko half day hota hai | 2026-10-31 10:15 | 2026-11-07 10:15 | Saturday ko half day hota hai: habitual fact |
| human-0040 | iii | Diwali se pehle ghar ki safai karwani hai | 2026-11-08 None | None None | Diwali 2026-11-08 |
| human-0080 | ii | 2 din pehle Vicky se 2000 liye the Friday ko lauta dunga | 2026-11-06 None | 2026-10-31 None | borrowed 2026-10-31 |
| human-0081 | iii | Diwali pe ghar jaana hai ticket check karo | 2026-11-08 None | None None | Diwali; ticket check undated |
| human-0086 | ii | pichle Monday ko jo laptop repair diya tha woh aaj 4 baje ready hoga | 2026-11-02 16:00 | 2026-10-26 16:00 | given for repair 2026-10-26 |
| human-0087 | iii | har Monday subah 9 baje team sync hota hai yaad dilate rehna | 2026-11-02 09:00 | 2026-11-09 09:00 | recurring every Monday 09:00 |
| human-0097 | ii | kal Sunday ko jo meeting thi woh cancel ho gayi thi aaj 4 baje reschedule karni hai | 2026-11-02 16:00 | 2026-11-01 16:00 | meeting was 2026-11-01 |
| human-0116 | ii | pichle hafte Thursday ko RTO gaya tha licence ke liye, 2 hafte mein aayega | 2026-10-29 None | 2026-11-17 None | licence expected ~2026-11-12 |
| human-0154 | ii | kal subah 7 baje uthna hai standup 9:30 pe hai | 2026-11-05 07:00 | 2026-11-05 09:30 | standup 2026-11-05 09:30 |
| human-0161 | gold-other | kal dopahar ko meeting thi woh mujhe miss ho gayi | 2026-11-03 None | 2026-11-03 13:00 | kal dopahar ... thi: gold has no time; convention gives dopahar 13:00 |
| human-0171 | iii | jab uthu toh sabse pehle paani ki bottle bharni hai | 2026-11-05 09:00 | None None | on waking |
| human-0190 | vi | kal raat 3 baje tak padha tha aaj jaldi so raha hu | 2026-11-04 03:00 | 2026-11-05 03:00 | kal raat ... padha tha: past tense missed, read as tomorrow night |
| human-0197 | iii | next week se daily shaam 6 baje walk | 2026-11-09 18:00 | 2026-11-05 18:00 | daily from |
| human-0219 | gold-weekday | dentist on Thursday morning | 2026-11-05 09:00 | 2026-11-12 09:00 | Thursday at Thu 06:30: gold today, convention says next Thursday |
| human-0230 | iii | aaj se ek mahine baad lease khatam ho rahi hai naya ghar dhoondhna hai | 2026-12-05 None | 2026-11-05 None |  |
| human-0233 | ii | kal hi to bola tha Raj ne ki Sunday ko aayega | 2026-11-08 None | 2026-11-01 None | said 2026-11-04 |
| human-0237 | v | end of next week tak appraisal form bharna | 2026-11-15 None | None None | alt 2026-11-13 (Fri) |
| human-0240 | v | next month ki 10 tareekh ko school reunion | 2026-12-10 None | 2026-11-10 None |  |
| human-0253 | ii | kal raat jo khana bacha tha woh fridge mein hai aaj lunch mein le jaana | 2026-11-05 13:00 | 2026-11-05 21:00 |  |
| human-0273 | vi | Wednesday ko office mein Kunal ko 500 diye the | 2026-11-04 None | 2026-11-11 None | diye the (past) read as future |
| human-0275 | ii | pichle Sunday plants mein khaad daali thi agli baar 2 hafte baad | 2026-11-01 None | 2026-11-20 None | next ~2026-11-15 |
| human-0288 | ii | abhi kuch der pehle Ma ka call aaya tha 9 baje wapas call karna | 2026-11-06 21:00 | 2026-11-06 09:00 |  |
| human-0298 | ii | 10 baje tak Vikram ko kal ke liye confirm karna | 2026-11-06 22:00 | 2026-11-07 10:00 |  |
| human-0319 | vi | kal raat 2 baje tak cards khele the | 2026-11-08 02:00 | 2026-11-10 02:00 | khele the (past) read as future |
| human-0331 | ii | 3 din baad office wapas, nahi nahi kal se office hai | 2026-11-09 None | 2026-11-11 None | self-correction |
| human-0336 | iv | raat 1 baje tak pataakhe chalenge earplugs nikaal ke rakhna | 2026-11-08 21:00 | 2026-11-09 01:00 |  |
| human-0337 | iii | next month Christmas pe Goa | 2026-12-25 None | None None |  |
| human-0354 | ii | कल रात 12 बजे दीदी को फोन किया था, आज दोपहर में फिर करना | 2026-11-08 13:00 | 2026-11-08 12:00 | past call 2026-11-08 00:00 |
| human-0366 | iii | next month Christmas ke liye Goa ki tickets | 2026-12-25 None | None None | booking task undated |
| human-0368 | ii | 31 December ki party kaha karni hai Friday tak decide karna | 2026-12-04 None | 2026-12-31 None |  |
| human-0369 | gold-other | is mahine ke end tak report bhejni thi, aaj hi bhejni hai | 2026-11-30 21:00 | 2026-11-30 None | gold time 21:00 with no time word in the entry |
| human-0377 | iv | Saturday ko Skandagiri trek, raat 3 baje nikalna hai | 2026-12-05 03:00 | 2026-12-06 03:00 |  |
| human-0387 | i | book dentist for next friday morning | 2026-12-04 09:00 | 2026-12-11 09:00 | alt 2026-12-11 |
| human-0404 | i | agle Friday bijli ka bill bharna hai | 2026-12-04 None | 2026-12-11 None |  |
| human-0410 | vi | aaj shaam ko Rahul se mila tha | 2026-11-30 18:00 | 2026-12-01 18:00 | aaj at 00:10 means Monday |
| human-0411 | ii | abhi 10 minute pehle Ma ka message aaya subah reply karna | 2026-12-01 09:00 | 2026-12-01 00:00 | msg 2026-12-01 00:00 |
| human-0416 | iv | 1 baje tak so jaana hai | 2026-12-01 01:00 | 2026-12-01 13:00 |  |
| human-0422 | iii | Christmas pe Goa | 2026-12-25 None | None None |  |
| human-0424 | i | agle Friday bijli ka bill bharna hai | 2026-12-04 None | 2026-12-11 None |  |
| human-0432 | i | next Sunday morning 7 baje cycling | 2026-12-06 07:00 | 2026-12-13 07:00 |  |
| human-0441 | iv | aaj se December shuru, aaj se roz 10 baje so jaana | 2026-12-01 22:00 | 2026-12-01 10:00 | daily from |
| human-0505 | vi | शुक्रवार की शाम है, 8 बजे खाना ऑर्डर करना | 2026-12-11 20:00 | 2026-12-18 20:00 | शुक्रवार की शाम है: statement naming today, Devanagari |
| human-0508 | iv | parso Tuesday ko beach shack pe dinner booking 8 baje | 2026-12-22 20:00 | 2026-12-22 08:00 |  |
| human-0518 | iii | Christmas ki raat 12 baje midnight mass dekhne jaana hai | 2026-12-25 00:00 | 2026-12-21 00:00 | night of 2026-12-24 |
| human-0542 | gold-hour | sat baje taxi airport se | 2026-12-21 07:00 | 2026-12-20 19:00 | bare 7 with no morning cue; hour rule gives 19:00, gold 07:00 |
| human-0551 | gold-other | jo ticket kal book kiya tha uska PNR mail mein hai | None None | 2026-12-19 None | past booking left undated, other past notes are dated |
| human-0576 | v | January ke end tak tax documents | 2027-01-31 None | None None |  |
| human-0623 | iii | last year Diwali pe Nani ke ghar gaye the | 2026-11-08 None | None None |  |
| human-0625 | i | pichle Monday gaadi service karwayi thi | 2026-12-28 None | 2026-12-21 None |  |
| human-0639 | iv | next week Thursday Delhi flight 7 baje | 2027-01-07 07:00 | 2027-01-07 19:00 | AM assumed |
| human-0647 | gold-other | 31 ki raat jo bill aaya tha usko split karna | 2026-12-31 None | 2026-12-31 21:00 | 31 ki raat: gold has no time; convention gives raat 21:00 |
| human-0670 | i | agle Friday bijli ka bill bharna hai | 2027-01-15 None | 2027-01-22 None | alt 2027-01-22 |
| human-0677 | ii | 3 din pehle laptop gira tha screen crack, Saturday ko service center | 2027-01-16 None | 2027-01-10 None | laptop dropped 2027-01-10 |
| human-0678 | ii | April mein Japan ki tickets is mahine book karni hai | 2027-01-31 None | None None |  |
| human-0705 | ii | 3:30 baje wali standup ke notes bhejne hai | 2027-01-13 15:30 | 2027-01-14 15:30 | 3:30 wali standup: the time names the meeting, the task is now |
| human-0708 | gold-weekday | बुधवार को शाम 6 बजे दर्ज़ी से कुर्ता लेना है | 2027-01-13 18:00 | 2027-01-20 18:00 | बुधवार at Wed 16:05: gold today, convention says next Wednesday |
| human-0725 | ii | 26 ko Coorg mein the wahan ki coffee mangwani hai | 2027-01-26 None | 2027-02-26 None |  |
| human-0728 | iv | 14 February ko 8 baje dinner booking | 2027-02-14 20:00 | 2027-02-14 08:00 |  |
| human-0731 | v | February ke end tak investment proofs submit karne hai | 2027-02-28 None | None None |  |
| human-0775 | iv | sava 8 baje kal dinner | 2027-03-01 20:15 | 2027-03-01 08:15 |  |
| human-0779 | v | next month end tak tax ka sab kaam | 2027-03-31 None | None None |  |
| human-0786 | iv | remind me tomorrow at 7 to leave early | 2027-03-01 07:00 | 2027-03-01 19:00 |  |
| human-0794 | iii | kal ke baad wala din chutti hai | 2027-03-02 None | 2027-03-01 None |  |
| human-0798 | ii | Saturday ko jo shoes liye the woh return karne hai | 2027-02-27 None | 2027-03-06 None | return undated |
| human-0801 | ii | abhi kuch der pehle Papa ne bola ki Tuesday ko aayenge | 2027-03-02 None | 2027-02-23 None |  |
| human-0813 | vi | kal 10k race daudi thi 58 minute mein | 2027-03-14 None | 2027-03-15 07:58 | 58 minute mein (race time) read as an offset |
| human-0821 | i | agle Friday bijli ka bill bharna hai | 2027-03-19 None | 2027-03-26 None |  |
| human-0841 | ii | kal raat 11 baje Arjun ne bola tha ki aaj 4 baje call karega | 2027-03-15 16:00 | 2027-03-16 04:00 | said 2027-03-14 23:00 |
| human-0847 | iii | har saal Holi pe Nani ke ghar, is baar bhi | 2027-03-22 None | None None | Holi |
| human-0848 | gold-hour | kal sat baje gym | 2027-03-16 07:00 | 2027-03-16 19:00 | kal 7 with no morning cue; hour rule gives 19:00, gold 07:00 |
| human-0858 | gold-other | kal subah dentist gaya tha bola 6 mahine baad aana | 2027-03-14 None | 2027-03-14 09:00 | kal subah ... gaya tha: gold has no time; convention gives subah 09:00 |
| human-0871 | i | agle Friday bijli ka bill bharna hai | 2027-05-14 None | 2027-05-21 None | alt 2027-05-21 |
| human-0898 | ii | 12 baje wali meeting cancel ho gayi thi Friday ko rakhi hai | 2027-05-14 12:00 | 2027-05-07 12:00 | time assumed unchanged |
| human-0948 | iii | har mahine last Friday ko team lunch, aaj hai | 2027-07-30 13:00 | 2027-07-23 None | monthly, last Friday |
| human-0979 | v | October mein half marathon hai 17 tareekh ko | 2027-10-17 None | 2027-09-17 None |  |
| human-0987 | v | September ke end tak appraisal | 2027-09-30 None | None None |  |
| human-0990 | iii | har Sunday raat 8 baje week ka plan banana | 2027-09-05 20:00 | 2027-09-12 20:00 | recurring every Sun 20:00 |
| human-1010 | ii | रविवार शाम है, अगले शनिवार को 11 बजे हेयरकट | 2027-09-11 11:00 | 2027-09-11 23:00 |  |
