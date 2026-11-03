# Untrained gpt-oss:20b on Kaggle GPU (T4 x2) with Ollama. Outputs are prediction jsonl files.
# KP_THINK: Ollama think value for reasoning-only models (gpt-oss: "low"), passed to baselines/llm_eval.py.
import glob, json, os, shutil, subprocess, sys, time, urllib.request
T_END = time.time() + 11 * 3600  # Kaggle stops at 12 h; stop early so partial files are kept
MODELS = json.loads(os.environ.get("KP_MODELS", "null")) or json.loads('[["gpt-oss:20b", [["few2", "human_test", null], ["spans", "human_test", null]]]]')
THINK = os.environ.get("KP_THINK", "low")
SRC = os.path.dirname(glob.glob("/kaggle/input/**/llm_eval.py", recursive=True)[0])
DATA = os.path.dirname(glob.glob("/kaggle/input/**/human_test.jsonl", recursive=True)[0])
OUT = "/kaggle/working"
EVAL = f"{OUT}/llm_eval_patched.py"
s = open(f"{SRC}/llm_eval.py").read()
if THINK:
    a = 'think = mode in ("think", "think2")'
    assert a in s; s = s.replace(a, 'think = os.environ.get("KP_THINK") or mode in ("think", "think2")')
open(EVAL, "w").write(s)
print(SRC, DATA, MODELS, "think:", THINK or None, flush=True)
subprocess.run("apt-get install -y -qq zstd >/dev/null 2>&1; curl -fsSL https://ollama.com/install.sh | sh", shell=True, check=True)
env = dict(os.environ, OLLAMA_NUM_PARALLEL="4", OLLAMA_MAX_LOADED_MODELS="1", OLLAMA_KEEP_ALIVE="60m")
srv = subprocess.Popen(["ollama", "serve"], env=env, stdout=open(f"{OUT}/ollama.log", "w"), stderr=subprocess.STDOUT)
for _ in range(60):
    try: urllib.request.urlopen("http://localhost:11434/api/tags"); break
    except Exception: time.sleep(2)
subprocess.run("nvidia-smi; free -g; df -h / /kaggle/working", shell=True)
for model, jobs in MODELS:
    if time.time() > T_END - 1800: print("no time left for", model, flush=True); break
    t0 = time.time()
    for attempt in range(4):  # the registry sometimes answers 503
        r = subprocess.run(["ollama", "pull", model], capture_output=True, text=True)
        if r.returncode == 0: break
        time.sleep(60)
    print("pull", model, r.returncode, f"{time.time()-t0:.0f}s", r.stderr[-300:], flush=True)
    subprocess.run("df -h /", shell=True)
    if r.returncode: continue
    tag = model.replace(":", "_").replace("/", "_")
    for mode, split, limit in jobs:
        left = T_END - time.time()
        if left < 900: print("skip", model, mode, "no time", flush=True); continue
        dst = f"{OUT}/{tag}.{mode}.{split}.jsonl"
        try:
            subprocess.run([sys.executable, EVAL, model, mode, f"{DATA}/{split}.jsonl", dst, str(limit or "-"), "4"],
                           env=dict(os.environ, KP_SRC=SRC, KP_THINK=THINK), timeout=left)
        except subprocess.TimeoutExpired:
            print("time budget hit", model, mode, flush=True)
        subprocess.run(["ollama", "ps"])
    subprocess.run(["ollama", "rm", model]); subprocess.run("df -h /", shell=True)
srv.terminate()
print("ALL DONE", flush=True)
