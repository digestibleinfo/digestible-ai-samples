"""One recorded run for the inkling-2-mini-16gb trial (stage 3b). Run from the work folder (relative paths only):

    python run_inkling.py check|flappy|hexagon [ngl]

Starts llama-server (pinned build b12633, UD-IQ4_XS), samples VRAM/RAM, streams one chat completion, prints a
live status line, stops the server by its own PID and writes results/<name>/run.json, server.log, response text
and the saved HTML.
"""
import json, re, statistics, subprocess, sys, threading, time, urllib.request
from pathlib import Path
import psutil

MODEL = r"models\Inkling-2-Mini-UD-IQ4_XS.gguf"
SERVER = r"llama\llama-server.exe"
PORT = 8082
VRAM_TOTAL_GB = 16.0
PROMPTS = {
    "check": "Say hello in one short sentence.",
    "flappy": ("Write one complete Flappy Bird game as a single HTML file, with no external files. Use HTML, CSS and "
               "JavaScript on a canvas. Space or a click makes the bird jump. Pipes scroll left. Each pipe passed adds 1 "
               "to the score on screen. The game ends on a collision with a pipe or the ground and shows 'Game Over' and "
               "the score. Output only the HTML file."),
    "hexagon": "Bouncing ball(s) inside a rotating hexagon with gravity and collisions.",
}
name = sys.argv[1]
ngl = sys.argv[2] if len(sys.argv) > 2 else "99"
max_tokens = 64 if name == "check" else 12000
out = Path("results") / name
out.mkdir(parents=True, exist_ok=True)
samples, stop = [], threading.Event()
t0 = time.time()


def gpu_mib():
    r = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                       capture_output=True, text=True)
    return float(r.stdout.strip().splitlines()[0])


def sampler():
    with open(out / "samples.csv", "w", encoding="utf-8") as f:
        f.write("t_s,gpu_used_mib,ram_used_gb\n")
        while not stop.is_set():
            g, r = gpu_mib(), psutil.virtual_memory().used / 1e9
            samples.append((time.time() - t0, g, r))
            f.write(f"{time.time() - t0:.1f},{g},{r:.2f}\n")
            f.flush()
            time.sleep(0.9)


base = statistics.median([gpu_mib() for _ in range(5)])
ram_base = psutil.virtual_memory().used / 1e9
threading.Thread(target=sampler, daemon=True).start()
log = open(out / "server.log", "w", encoding="utf-8")
args = [SERVER, "-m", MODEL, "--host", "127.0.0.1", "--port", str(PORT), "-c", "16384", "-np", "1",
        "-ngl", ngl, "-ctk", "q8_0", "-ctv", "q8_0", "--jinja", "-lv", "4"]
print("$ llama-server (build b12633) -m Inkling-2-Mini-UD-IQ4_XS.gguf -ngl", ngl, "-c 16384", flush=True)
srv = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT)
t_load = time.time()
ready = False
while time.time() - t_load < 900 and srv.poll() is None:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=5) as r:
            if r.status == 200:
                ready = True
                break
    except Exception:
        pass
    time.sleep(2)
load_s = time.time() - t_load
print(f"server ready: {ready} after {load_s:.0f} s", flush=True)


def vram_gb():
    return (samples[-1][1] - base) / 1024 if samples else 0


err, text, reasoning, ntok, timings, finish = None, "", "", 0, {}, None
t_gen = time.time()
if ready:
    body = {"messages": [{"role": "user", "content": PROMPTS[name]}], "max_tokens": max_tokens, "temperature": 0.7,
            "top_p": 0.8, "top_k": 20, "presence_penalty": 1.5, "seed": 1, "stream": True}
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{PORT}/v1/chat/completions", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        last = 0.0
        with urllib.request.urlopen(req, timeout=7200) as r:
            for raw in r:
                raw = raw.decode("utf-8", "replace").strip()
                if not raw.startswith("data:") or raw.endswith("[DONE]"):
                    continue
                ch = json.loads(raw[5:])
                if ch.get("timings"):
                    timings = ch["timings"]
                for c in ch.get("choices", []):
                    d = c.get("delta", {})
                    if d.get("content"):
                        text += d["content"]; ntok += 1
                    if d.get("reasoning_content"):
                        reasoning += d["reasoning_content"]; ntok += 1
                    finish = c.get("finish_reason") or finish
                if time.time() - last > 10:
                    last = time.time()
                    el = last - t_gen
                    print(f"[{el:5.0f}s] tokens {ntok:5d} | {ntok / max(el, 1):.2f} tok/s | VRAM {vram_gb():.1f}/"
                          f"{VRAM_TOTAL_GB:.0f} GB | RAM {samples[-1][2]:.1f} GB", flush=True)
    except Exception as e:
        err = f"request failed: {e!r}"
else:
    err = "server did not become ready (see server.log)"
gen_s = time.time() - t_gen
srv.terminate()
try:
    srv.wait(timeout=60)
except subprocess.TimeoutExpired:
    srv.kill()
log.close()
time.sleep(2)
stop.set()
txt = open(out / "server.log", encoding="utf-8", errors="replace").read()
off = re.findall(r"offloaded (\d+)/(\d+) layers to GPU", txt)
m = re.search(r"```(?:html)?\s*\n(.*?)```", text, re.S)
html = (m.group(1) if m else text).strip()
html_ok = "<html" in html.lower() or "<canvas" in html.lower()
if html_ok:
    (out / f"{name}.html").write_text(html, encoding="utf-8")
(out / "response.txt").write_text(text, encoding="utf-8")
if reasoning:
    (out / "reasoning.txt").write_text(reasoning, encoding="utf-8")
peak_g = max(g for _, g, _ in samples)
run = {"name": name, "build": "llama.cpp b12633 win-cuda-13.5", "model": "Inkling-2-Mini UD-IQ4_XS (unsloth Mainline_Support)",
       "ngl_arg": ngl, "layers_on_gpu": f"{off[-1][0]}/{off[-1][1]}" if off else None, "load_s": round(load_s, 1),
       "gen_s": round(gen_s, 1), "stream_chunks": ntok, "completion_tokens": timings.get("predicted_n"),
       "tokens_per_s": round(timings["predicted_per_second"], 2) if timings.get("predicted_per_second") else None,
       "prompt_tokens": timings.get("prompt_n"), "finish_reason": finish,
       "gpu_baseline_gb": round(base / 1024, 2), "peak_gpu_total_gb": round(peak_g / 1024, 2),
       "peak_vram_process_gb": round((peak_g - base) / 1024, 2), "ram_baseline_gb": round(ram_base, 2),
       "peak_ram_gb": round(max(r for _, _, r in samples), 2), "html_saved": html_ok, "reasoning_chars": len(reasoning),
       "error": err, "settings": {"ctx": 16384, "kv": "q8_0/q8_0", "temperature": 0.7, "top_p": 0.8, "top_k": 20,
                                  "presence_penalty": 1.5, "seed": 1, "max_tokens": max_tokens}, "prompt": PROMPTS[name]}
(out / "run.json").write_text(json.dumps(run, indent=1), encoding="utf-8")
print("RESULT", json.dumps({k: run[k] for k in ["layers_on_gpu", "completion_tokens", "tokens_per_s", "gen_s",
                                                  "peak_vram_process_gb", "peak_ram_gb", "html_saved", "finish_reason", "error"]}), flush=True)

