"""CPU stress and efficiency benchmark (desktop i7-9700, 8 cores, no GPU). One system per call.
Phases: single-stream latency, concurrency sweep, sustained load, per-request CPU spike, energy (Intel RAPL).
CPU use is read system-wide from /proc/stat (10 ms jiffies) minus the idle baseline measured first, so in-process
ONNX and the Ollama server are measured the same way.
Usage: python stress.py SYSTEM ARG data.jsonl out.json [--single N] [--conc 1,2,4,8] [--per-level N]
                        [--sustain SEC] [--spike K]
  SYSTEM ARG:  onnx DIR:FILE   |  ollama MODEL  |  rules -"""
import argparse, glob, json, os, resource, statistics, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src")); sys.path.insert(0, os.path.join(HERE, "..", "baselines"))
from ground import ground_entry

ap = argparse.ArgumentParser()
ap.add_argument("system"); ap.add_argument("arg"); ap.add_argument("data"); ap.add_argument("out")
ap.add_argument("--single", type=int, default=200); ap.add_argument("--conc", default="1,2,4,8")
ap.add_argument("--per-level", type=int, default=200); ap.add_argument("--sustain", type=float, default=0)
ap.add_argument("--spike", type=int, default=20); ap.add_argument("--threads", type=int, default=1)
ap.add_argument("--mode", default="few2")
ap.add_argument("--proc", default="", help="cmdline substring of the model's runner process (its GGUF blob)")
ap.add_argument("--cool", type=float, default=0, help="before each single-stream request, wait while the CPU package is at or above this many C")
A = ap.parse_args()
rows = [json.loads(l) for l in open(A.data)]
NCPU = os.cpu_count()
RAPL = next((p for p in ("/rapl0/energy_uj", "/powercap/intel-rapl:0/energy_uj", "/sys/class/powercap/intel-rapl:0/energy_uj")
             if os.path.exists(p)), None)


def cpu_busy():
    """(busy_jiffies, total_jiffies) across all cores."""
    v = list(map(int, open("/proc/stat").readline().split()[1:]))
    idle = v[3] + v[4]
    return sum(v) - idle, sum(v)


TCK = os.sysconf("SC_CLK_TCK")


def own_cpu(pattern=None):
    """CPU seconds used so far by this process (in-process models) or by host processes matching pattern (Ollama)."""
    if not pattern:
        t = os.times(); return t.user + t.system
    tot = 0.0
    for pid in filter(str.isdigit, os.listdir("/proc")):
        try:
            if pattern in open(f"/proc/{pid}/cmdline", "rb").read().decode(errors="ignore"):
                f = open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()
                tot += (int(f[11]) + int(f[12])) / TCK
        except Exception:
            pass
    return tot


def energy_j():
    try: return int(open(RAPL).read()) / 1e6
    except Exception: return None


def rss_mb_of(pattern):
    """Total RSS (MB) of host processes whose cmdline contains pattern (needs --pid host for Ollama)."""
    tot = 0
    for pid in filter(str.isdigit, os.listdir("/proc")):
        try:
            if pattern in open(f"/proc/{pid}/cmdline", "rb").read().decode(errors="ignore"):
                for l in open(f"/proc/{pid}/status"):
                    if l.startswith("VmRSS"): tot += int(l.split()[1]) / 1024
        except Exception:
            pass
    return tot


class Meter:
    """Samples the system's own CPU time every 10 ms (cores in use by the model process, not the whole box),
    plus package energy and peak RSS."""
    def __init__(self, base_cores, rss_pat=None):
        self.base, self.rss_pat = base_cores, rss_pat
    def __enter__(self):
        self.series, self.stop, self.peak_rss = [], False, 0
        self.t0, self.e0, self.c0 = time.perf_counter(), energy_j(), own_cpu(self.rss_pat)
        def loop():
            prev, pt, k = own_cpu(self.rss_pat), time.perf_counter(), 0
            while not self.stop:
                time.sleep(0.01)
                cur, ct = own_cpu(self.rss_pat), time.perf_counter()
                self.series.append((ct - self.t0, (cur - prev) / (ct - pt)))
                prev, pt = cur, ct
                k += 1
                if self.rss_pat and k % 50 == 0: self.peak_rss = max(self.peak_rss, rss_mb_of(self.rss_pat))
        self.th = threading.Thread(target=loop, daemon=True); self.th.start()
        return self
    def __exit__(self, *a):
        self.stop = True; self.th.join()
        self.wall = time.perf_counter() - self.t0
        self.cpu_s = own_cpu(self.rss_pat) - self.c0
        e1 = energy_j()
        self.energy = (e1 - self.e0) if (e1 is not None and self.e0 is not None and e1 >= self.e0) else None
        self.energy_above_idle = (self.energy - IDLE_W * self.wall) if (self.energy is not None and IDLE_W) else None
        if self.rss_pat: self.peak_rss = max(self.peak_rss, rss_mb_of(self.rss_pat))


# ---------- systems
def make_runner():
    if A.system == "onnx":
        import onnxruntime as ort
        from transformers import AutoTokenizer
        d, fname = A.arg.split(":")
        meta = json.load(open(f"{d}/meta.json")); tok = AutoTokenizer.from_pretrained(d)
        so = ort.SessionOptions(); so.intra_op_num_threads = A.threads; so.inter_op_num_threads = 1
        sess = ort.InferenceSession(f"{d}/{fname}", so, providers=["CPUExecutionProvider"])
        labels, types, dirs = meta["labels"], meta["types"], meta["dirs"]
        def run(r):
            enc = tok(r["text"], return_offsets_mapping=True, truncation=True, max_length=meta["maxlen"], return_tensors="np")
            tg, ty, di = sess.run(None, {"input_ids": enc["input_ids"].astype("int64"),
                                         "attention_mask": enc["attention_mask"].astype("int64")})
            spans, cur = [], None
            for (s, e), t in zip(enc["offset_mapping"][0].tolist(), tg[0].argmax(-1).tolist()):
                if s == e: continue
                lab = labels[t]
                if lab == "O": cur = None; continue
                p, l = lab.split("-")
                if p == "B" or cur is None or cur[0] != l or s > cur[2] + 1: cur = [l, s, e]; spans.append(cur)
                else: cur[2] = e
            spans = [(l, r["text"][s:e]) for l, s, e in spans]
            typ = types[int(ty[0].argmax())]
            d_, t_ = ground_entry(spans, dirs[int(di[0].argmax())], datetime.fromisoformat(r["anchor"]), typ, r["text"])
            return {"type": typ, "date": d_, "time": t_}
        size = os.path.getsize(f"{d}/{fname}") / 2 ** 20
        return run, size, None
    if A.system == "ollama":
        import llm_eval
        def run(r):
            y = llm_eval.one(A.arg, A.mode, r)
            return {k: y.get(k) for k in ("type", "date", "time", "eval_count", "prompt_eval_count", "err")}
        return run, None, (A.proc or "llama-server")
    from rules import predict
    return (lambda r: {k: v for k, v in predict(r["text"], datetime.fromisoformat(r["anchor"])).items()
                       if k in ("type", "date", "time")}), 0, None


def pct(xs, q):
    xs = sorted(xs); return xs[min(int(q * len(xs)), len(xs) - 1)] if xs else None


res = {"system": A.system, "arg": A.arg, "threads": A.threads, "mode": A.mode, "host_cpus": NCPU,
       "started": datetime.now().isoformat(timespec="seconds")}
# idle baseline (the machine keeps running its usual background services)
c0, t0 = cpu_busy(), time.perf_counter(); e0 = energy_j(); time.sleep(5)
c1 = cpu_busy(); base = NCPU * (c1[0] - c0[0]) / max(c1[1] - c0[1], 1)
e1 = energy_j(); res["idle_cores"] = round(base, 3)
res["idle_watts"] = round((e1 - e0) / 5, 2) if e0 is not None and e1 is not None else None
IDLE_W = res["idle_watts"]

def pkg_temp():
    """CPU package temperature in C (host thermal zones bind-mounted at /thermal), or None."""
    for z in glob.glob("/thermal/thermal_zone*"):
        try:
            if open(f"{z}/type").read().strip() == "x86_pkg_temp": return int(open(f"{z}/temp").read()) / 1000
        except OSError: pass
    return None


res["cool"] = {"limit_c": A.cool, "pauses": 0, "paused_s": 0.0, "max_c": None}
def cool_down():
    """Pause until the package is 15 C under the limit; latencies are measured only after the pause."""
    c = pkg_temp()
    if c is None: return
    res["cool"]["max_c"] = max(res["cool"]["max_c"] or 0, c)
    if c < A.cool: return
    t = time.time(); res["cool"]["pauses"] += 1
    while (pkg_temp() or 0) >= A.cool - 15: time.sleep(5)
    res["cool"]["paused_s"] += time.time() - t


t0 = time.perf_counter(); run, size_mb, rss_pat = make_runner(); run(rows[0])
res["load_s"] = round(time.perf_counter() - t0, 2); res["model_file_mb"] = size_mb
rss_self = lambda: resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

# 1) single stream
lat, preds = [], []
with Meter(base, rss_pat) as m:
    for r in rows[:A.single]:
        if A.cool: cool_down()
        t = time.perf_counter(); p = run(r); lat.append((time.perf_counter() - t) * 1000); preds.append({"id": r["id"], **p})
n = len(lat)
res["single"] = {"n": n, "median_ms": statistics.median(lat), "p95_ms": pct(lat, .95), "p99_ms": pct(lat, .99),
                 "mean_ms": statistics.mean(lat), "max_ms": max(lat), "cpu_s_per_entry": m.cpu_s / n,
                 "joules_per_entry": (m.energy / n) if m.energy else None, "watts": (m.energy / m.wall) if m.energy else None,
                 "joules_above_idle_per_entry": (m.energy_above_idle / n) if m.energy_above_idle is not None else None}
res["peak_rss_mb"] = round(max(rss_self() if A.system != "ollama" else 0, m.peak_rss), 1)
print("single", json.dumps(res["single"]), flush=True)

# 2) concurrency sweep
res["conc"] = {}
for c in [int(x) for x in A.conc.split(",") if x]:
    lats, sub = [], [rows[i % len(rows)] for i in range(A.per_level)]
    def job(r):
        t = time.perf_counter(); run(r); return (time.perf_counter() - t) * 1000
    with Meter(base, rss_pat) as m, ThreadPoolExecutor(c) as ex:
        lats = list(ex.map(job, sub))
    res["conc"][c] = {"n": len(lats), "throughput_per_s": len(lats) / m.wall, "median_ms": statistics.median(lats),
                      "p95_ms": pct(lats, .95), "p99_ms": pct(lats, .99), "cores_used": m.cpu_s / m.wall,
                      "joules_per_entry": (m.energy / len(lats)) if m.energy else None,
                      "joules_above_idle_per_entry": (m.energy_above_idle / len(lats)) if m.energy_above_idle is not None else None}
    print("conc", c, json.dumps(res["conc"][c]), flush=True)

# 3) sustained back-to-back load (one stream): does latency drift?
if A.sustain:
    trace = []; t_end = time.perf_counter() + A.sustain; i = 0
    with Meter(base, rss_pat) as m:
        while time.perf_counter() < t_end:
            r = rows[i % len(rows)]; i += 1
            t = time.perf_counter(); run(r); trace.append((t - m.t0, (time.perf_counter() - t) * 1000))
    win = 30.0; wins = {}
    for ts, ms in trace: wins.setdefault(int(ts // win), []).append(ms)
    res["sustain"] = {"seconds": A.sustain, "n": len(trace), "throughput_per_s": len(trace) / m.wall,
                      "median_ms": statistics.median([x for _, x in trace]), "p99_ms": pct([x for _, x in trace], .99),
                      "windows_30s_median_ms": [round(statistics.median(v), 2) for k, v in sorted(wins.items())],
                      "cores_used": m.cpu_s / m.wall, "watts": (m.energy / m.wall) if m.energy else None,
                      "first_vs_last_window": None}
    w = res["sustain"]["windows_30s_median_ms"]
    if len(w) > 2: res["sustain"]["first_vs_last_window"] = round(w[-1] / w[0], 3)
    print("sustain", json.dumps({k: v for k, v in res["sustain"].items() if k != "windows_30s_median_ms"}), flush=True)

# 4) per-request CPU spike: isolated requests after 1.5 s of quiet
spikes = []
for r in rows[:A.spike]:
    time.sleep(1.5)
    with Meter(base, rss_pat) as m:
        t = time.perf_counter(); run(r); wall = time.perf_counter() - t
    over = [c for _, c in m.series]
    spikes.append({"wall_ms": wall * 1000, "cpu_s": m.cpu_s, "joules_above_idle": m.energy_above_idle, "peak_cores": max(over, default=0),
                   "above_1core_ms": 10 * sum(1 for c in over if c >= 1.0),
                   "above_half_machine_ms": 10 * sum(1 for c in over if c >= NCPU / 2)})
med = lambda k: statistics.median(s[k] for s in spikes) if spikes else None
res["spike"] = {"n": len(spikes), "wall_ms": med("wall_ms"), "cpu_s": med("cpu_s"),
                "joules_above_idle": statistics.median(s["joules_above_idle"] for s in spikes) if spikes and IDLE_W else None, "peak_cores": med("peak_cores"),
                "above_1core_ms": med("above_1core_ms"), "above_half_machine_ms": med("above_half_machine_ms"),
                "note": "10 ms sampling; spikes shorter than one sample show as 0-10 ms"}
print("spike", json.dumps(res["spike"]), flush=True)
json.dump(res, open(A.out, "w"), indent=1)
with open(A.out.replace(".json", ".preds.jsonl"), "w") as f:
    for p in preds: f.write(json.dumps(p, ensure_ascii=False) + "\n")
