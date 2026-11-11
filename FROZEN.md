# Frozen at 2026-10-31 04:29 IST

Grounding conventions and lexicon were calibrated on data/human/human_dev.jsonl only (262 rows, grouped split by sentence, seed 2026). Test-split scores were computed for monitoring; no convention was changed in response to them. The v3 data change (compositional clauses) was prompted by the synthetic held-out past-tense score (43.5%), not by test rows.

```
4c79986c3ef344f41b9b1dba93a08b81ee3c8bec7974c0ddda62e1dde60ea72c  src/ground.py
3a34a182167984d46b1ec29aebfa0893949c8a690aa37ce740d92b692019d6a2  src/lexicon.py
a167c4cfb359c93c295e94363700f8fdea5936c02d1675c122a32b7b54482964  src/rules.py
f27a90e75d91b84d52b369e3a5a3dffceab6c34b13c48564504827be93f506dd  src/generate.py
45d664c55e09b8a20d1bf13c9e150e72172e363df89105550fdcefb8ecf43917  data/human/split.json
```

Edits after the freeze. Three of the five files above were edited after the hashes were recorded, so `sha256sum -c` reports them as changed. None of the edits changes a grounding rule, a lexicon entry or a label:

- `src/ground.py`: one comment reworded ("dictation" to "informal spelling").
- `src/lexicon.py`: the module docstring reworded the same way.
- `src/generate.py`: one first name in the templates replaced (same length, also in `data/v1` to `data/v3`), one comment updated, and two lines added so the script creates its output folder (`import os`, `os.makedirs`).

`FROZEN.patch` is the exact diff from the frozen files to the released ones. To check the hashes, undo it on a copy:

```bash
cp -r . /tmp/kp_frozen && cd /tmp/kp_frozen && patch -R -p1 < FROZEN.patch && sha256sum -c <(grep -E '^[0-9a-f]{64}' FROZEN.md)
```
