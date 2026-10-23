"""Runs forge's own eval harness on its 26 non-compaction scenarios and prints one scoreboard.
Run it from inside forge-main, with llama-server already running on port 8080.

    python score.py <model.gguf> bare 3        (all guardrails off, 3 runs per scenario)
    python score.py <model.gguf> reforged 3    (forge's guardrails on: the default)

bare and reforged are forge's own ablation presets (docs/EVAL_GUIDE.md). A scenario run counts as
right when forge's harness scores it right; this script only adds the runs up.
"""

import re
import subprocess
import sys
import time

OG18 = ["basic_2step", "sequential_3step", "error_recovery", "tool_selection", "argument_fidelity", "sequential_reasoning",
        "conditional_routing", "data_gap_recovery", "relevance_detection"]
OG18 += [s + "_stateful" for s in OG18]
HARD = ["data_gap_recovery_extended", "argument_transformation", "inconsistent_api_recovery", "grounded_synthesis"]
HARD += [s + "_stateful" for s in HARD]

gguf, ablation, runs = sys.argv[1], sys.argv[2], sys.argv[3]
start = time.time()
out = subprocess.run([sys.executable, "-m", "tests.eval.eval_runner", "--backend", "llamafile", "--llamafile-mode", "native",
                      "--gguf", gguf, "--runs", runs, "--ablation", ablation, "--scenario", *OG18, *HARD],
                     capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
secs = time.time() - start

scores = {}
for name, right, total in re.findall(r"---\s+(\S+) \([^)]*\)\s+-+.*?Score:\s+(\d+)/(\d+)", out, re.S):
    scores[name] = (int(right), int(total))
missing = [s for s in OG18 + HARD if s not in scores]
if missing:
    print("no score found for:", ", ".join(missing))


def total(names):
    r = sum(scores[s][0] for s in names if s in scores)
    t = sum(scores[s][1] for s in names if s in scores)
    return r, t


print(f"ablation {ablation}, {runs} runs per scenario, {secs / 60:.1f} minutes")
for label, names in (("OG-18 (baseline tier)", OG18), ("advanced reasoning (hard tier)", HARD)):
    r, t = total(names)
    print(f"  {label:32} {r:3} of {t:3} right ({r / max(1, t):.0%})")
r, t = total(OG18 + HARD)
print(f"  {'ALL 26 SCENARIOS':32} {r:3} of {t:3} right ({r / max(1, t):.0%})")
worst = sorted((v[0] / v[1], k) for k, v in scores.items())[:4]
print("  weakest:", ", ".join(f"{k} {scores[k][0]}/{scores[k][1]}" for _, k in worst))
