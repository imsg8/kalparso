"""int8 variants of a route A ONNX model. Plain dynamic quantization breaks MuRIL (80.7 -> 3.7 full match),
so this tries safer settings. Usage: python quantize.py results/kaggle_a/routeA_muril_onnx"""
import os, sys
import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType

d = sys.argv[1]
src = f"{d}/model.onnx"
heads = [n.name for n in onnx.load(src, load_external_data=False).graph.node
         if n.op_type in ("MatMul", "Gemm") and any(o in ("tags", "type", "dir") or "tag" in o or "typ" in o for o in n.output)]
variants = {
    "int8pc": dict(per_channel=True, reduce_range=True),                      # per-channel scales
    "int8mm": dict(per_channel=True, op_types_to_quantize=["MatMul"]),        # skip the embedding Gather
    "int8mmh": dict(per_channel=True, op_types_to_quantize=["MatMul"], nodes_to_exclude=heads),  # + fp32 heads
}
for name, kw in variants.items():
    quantize_dynamic(src, f"{d}/model.{name}.onnx", weight_type=QuantType.QInt8, **kw)
    print(name, f"{os.path.getsize(f'{d}/model.{name}.onnx') / 1e6:.0f} MB")
