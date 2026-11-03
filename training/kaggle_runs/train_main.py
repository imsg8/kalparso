# Route A (KalParso): 3 encoders x 5 seeds on v3 synthetic data + PHINC weak tense labels.
import glob, os, subprocess, sys
T = glob.glob("/kaggle/input/**/train_encoder.py", recursive=True)[0]
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "onnx", "onnxruntime"], check=False)
for models in ["muril", "xlmr", "mdistil"]:
    subprocess.run([sys.executable, T], env=dict(os.environ, KP_MODELS=models, KP_SEEDS="13,42,7,1,2", KP_DATA="v3", KP_PHINC="1"))
