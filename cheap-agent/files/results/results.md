# Results: Cheap Agent vs Claude Code alone, both on DeepSeek (deepseek-flash)
Planner = Claude Code (on DeepSeek's Anthropic endpoint). Implementer = Cheap Agent worker (deepseek preset, deepseek-flash). Takeover "self". Dollars = tokens x DeepSeek list price (peak). Tests = our pytest acceptance run.

| task | run | planner tokens | implementer tokens | cost $ | tests | wall |
|---|---|---|---|---|---|---|
| 1 easy (CLI flag) | alone | 236,433 | 0 | 0.0111 | 8/8 | 53 s |
| 1 easy | plugin | 50,207 | 68,296 | 0.0119 | 9/9 | 97 s |
| 2 medium (CSV, 3 files) | alone | 315,058 | 0 | 0.0152 | 13/13 | 64 s |
| 2 medium | plugin | 90,112 | 124,362 | 0.0185 | 9/9 | 724 s |
| 3 hard (cache bugs) | alone | 550,274 | 0 | 0.0233 | 7/7 | 1,739 s |
| 3 hard | plugin | 90,013 | 88,581 | 0.0134 | 7/7 | 107 s |
| total | alone | 1,101,765 | 0 | 0.0496 | 28/28 | 1,856 s |
| total | plugin | 230,332 | 281,239 | 0.0438 | 25/25 | 928 s |

Direction: planner (main model) tokens fell 79 percent (1.10M to 0.23M), total tokens fell 54 percent; dollars on DeepSeek fell only 12 percent ($0.0496 to $0.0438, differences of a cent or two); easy and medium tasks cost slightly MORE with the plugin, hard task 43 percent less. All tests passed in all six runs.
Caveats: one run per cell; wall time is dominated by DeepSeek API load (same task ranged 53 s to 247 s alone, 97 s to 745 s with plugin across attempts), so no speed claim. The test counts differ because each run adds its own tests. "Alone" runs could not run python from their shell (their summaries say so) but code passed our tests. Opus-price figures are not measured; any must be labelled arithmetic.
No-Claude check (check.py, recorded in tally.mp4): model ids seen deepseek-flash only; 0 connections to Anthropic IPs from the Claude Code process tree in all six runs (per-process psutil sampling every 0.7 s, DeepSeek IP seen); 0 claude/opus/sonnet model strings in the six stream logs; session env: base URL api.deepseek.com/anthropic, all model aliases mapped to deepseek-flash, takeover self.
Setup facts: Git for Windows present; PowerShell blocked npx.ps1 until Set-ExecutionPolicy -Scope Process Bypass (shown); install answered Y to "Add cheapag to Claude Code"; plugin first run about 2 min; opencode.exe killed after each run by exact name. Project health (2026-11-03): created 2026-10-28, 240 stars, 0 open issues, last commit 2026-11-02 (release 1.3.2), 3 contributors, MIT.
Failures shown: run 1 alone first hit a DeepSeek 503 (infrastructure, not a model failure), rerun; no test failure, so the v4-pro fix run was not used.
Recordings (results/recordings): setup, run_t{1,2,3}-{plain,plugin}, tally, doc-what/claim/windows/honest/health/issues/prices (+ .log, timeline .json). Runs 2 plugin and 3 plain/plugin recordings end with idle terminal time (a 20 minute leftover timer in the runner, since fixed): trim to the printed wall time using the "RUN TOTAL" line.
