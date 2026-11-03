# Ablations on MuRIL, 3 seeds each: data versions (v2 / v3 / v3+PHINC is the main run), learning curve, noise.
import glob, os, subprocess, sys
T = glob.glob("/kaggle/input/**/train_encoder.py", recursive=True)[0]
base = dict(os.environ, KP_MODELS="muril", KP_SEEDS="13,42,7", KP_ONNX="0")
subprocess.run([sys.executable, T], env=dict(base, KP_DATA="v2"))
subprocess.run([sys.executable, T], env=dict(base, KP_DATA="v3"))
subprocess.run([sys.executable, T], env=dict(base, KP_DATA="v1"))
for n in ["1000", "3000", "10000"]:
    subprocess.run([sys.executable, T], env=dict(base, KP_NTRAIN=n, KP_DATA="v3", KP_PHINC="1"))
subprocess.run([sys.executable, T], env=dict(base, KP_DATA="v3", KP_PHINC="1", KP_CLEAN="1", KP_TAG="v3clean_phinc"))
