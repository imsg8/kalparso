# Untrained LLM accuracy on Kaggle GPU (T4 x2) with Ollama. Outputs are prediction jsonl files.
import glob, json, os, subprocess, sys, time, urllib.request
MODELS = json.loads(os.environ.get("KP_MODELS", "null")) or json.loads('[["qwen3.5:4b", [["few2", "human_test", null]]], ["qwen3:8b", [["few2", "human_test", null], ["think2", "human_test", 150]]], ["llama3.1:8b", [["few2", "human_test", null]]], ["gemma3:12b", [["few2", "human_test", null]]], ["qwen3.5:0.8b", [["few2", "human_test", null]]], ["qwen3:30b-a3b", [["few2", "human_test", null]]], ["gemma4:26b", [["few2", "human_test", null]]], ["qwen3:32b", [["few2", "human_test", null], ["spans", "human_test", null]]]]')
SRC = os.path.dirname(glob.glob("/kaggle/input/**/llm_eval.py", recursive=True)[0])
DATA = os.path.dirname(glob.glob("/kaggle/input/**/human_test.jsonl", recursive=True)[0])
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
    for attempt in range(4):  # the registry sometimes answers 503
        r = subprocess.run(["ollama", "pull", model], capture_output=True, text=True)
        if r.returncode == 0: break
        time.sleep(60)
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
