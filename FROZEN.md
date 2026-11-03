# Frozen at 2026-10-31 04:29 IST

Grounding conventions and lexicon were calibrated on data/human/human_dev.jsonl only (262 rows, grouped split by sentence, seed 2026). Test-split scores were computed for monitoring; no convention was changed in response to them. The v3 data change (compositional clauses) was prompted by the synthetic held-out past-tense score (43.5%), not by test rows.

```
4c79986c3ef344f41b9b1dba93a08b81ee3c8bec7974c0ddda62e1dde60ea72c  src/ground.py
3a34a182167984d46b1ec29aebfa0893949c8a690aa37ce740d92b692019d6a2  src/lexicon.py
a167c4cfb359c93c295e94363700f8fdea5936c02d1675c122a32b7b54482964  src/rules.py
f27a90e75d91b84d52b369e3a5a3dffceab6c34b13c48564504827be93f506dd  src/generate.py
45d664c55e09b8a20d1bf13c9e150e72172e363df89105550fdcefb8ecf43917  data/human/split.json
```

Note added at release: one first name in the synthetic templates was replaced in `src/generate.py` and `data/v1`-`data/v3` (same length, labels unchanged), so the `generate.py` hash above is the frozen version, not the released one. The grounder, lexicon, rules and split are unchanged.
