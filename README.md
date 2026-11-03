# KalParso: Millisecond Temporal Grounding of Informal Hindi-English Planner Entries on a Commodity CPU

Grounding informal Hinglish planner entries to an exact date and time, on a CPU, in milliseconds.

*"parso shaam saade 5 baje dentist"* written on Saturday 31 October at 14:00 means **Monday 2 November, 17:30**. *"kal"* means tomorrow or yesterday depending only on the verb's tense, and the clock words (*saade*, *paune*, *raat 2 baje*) follow conventions that general date parsers do not know. KalParso tags the time spans and the tense with a small multilingual encoder, and a 200-line deterministic grounder does the calendar arithmetic.

## Results (706 held-out human entries, date and time both correct)

| System | Parameters | Accuracy | CPU latency per entry |
|---|---|---|---|
| **KalParso-MuRIL** (5 seeds) | 0.24B | **86.1 ± 0.3%** | 29 ms (fp32, 1 core) |
| **KalParso-XLM-R** int8 (5 seeds) | 0.28B | **85.4 ± 0.6%** | **17 ms** (1 core) |
| KalParso-mDistilBERT (5 seeds) | 0.14B | 84.3 ± 0.9% | 9 ms (int8, 1 core) |
| Cascade: KalParso-MuRIL, gemma4:26b on 6% of entries | 0.24B + 26B | 88.0 ± 0.1% | about 0.7 s on average |
| Rules only (this repo's grounder with a rule tagger) | 0 | 85.7% | |
| gemma4:26b, untrained, prompted with the conventions | 26B | 89.0% | 10.8 s (8 cores) |
| gemma3:27b, same prompt | 27B | 82.3% | 34.0 s |
| qwen3:32b, same prompt | 33B | 69.8% | 44.0 s |
| gpt-oss:20b, same prompt, low reasoning | 21B | 67.1% | 18.0 s |
| qwen3.5:4b, same prompt | 4B | 56.4% | 18.9 s |
| dateparser / Duckling | | 20.8% / 22.0% | |

CPU: Intel Core i7-9700 (2019), 35 W cap, no GPU. All rows, seeds, significance tests and ablations: `results/REPORT.md` after running the report (below).

## Quick start (CPU, no PyTorch)

```bash
pip install -r requirements.txt
python src/kalparso.py MODEL_DIR "kal shaam 5 baje gym jaana"
python src/kalparso.py MODEL_DIR "kal gym gaya tha" --anchor 2026-10-31T22:06
```

```python
from kalparso import KalParso
kp = KalParso("MODEL_DIR")
kp("parso subah dentist")   # {'type': 'reminder', 'date': ..., 'time': ...}
```

`MODEL_DIR` holds `model.onnx` (or `model.int8.onnx`), `tokenizer.json` and `meta.json`. Trained models: see *Models* below.

## Reproduce the numbers

Every prediction file behind the reported results is in `results/`, so the scores can be rebuilt without a GPU:

```bash
pip install -r requirements.txt
python results/report.py              # results/REPORT.md, results/report.json
python tests/smoke.py                 # grounder and scorer checks
```

### Out of domain: NTX Hindi

Formal Devanagari Hindi from NTX (Chen et al., 2023), zero-shot. Put `ntxt-HI-t.jsonl` from Hugging Face `tellarin-ai/ntx_llm_inst_hindi` in `data/external/ntx_hindi/`, download the three models, and run:

```bash
python bench/eval_ntx.py kalparso-muril/onnx kalparso-xlmr/onnx kalparso-mdistil/onnx
```

It builds the 469 scored sentences (532 gold spans) and the 140 single date or time expressions, and writes span precision, recall and F1 (`results/human/ntx_span_detection.json`), grounding accuracy (`ntx_grounding.json`) and every prediction (`ntxall_*.jsonl`, `ntx_*_points.jsonl`). A gold span is found when a predicted span overlaps it, and a predicted span that overlaps no gold span is a false positive. With the released models:

| System | Span P | Span R | Span F1 | Grounded (of 140) |
|---|---|---|---|---|
| Rules | 78.6 | 31.0 | 44.5 | 8.6% |
| KalParso-MuRIL | 84.6 | 89.7 | 87.0 | 10.0% |
| KalParso-XLM-R | 85.5 | 88.5 | 87.0 | 10.0% |
| KalParso-mDistilBERT | 42.4 | 88.2 | 57.3 | 10.0% |

Grounding stays low because the lexicon has no formal Hindi number words or Devanagari month names, and NTX's resolved values use reference dates that differ from the one its prompts state.

## Repository

| Path | What |
|---|---|
| `spec.md` | Task, labels and grounding conventions |
| `FROZEN.md` | Hashes of the grounder and split at the point the conventions were frozen |
| `src/` | `ground.py` (grounder), `lexicon.py`, `rules.py` (rules baseline), `generate.py` (synthetic data), `eval_human.py` (scoring, McNemar, bootstrap), `kalparso.py` (ONNX runtime) |
| `data/v1`, `data/v2`, `data/v3` | Synthetic train / dev / held-out test sets (about 30k / 2k / 2k); v3 is the final one (29,911 / 1,988 / 1,999), v1 and v2 are archived snapshots for the ablation |
| `data/human/` | 1,010 real entries with human answers; `split.json` puts 262 in `human_dev` (calibration) and 748 in `human_test` (706 scored) |
| `training/` | Encoder fine-tuning (`train_encoder.py`), Qwen3-0.6B LoRA baseline, and the Kaggle run scripts |
| `baselines/` | Rules, dateparser, Duckling, untrained LLMs through Ollama (`llm_eval.py`) |
| `llm_eval/kaggle_runs/` | The LLM accuracy runs (Kaggle, 2 x T4) |
| `bench/` | CPU latency, throughput, energy (RAPL), thermal-safe LLM timing, and the NTX out-of-domain check (`eval_ntx.py`) |
| `results/` | Predictions, timing JSON, report scripts |
| `scripts/` | PHINC weak labels and where to get third-party data |

## Synthetic data

```bash
cd src && python generate.py /tmp/kp_gen && cd ..             # 30,000 / 2,000 / 2,000 rows, seed 13
python -I scripts/decontaminate.py /tmp/kp_gen data/v3          # drops rows that match a human entry -> data/v3, byte for byte
```

One illustrative first name in the generator's templates was changed after training (to Kunal); the shipped data and the generator match each other, and the change does not affect any label.

## Training

```bash
pip install -r requirements-train.txt
python -I scripts/build_phinc_labels.py <PHINC csv> data/v3/phinc_dir.jsonl   # optional, see scripts/fetch_external.md
KP_DATA=v3 KP_PHINC=1 KP_MODELS=muril KP_SEEDS=13 python training/train_encoder.py
```

One MuRIL run takes about 12 minutes on one NVIDIA T4. Outputs go to `results/v2/` (predictions, weights, ONNX).

## How the LLMs were measured

Accuracy runs use two NVIDIA T4 GPUs on Kaggle (all 748 entries). CPU latency and energy are measured on the i7-9700 on 10 to 30 entries per model, with a pause before each request until the CPU cools below a set temperature (`bench/run_llm_cpu.sh`). On the 175 entries timed on both, 160 answers are identical. gpt-oss always reasons and runs with `think="low"`; all other models answer without reasoning unless a row says *think*.

## Models

On Hugging Face, each with ONNX files for CPU inference, fp16 safetensors and the runtime (`kalparso.py`, `ground.py`, `lexicon.py`):

| Model | Base | Held-out test | Use |
|---|---|---|---|
| [kalparso-xlmr](https://huggingface.co/imsg8/kalparso-xlmr) | XLM-R base | 86.4% (int8: 85.8%) | Recommended: int8, 278 MB, 17 ms per entry |
| [kalparso-muril](https://huggingface.co/imsg8/kalparso-muril) | MuRIL base | 86.4% | Most accurate; fp32 only, int8 breaks it |
| [kalparso-mdistil](https://huggingface.co/imsg8/kalparso-mdistil) | mDistilBERT | 85.0% (int8: 83.6%) | Smallest: int8, 135 MB, 9 ms per entry |

Data: [imsg8/kalparso](https://huggingface.co/datasets/imsg8/kalparso) (configs `synthetic` and `human`).

## Data and licences

- Code: Apache-2.0 (`LICENSE`).
- KalParso data: CC BY 4.0 (`data/LICENSE`).
- Third-party corpora (PHINC, NTX, Kaggle Hinglish sets) are not included: `scripts/fetch_external.md`.
- The 1,010 human entries were written and labelled by the first author for this test set and contain no personal information. Do not train on `data/human/human_test.jsonl`.

## Citation

Archived on Zenodo: [10.5281/zenodo.23910743](https://doi.org/10.5281/zenodo.23910743) (all versions). See `CITATION.cff`.
