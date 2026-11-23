"""One Claude Code run (Haiku, lowest effort, no tools) for the inkling trial comparison.

    python run_claude.py flappy|hexagon

Same frozen prompts as run_inkling.py. Runs `claude -p --model haiku --effort low --tools ""` (no tools, so the HTML
comes back as text, like the local run), cap $0.50, one try. Saves results/claude_haiku_<name>/ with the html, the raw
json (usage, cost) and run.json.
"""
import glob, json, os, re, subprocess, sys, time
from pathlib import Path

PROMPTS = {
    "flappy": ("Write one complete Flappy Bird game as a single HTML file, with no external files. Use HTML, CSS and "
               "JavaScript on a canvas. Space or a click makes the bird jump. Pipes scroll left. Each pipe passed adds 1 "
               "to the score on screen. The game ends on a collision with a pipe or the ground and shows 'Game Over' and "
               "the score. Output only the HTML file."),
    "hexagon": "Bouncing ball(s) inside a rotating hexagon with gravity and collisions.",
}
name = sys.argv[1]
exe = "claude"  # the Claude Code CLI on PATH
out = Path("results") / f"claude_haiku_{name}"
out.mkdir(parents=True, exist_ok=True)
print(f"Claude Code, model haiku, effort low, no tools, one try. Prompt: {PROMPTS[name][:70]}...", flush=True)
t0 = time.time()
r = subprocess.run([exe, "-p", PROMPTS[name], "--model", "haiku", "--effort", "low", "--tools", "",
                    "--output-format", "json", "--max-budget-usd", "0.50", "--no-session-persistence"],
                   capture_output=True, text=True, encoding="utf-8")
wall = time.time() - t0
(out / "raw.json").write_text(r.stdout, encoding="utf-8")
try:
    j = json.loads(r.stdout)
except Exception:
    print("no json", r.stderr[:300]); sys.exit(1)
text = j.get("result", "")
(out / "response.txt").write_text(text, encoding="utf-8")
m = re.search(r"```(?:html)?\s*(.*?)```", text, re.S)
html = (m.group(1) if m else text).strip()
(out / f"{name}.html").write_text(html, encoding="utf-8")
u = j.get("usage", {})
info = {"model": "haiku (Claude Code)", "wall_s": round(wall, 1), "api_ms": j.get("duration_api_ms"),
        "cost_usd": j.get("total_cost_usd"), "input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"),
        "cache_read": u.get("cache_read_input_tokens"), "cache_create": u.get("cache_creation_input_tokens"),
        "modelUsage": j.get("modelUsage"), "html_chars": len(html), "turns": j.get("num_turns"), "is_error": j.get("is_error")}
(out / "run.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
print(f"done in {wall:.0f} s | output tokens {info['output_tokens']} | cost ${info['cost_usd']} | html {len(html)} chars")
