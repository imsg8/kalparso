# Agreement audit: rows where 3 systems agree with each other but not with the gold

Nothing was changed. On reading all rows, nearly all are system errors (the gold is right); kept for the error-analysis section. Seen after the grounder was frozen, so none of it was used for tuning.

| id | spoken at | entry | gold | systems say | note |
|---|---|---|---|---|---|
| human-0023 | Sat 2026-10-31 02:35 | sava 10 baje subah bank jaana hai Saturday ko half day hota hai | 2026-10-31 10:15 | 2026-11-07 10:15 | sava = quarter past |
| human-0040 | Sat 2026-10-31 02:35 | Diwali se pehle ghar ki safai karwani hai | 2026-11-08 None | None None | Diwali 2026-11-08 |
| human-0080 | Mon 2026-11-02 08:10 | 2 din pehle Vicky se 2000 liye the Friday ko lauta dunga | 2026-11-06 None | 2026-10-31 None | borrowed 2026-10-31 |
| human-0081 | Mon 2026-11-02 08:10 | Diwali pe ghar jaana hai ticket check karo | 2026-11-08 None | None None | Diwali; ticket check undated |
| human-0086 | Mon 2026-11-02 08:10 | pichle Monday ko jo laptop repair diya tha woh aaj 4 baje ready hoga | 2026-11-02 16:00 | 2026-10-26 16:00 | given for repair 2026-10-26 |
| human-0087 | Mon 2026-11-02 08:10 | har Monday subah 9 baje team sync hota hai yaad dilate rehna | 2026-11-02 09:00 | 2026-11-09 09:00 | recurring every Monday 09:00 |
| human-0097 | Mon 2026-11-02 08:10 | kal Sunday ko jo meeting thi woh cancel ho gayi thi aaj 4 baje reschedule karni hai | 2026-11-02 16:00 | 2026-11-01 16:00 | meeting was 2026-11-01 |
| human-0116 | Tue 2026-11-03 13:20 | pichle hafte Thursday ko RTO gaya tha licence ke liye, 2 hafte mein aayega | 2026-10-29 None | 2026-11-17 None | licence expected ~2026-11-12 |
| human-0154 | Wed 2026-11-04 23:45 | kal subah 7 baje uthna hai standup 9:30 pe hai | 2026-11-05 07:00 | 2026-11-05 09:30 | standup 2026-11-05 09:30 |
| human-0161 | Wed 2026-11-04 23:45 | kal dopahar ko meeting thi woh mujhe miss ho gayi | 2026-11-03 None | 2026-11-03 13:00 | AMBIG near midnight: may mean today 2026-11-04 |
| human-0171 | Wed 2026-11-04 23:45 | jab uthu toh sabse pehle paani ki bottle bharni hai | 2026-11-05 09:00 | None None | on waking |
| human-0190 | Wed 2026-11-04 23:45 | kal raat 3 baje tak padha tha aaj jaldi so raha hu | 2026-11-04 03:00 | 2026-11-05 03:00 | Tue night |
| human-0197 | Wed 2026-11-04 23:45 | next week se daily shaam 6 baje walk | 2026-11-09 18:00 | 2026-11-05 18:00 | daily from |
| human-0219 | Thu 2026-11-05 06:30 | dentist on Thursday morning | 2026-11-05 09:00 | 2026-11-12 09:00 | AMBIG: today is Thu morning; alt 2026-11-12 |
| human-0230 | Thu 2026-11-05 06:30 | aaj se ek mahine baad lease khatam ho rahi hai naya ghar dhoondhna hai | 2026-12-05 None | 2026-11-05 None |  |
| human-0233 | Thu 2026-11-05 06:30 | kal hi to bola tha Raj ne ki Sunday ko aayega | 2026-11-08 None | 2026-11-01 None | said 2026-11-04 |
| human-0237 | Thu 2026-11-05 06:30 | end of next week tak appraisal form bharna | 2026-11-15 None | None None | alt 2026-11-13 (Fri) |
| human-0240 | Thu 2026-11-05 06:30 | next month ki 10 tareekh ko school reunion | 2026-12-10 None | 2026-11-10 None |  |
| human-0253 | Thu 2026-11-05 06:30 | kal raat jo khana bacha tha woh fridge mein hai aaj lunch mein le jaana | 2026-11-05 13:00 | 2026-11-05 21:00 |  |
| human-0273 | Fri 2026-11-06 19:15 | Wednesday ko office mein Kunal ko 500 diye the | 2026-11-04 None | 2026-11-11 None |  |
| human-0275 | Fri 2026-11-06 19:15 | pichle Sunday plants mein khaad daali thi agli baar 2 hafte baad | 2026-11-01 None | 2026-11-20 None | next ~2026-11-15 |
| human-0288 | Fri 2026-11-06 19:15 | abhi kuch der pehle Ma ka call aaya tha 9 baje wapas call karna | 2026-11-06 21:00 | 2026-11-06 09:00 |  |
| human-0298 | Fri 2026-11-06 19:15 | 10 baje tak Vikram ko kal ke liye confirm karna | 2026-11-06 22:00 | 2026-11-07 10:00 |  |
| human-0319 | Sun 2026-11-08 10:00 | kal raat 2 baje tak cards khele the | 2026-11-08 02:00 | 2026-11-10 02:00 | Sat night |
| human-0331 | Sun 2026-11-08 10:00 | 3 din baad office wapas, nahi nahi kal se office hai | 2026-11-09 None | 2026-11-11 None | self-correction |
| human-0336 | Sun 2026-11-08 10:00 | raat 1 baje tak pataakhe chalenge earplugs nikaal ke rakhna | 2026-11-08 21:00 | 2026-11-09 01:00 |  |
| human-0337 | Sun 2026-11-08 10:00 | next month Christmas pe Goa | 2026-12-25 None | None None |  |
| human-0354 | Sun 2026-11-08 10:00 | कल रात 12 बजे दीदी को फोन किया था, आज दोपहर में फिर करना | 2026-11-08 13:00 | 2026-11-08 12:00 | past call 2026-11-08 00:00 |
| human-0366 | Mon 2026-11-30 21:40 | next month Christmas ke liye Goa ki tickets | 2026-12-25 None | None None | booking task undated |
| human-0368 | Mon 2026-11-30 21:40 | 31 December ki party kaha karni hai Friday tak decide karna | 2026-12-04 None | 2026-12-31 None |  |
| human-0369 | Mon 2026-11-30 21:40 | is mahine ke end tak report bhejni thi, aaj hi bhejni hai | 2026-11-30 21:00 | 2026-11-30 None |  |
| human-0377 | Mon 2026-11-30 21:40 | Saturday ko Skandagiri trek, raat 3 baje nikalna hai | 2026-12-05 03:00 | 2026-12-06 03:00 |  |
| human-0387 | Mon 2026-11-30 21:40 | book dentist for next friday morning | 2026-12-04 09:00 | 2026-12-11 09:00 | alt 2026-12-11 |
| human-0404 | Mon 2026-11-30 21:40 | agle Friday bijli ka bill bharna hai | 2026-12-04 None | 2026-12-11 None |  |
| human-0410 | Tue 2026-12-01 00:10 | aaj shaam ko Rahul se mila tha | 2026-11-30 18:00 | 2026-12-01 18:00 | LATE-NIGHT: aaj = Monday |
| human-0411 | Tue 2026-12-01 00:10 | abhi 10 minute pehle Ma ka message aaya subah reply karna | 2026-12-01 09:00 | 2026-12-01 00:00 | msg 2026-12-01 00:00 |
| human-0416 | Tue 2026-12-01 00:10 | 1 baje tak so jaana hai | 2026-12-01 01:00 | 2026-12-01 13:00 |  |
| human-0422 | Tue 2026-12-01 00:10 | Christmas pe Goa | 2026-12-25 None | None None |  |
| human-0424 | Tue 2026-12-01 00:10 | agle Friday bijli ka bill bharna hai | 2026-12-04 None | 2026-12-11 None |  |
| human-0432 | Tue 2026-12-01 00:10 | next Sunday morning 7 baje cycling | 2026-12-06 07:00 | 2026-12-13 07:00 |  |
| human-0441 | Tue 2026-12-01 00:10 | aaj se December shuru, aaj se roz 10 baje so jaana | 2026-12-01 22:00 | 2026-12-01 10:00 | daily from |
| human-0505 | Fri 2026-12-11 17:50 | शुक्रवार की शाम है, 8 बजे खाना ऑर्डर करना | 2026-12-11 20:00 | 2026-12-18 20:00 |  |
| human-0508 | Sun 2026-12-20 15:15 | parso Tuesday ko beach shack pe dinner booking 8 baje | 2026-12-22 20:00 | 2026-12-22 08:00 |  |
| human-0518 | Sun 2026-12-20 15:15 | Christmas ki raat 12 baje midnight mass dekhne jaana hai | 2026-12-25 00:00 | 2026-12-21 00:00 | night of 2026-12-24 |
| human-0542 | Sun 2026-12-20 15:15 | sat baje taxi airport se | 2026-12-21 07:00 | 2026-12-20 19:00 | "sat" = saat |
| human-0551 | Sun 2026-12-20 15:15 | jo ticket kal book kiya tha uska PNR mail mein hai | None None | 2026-12-19 None | booked 2026-12-19 |
| human-0576 | Thu 2026-12-31 22:30 | January ke end tak tax documents | 2027-01-31 None | None None |  |
| human-0623 | Fri 2027-01-01 11:00 | last year Diwali pe Nani ke ghar gaye the | 2026-11-08 None | None None |  |
| human-0625 | Fri 2027-01-01 11:00 | pichle Monday gaadi service karwayi thi | 2026-12-28 None | 2026-12-21 None |  |
| human-0639 | Fri 2027-01-01 11:00 | next week Thursday Delhi flight 7 baje | 2027-01-07 07:00 | 2027-01-07 19:00 | AM assumed |
| human-0647 | Fri 2027-01-01 11:00 | 31 ki raat jo bill aaya tha usko split karna | 2026-12-31 None | 2026-12-31 21:00 | split task undated |
| human-0670 | Wed 2027-01-13 16:05 | agle Friday bijli ka bill bharna hai | 2027-01-15 None | 2027-01-22 None | alt 2027-01-22 |
| human-0677 | Wed 2027-01-13 16:05 | 3 din pehle laptop gira tha screen crack, Saturday ko service center | 2027-01-16 None | 2027-01-10 None | laptop dropped 2027-01-10 |
| human-0678 | Wed 2027-01-13 16:05 | April mein Japan ki tickets is mahine book karni hai | 2027-01-31 None | None None |  |
| human-0705 | Wed 2027-01-13 16:05 | 3:30 baje wali standup ke notes bhejne hai | 2027-01-13 15:30 | 2027-01-14 15:30 | send notes now |
| human-0708 | Wed 2027-01-13 16:05 | बुधवार को शाम 6 बजे दर्ज़ी से कुर्ता लेना है | 2027-01-13 18:00 | 2027-01-20 18:00 |  |
| human-0725 | Sat 2027-01-30 09:20 | 26 ko Coorg mein the wahan ki coffee mangwani hai | 2027-01-26 None | 2027-02-26 None |  |
| human-0728 | Sat 2027-01-30 09:20 | 14 February ko 8 baje dinner booking | 2027-02-14 20:00 | 2027-02-14 08:00 |  |
| human-0731 | Sat 2027-01-30 09:20 | February ke end tak investment proofs submit karne hai | 2027-02-28 None | None None |  |
| human-0775 | Sun 2027-02-28 20:45 | sava 8 baje kal dinner | 2027-03-01 20:15 | 2027-03-01 08:15 |  |
| human-0779 | Sun 2027-02-28 20:45 | next month end tak tax ka sab kaam | 2027-03-31 None | None None |  |
| human-0786 | Sun 2027-02-28 20:45 | remind me tomorrow at 7 to leave early | 2027-03-01 07:00 | 2027-03-01 19:00 |  |
| human-0794 | Sun 2027-02-28 20:45 | kal ke baad wala din chutti hai | 2027-03-02 None | 2027-03-01 None |  |
| human-0798 | Sun 2027-02-28 20:45 | Saturday ko jo shoes liye the woh return karne hai | 2027-02-27 None | 2027-03-06 None | return undated |
| human-0801 | Sun 2027-02-28 20:45 | abhi kuch der pehle Papa ne bola ki Tuesday ko aayenge | 2027-03-02 None | 2027-02-23 None |  |
| human-0813 | Mon 2027-03-15 07:00 | kal 10k race daudi thi 58 minute mein | 2027-03-14 None | 2027-03-15 07:58 |  |
| human-0821 | Mon 2027-03-15 07:00 | agle Friday bijli ka bill bharna hai | 2027-03-19 None | 2027-03-26 None |  |
| human-0841 | Mon 2027-03-15 07:00 | kal raat 11 baje Arjun ne bola tha ki aaj 4 baje call karega | 2027-03-15 16:00 | 2027-03-16 04:00 | said 2027-03-14 23:00 |
| human-0847 | Mon 2027-03-15 07:00 | har saal Holi pe Nani ke ghar, is baar bhi | 2027-03-22 None | None None | Holi |
| human-0848 | Mon 2027-03-15 07:00 | kal sat baje gym | 2027-03-16 07:00 | 2027-03-16 19:00 | "sat" = saat |
| human-0858 | Mon 2027-03-15 07:00 | kal subah dentist gaya tha bola 6 mahine baad aana | 2027-03-14 None | 2027-03-14 09:00 | follow-up ~2027-09-14 |
| human-0871 | Wed 2027-05-12 14:30 | agle Friday bijli ka bill bharna hai | 2027-05-14 None | 2027-05-21 None | alt 2027-05-21 |
| human-0898 | Wed 2027-05-12 14:30 | 12 baje wali meeting cancel ho gayi thi Friday ko rakhi hai | 2027-05-14 12:00 | 2027-05-07 12:00 | time assumed unchanged |
| human-0948 | Fri 2027-07-30 12:00 | har mahine last Friday ko team lunch, aaj hai | 2027-07-30 13:00 | 2027-07-23 None | monthly, last Friday |
| human-0979 | Sun 2027-09-05 18:55 | October mein half marathon hai 17 tareekh ko | 2027-10-17 None | 2027-09-17 None |  |
| human-0987 | Sun 2027-09-05 18:55 | September ke end tak appraisal | 2027-09-30 None | None None |  |
| human-0990 | Sun 2027-09-05 18:55 | har Sunday raat 8 baje week ka plan banana | 2027-09-05 20:00 | 2027-09-12 20:00 | recurring every Sun 20:00 |
| human-1010 | Sun 2027-09-05 18:55 | रविवार शाम है, अगले शनिवार को 11 बजे हेयरकट | 2027-09-11 11:00 | 2027-09-11 23:00 |  |
