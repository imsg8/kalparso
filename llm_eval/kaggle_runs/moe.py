# Untrained LLM accuracy on Kaggle GPU (T4 x2) with Ollama. Outputs are prediction jsonl files.
import glob, json, os, subprocess, sys, time, urllib.request
MODELS = json.loads(os.environ.get("KP_MODELS", "null")) or json.loads('[["qwen3:30b-a3b", [["few", "test_human", null], ["spans", "test_human", null], ["zero", "test_human", 300], ["few", "test_synth_300", null], ["think", "test_human", 150]]], ["gemma4:26b", [["few", "test_human", null], ["spans", "test_human", null], ["zero", "test_human", 300], ["few", "test_synth_300", null]]]]')
SRC = os.path.dirname(glob.glob("/kaggle/input/**/llm_eval.py", recursive=True)[0])
DATA = os.path.dirname(glob.glob("/kaggle/input/**/test_human.jsonl", recursive=True)[0])
OUT = "/kaggle/working"
print(SRC, DATA, MODELS, flush=True)
subprocess.run("apt-get install -y -qq zstd >/dev/null 2>&1; curl -fsSL https://ollama.com/install.sh | sh", shell=True, check=True)
env = dict(os.environ, OLLAMA_NUM_PARALLEL="4", OLLAMA_MAX_LOADED_MODELS="1", OLLAMA_KEEP_ALIVE="30m")
srv = subprocess.Popen(["ollama", "serve"], env=env, stdout=open(f"{OUT}/ollama.log", "w"), stderr=subprocess.STDOUT)
for _ in range(60):
    try: urllib.request.urlopen("http://localhost:11434/api/tags"); break
    except Exception: time.sleep(2)
subprocess.run("nvidia-smi", shell=True)
for model, jobs in MODELS:
    t0 = time.time()
    r = subprocess.run(["ollama", "pull", model], capture_output=True, text=True)
    print("pull", model, r.returncode, f"{time.time()-t0:.0f}s", r.stderr[-300:], flush=True)
    if r.returncode: continue
    tag = model.replace(":", "_").replace("/", "_")
    for mode, split, limit in jobs:
        dst = f"{OUT}/{tag}.{mode}.{split}.jsonl"
        subprocess.run([sys.executable, f"{SRC}/llm_eval.py", model, mode, f"{DATA}/{split}.jsonl", dst, str(limit or "-"),
                        "4"], env=dict(os.environ, KP_SRC=SRC))
    subprocess.run(["ollama", "ps"]); subprocess.run(["ollama", "rm", model])
srv.terminate()
print("ALL DONE", flush=True)
