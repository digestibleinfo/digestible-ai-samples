import json, os, re, shutil, subprocess, sys, threading, time, socket
from pathlib import Path
W = Path(os.environ["CHEAP_WORK"])   # your work folder: base/ (the project), accept/, bin/ (claude), venv/, prices.json
RES = Path(os.environ.get("CHEAP_RESULTS", "results"))
PR = json.load(open(W/"prices.json"))["deepseek-flash"]
PROMPTS = {
 "1": "In this repo add a --sort flag to shop/cli.py (python -m shop.cli ITEMS.json --sort name|price sorts ascending, and --reverse flips the order) and add a test for it in tests/. Run the tests.",
 "2": "Add CSV export. New module shop/export.py with to_csv(items) returning a string: header name,category,price,stock and price in dollars with 2 decimals (150 becomes 1.50). Add Store.filter(category=None, in_stock=False) returning the filtered items. In shop/cli.py add --csv PATH that writes the items selected by --category/--in-stock to that file using these two. Add tests in tests/. Run the tests.",
 "3": "tests/test_cache.py has failing tests. Find and fix the bugs in the code (not in the tests). Run the tests until they all pass.",
}
import builtins
_p = builtins.print
def print(*a, **k):
    _p(*[re.sub(r"[A-Za-z]:[\\/][^\s\"']*", "<dir>", x) if isinstance(x, str) else x for x in a], **k)
task, mode = sys.argv[1], sys.argv[2]   # mode: plain | plugin
tag = f"t{task}-{mode}"
d = W/"work"/tag
if d.exists(): d.rename(d.with_name(d.name + "-old" + str(int(time.time()))))
shutil.copytree(W/"base", d, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
env = dict(os.environ)
env["PATH"] = f"{W/'bin'};{W/'venv'/'Scripts'};" + env["PATH"]
env.update(CLAUDE_CONFIG_DIR=str(W/("claude-home" if mode == "plugin" else "claude-home-plain")),
  ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic", ANTHROPIC_MODEL="deepseek-flash",
  ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-flash", ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-flash",
  ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-flash", ANTHROPIC_SMALL_FAST_MODEL="deepseek-flash",
  CLAUDE_CODE_SUBAGENT_MODEL="deepseek-flash", CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1", PYTHONIOENCODING="utf-8")
key = os.environ["DEEPSEEK_API_KEY"]
env["ANTHROPIC_AUTH_TOKEN"] = key
if task in "12": (d/"tests"/"test_cache.py").unlink()
os.chdir(d)
print(f"task {task} / {'with Cheap Agent' if mode=='plugin' else 'Claude Code alone'}", flush=True)
if mode == "plugin":
    json.dump({"takeover": "self", "test_cmd": "python -m pytest -q"}, open("cheapag.json", "w"))
    r = subprocess.run("npx.cmd -y cheap-agent allow", shell=True, env=env, capture_output=True, text=True)
    print("allowed:", (r.stdout.strip().splitlines() or ["?"])[-1][:100], "| takeover: self", flush=True)
subprocess.run("git add -A & git -c user.email=a@b -c user.name=d commit -qm cfg", shell=True, env=env, capture_output=True)
ips = set()
for h in ("api.anthropic.com", "console.anthropic.com", "statsig.anthropic.com"):
    try: ips |= {x[4][0] for x in socket.getaddrinfo(h, 443)}
    except Exception: pass
seen, bad, stop = set(), set(), False
import psutil
root = [None]
ds_ips = set()
for h in ("api.deepseek.com",):
    try: ds_ips |= {x[4][0] for x in socket.getaddrinfo(h, 443)}
    except Exception: pass
ds_seen = set()
def net():
    # only connections owned by this run's Claude Code process tree (and the cheap-model engine it starts)
    while not stop:
        if root[0]:
            try:
                tree = {root[0]} | {c.pid for c in psutil.Process(root[0]).children(recursive=True)}
                tree |= {q.pid for q in psutil.process_iter(["name"]) if (q.info["name"] or "").lower().startswith("opencode")}
                for c in psutil.net_connections(kind="tcp"):
                    if c.pid in tree and c.raddr:
                        seen.add(c.raddr.ip)
                        if c.raddr.ip in ips: bad.add(c.raddr.ip)
                        if c.raddr.ip in ds_ips: ds_seen.add(c.raddr.ip)
            except Exception: pass
        time.sleep(0.7)
threading.Thread(target=net, daemon=True).start()
t0 = time.time()
cmd = [str(W/"bin"/"claude.exe"), "-p", PROMPTS[task], "--output-format", "stream-json", "--verbose", "--permission-mode", "acceptEdits", "--allowedTools", "Read,Edit,Write,Glob,Grep,Bash(python:*),Bash(git:*),Bash(pytest:*),Bash(ls:*),Bash(cat:*),mcp__cheapag", "--max-turns", "40"]
p = subprocess.Popen(cmd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
root[0] = p.pid
final, models, calls = None, set(), 0
timed_out = [False]; ids = {}
def _kill():
    timed_out[0] = True
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
_tm = threading.Timer(1200, _kill); _tm.daemon = True; _tm.start()
log = open(RES/f"stream_{tag}.jsonl", "w", encoding="utf-8")
for line in p.stdout:
    log.write(line)
    try: e = json.loads(line)
    except Exception: continue
    if e.get("type") == "assistant":
        m = e["message"]; models.add(m.get("model", "?")); ids[m.get("id", str(calls))] = m.get("usage") or {}
        for c in m["content"]:
            if c["type"] == "tool_use":
                calls += 1
                i = c["input"]; a = i.get("file_path") or i.get("command") or i.get("path") or i.get("description") or ""
                a = str(a).replace(str(d), ".").replace(str(d).replace(chr(92), "/"), ".")
                print(f"  {int(time.time()-t0):>4}s  {c['name'].replace('mcp__cheapag__','cheapag:')} {str(a)[:70]}".replace("\n", " "), flush=True)
    elif e.get("type") == "user" and isinstance(e["message"].get("content"), list):
        for c in e["message"]["content"]:
            if c.get("type") == "tool_result" and calls:
                t = c.get("content"); t = t if isinstance(t, str) else " ".join(x.get("text", "") for x in t)
                if "cheapag" in t.lower()[:300] or t.startswith(("DONE","FAIL","PARTIAL")): print("        ->", t.replace(chr(10), " ")[:110].replace(str(d), "."), flush=True)
    elif e.get("type") == "result":
        final = e
p.wait(); wall = time.time() - t0; stop = True
os.system("taskkill /F /IM opencode.exe >nul 2>&1")
if final is None:
    tot = {k: sum(x.get(k, 0) or 0 for x in ids.values()) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")}
    final = {"usage": tot, "result": "no result: stopped after 20 minutes (hung)"}
u = final["usage"]
miss = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0); hit = u.get("cache_read_input_tokens", 0); out = u.get("output_tokens", 0)
plan_usd = (miss*PR["miss"] + hit*PR["hit"] + out*PR["out"]) / 1e6
if task in "12":
    shutil.copy(W/"accept"/f"accept{task}.py", d/"tests"/"test_accept.py")
t = subprocess.run("python -m pytest -q -p no:cacheprovider", shell=True, env=env, capture_output=True, text=True)
last = t.stdout.strip().splitlines()[-1] if t.stdout.strip() else "no output"
import re
npass = int((re.search(r"(\d+) passed", last) or [0, 0])[1]); nfail = int((re.search(r"(\d+) failed", last) or [0, 0])[1])
im = io_ = ic = 0; njobs = 0
for rj in (d/".cheapag"/"jobs").glob("*/result.json") if (d/".cheapag").exists() else []:
    uu = json.load(open(rj)).get("usage") or {}
    im += uu.get("inputTokens", 0); io_ += uu.get("outputTokens", 0) + uu.get("reasoningTokens", 0); ic += uu.get("cacheRead", 0); njobs += 1
impl_usd = (im*PR["miss"] + ic*PR["hit"] + io_*PR["out"]) / 1e6
res = dict(timed_out=timed_out[0], impl_input_miss=im, impl_cache_read=ic, impl_output=io_, impl_usd=round(impl_usd, 4), worker_jobs=njobs, total_usd=round(plan_usd+impl_usd, 4), final_text=(final.get('result') or '')[:600], task=task, mode=mode, planner_input_miss=miss, planner_cache_read=hit, planner_output=out, planner_usd=round(plan_usd, 4),
  tests_passed=npass, tests_failed=nfail, wall_s=round(wall), tool_calls=calls, models_seen=sorted(models),
  claude_model_names=[m for m in models if "claude" in m.lower() or "opus" in m.lower() or "sonnet" in m.lower()],
  anthropic_ips_resolved=len(ips), anthropic_connections=sorted(bad), deepseek_connection_ips=len(ds_seen), remote_hosts_seen=len(seen), pytest_last=last,
  modelUsage=final.get("modelUsage"), cheapag_files=[str(x.relative_to(d)) for x in (d/".cheapag").rglob("*") if x.is_file()] if (d/".cheapag").exists() else [])
(RES/f"run_{tag}.json").write_text(json.dumps(res, indent=1))
print(f"\nplanner tokens: {miss+hit+out:,} (new in {miss:,}, cached {hit:,}, out {out:,})  planner ${plan_usd:.4f}")
print(f"implementer tokens: {im+ic+io_:,} (new in {im:,}, cached {ic:,}, out {io_:,})  implementer ${impl_usd:.4f}")
print(f"RUN TOTAL ${plan_usd+impl_usd:.4f}")
print(f"tests: {last}   wall: {int(wall//60)}m{int(wall%60):02d}s")
print(f"models: {', '.join(sorted(models))}   Anthropic connections: {len(bad)}   DeepSeek: {len(ds_seen)}")
