# Learning curve on MuRIL with equal optimizer steps: epochs = 3 x 30000 / n, v3 data, no PHINC, 3 seeds. Weights not saved.
import glob, os, subprocess, sys
T = glob.glob("/kaggle/input/**/train_encoder.py", recursive=True)[0]
base = dict(os.environ, KP_MODELS="muril", KP_SEEDS="13,42,7", KP_ONNX="0", KP_SAVE="0", KP_DATA="v3")
for n in [1000, 3000, 10000]:
    subprocess.run([sys.executable, T], env=dict(base, KP_NTRAIN=str(n), KP_EPOCHS=str(90000 // n), KP_TAG=f"v3_n{n}_eqsteps"))
