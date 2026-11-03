# Third-party data (not redistributed)

These corpora were used in training and evaluation but are not part of this repository. Get them from their owners and follow their licences.

| Use | Source | Put it in |
|---|---|---|
| PHINC weak tense labels for training (`KP_PHINC=1`) | PHINC parallel Hinglish corpus (Srivastava and Singh, 2020), Kaggle `mrutyunjaybiswal/phincparallel-hinglish-corpus-machine-translation` | `data/external/phinc/` |
| Real-text tense check (`bench/tense_real.py`) | same PHINC file | `data/external/phinc/` |
| Mined Hinglish time expressions (`src/mine_external.py`) | Kaggle `mansiaggarwal88/hinglish-code-mixed-nlp-dataset-55k`, `ctolerate/hinglish-customer-support-conversations-dataset` | `data/external/<name>/` |
| Out-of-domain test, formal Hindi (`bench/eval_ntx.py`) | NTX Hindi (Chen et al., 2023), Hugging Face `tellarin-ai/ntx_llm_inst_hindi`, file `ntxt-HI-t.jsonl` (CC BY-SA) | `data/external/ntx_hindi/` |

Build the PHINC weak labels after downloading:

```bash
python -I scripts/build_phinc_labels.py "data/external/phinc/English-Hindi code-mixed parallel corpus.csv" data/v3/phinc_dir.jsonl
```
