"""KalParso runtime: one informal Hinglish/English planner entry -> {type, date, time}, on CPU.
Dependencies: onnxruntime, tokenizers, numpy (no PyTorch, no transformers).
  python kalparso.py MODEL_DIR "kal shaam 5 baje gym jaana"            (anchor = now)
  python kalparso.py MODEL_DIR "kal gym gaya tha" --anchor 2026-10-31T22:06
  from kalparso import KalParso; KalParso(MODEL_DIR)("parso subah dentist")"""
import json, os, sys
from datetime import datetime

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ground import ground_entry


class KalParso:
    def __init__(self, model_dir, onnx_file=None, threads=1):
        meta = json.load(open(f"{model_dir}/meta.json"))
        self.labels, self.types, self.dirs, self.maxlen = meta["labels"], meta["types"], meta["dirs"], meta["maxlen"]
        self.tok = Tokenizer.from_file(f"{model_dir}/tokenizer.json")
        self.tok.enable_truncation(self.maxlen)
        so = ort.SessionOptions(); so.intra_op_num_threads = threads; so.inter_op_num_threads = 1
        f = onnx_file or ("model.onnx" if os.path.exists(f"{model_dir}/model.onnx") else "model.int8.onnx")
        self.sess = ort.InferenceSession(f"{model_dir}/{f}", so, providers=["CPUExecutionProvider"])

    def __call__(self, text, anchor=None):
        anchor = anchor or datetime.now().replace(second=0, microsecond=0)
        enc = self.tok.encode(text)
        ids = np.array([enc.ids], dtype=np.int64)
        tg, ty, di = self.sess.run(None, {"input_ids": ids, "attention_mask": np.ones_like(ids)})
        spans, cur = [], None
        for (s, e), t in zip(enc.offsets, tg[0].argmax(-1).tolist()):
            if s == e: continue
            lab = self.labels[t]
            if lab == "O": cur = None; continue
            p, l = lab.split("-")
            if p == "B" or cur is None or cur[0] != l or s > cur[2] + 1: cur = [l, s, e]; spans.append(cur)
            else: cur[2] = e
        spans = [(l, text[s:e]) for l, s, e in spans]
        typ, dirn = self.types[int(ty[0].argmax())], self.dirs[int(di[0].argmax())]
        date, time = ground_entry(spans, dirn, anchor, typ, text)
        return {"type": typ, "date": date, "time": time, "direction": dirn, "spans": spans}


if __name__ == "__main__":
    args = sys.argv[1:]
    anchor = None
    if "--anchor" in args:
        i = args.index("--anchor"); anchor = datetime.fromisoformat(args[i + 1]); del args[i:i + 2]
    kp = KalParso(args[0])
    for t in args[1:]:
        print(json.dumps({"text": t, **kp(t, anchor)}, ensure_ascii=False))
