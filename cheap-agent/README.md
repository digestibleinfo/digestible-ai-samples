# Cheap Agent vs Claude Code alone: sample pack

Used in the Digestible AI videos about the Cheap Agent plugin ([muaaz9329/cheap-ag](https://github.com/muaaz9329/cheap-ag), MIT licence).

**Download:** [cheap-agent-samples.zip](https://github.com/digestibleinfo/digestible-ai-samples/raw/main/cheap-agent/cheap-agent-samples.zip). Save it into the folder you made in the video, then unpack it with
`tar -xf cheap-agent-samples.zip` in Command Prompt. The same files are in [files](files).

## What was tested
Three coding jobs on a small Python shop project (`project/`, pytest), each run twice, six runs in all:

1. Easy: add a `--sort` / `--reverse` flag to the CLI and a test.
2. Medium: add CSV export (new module, a filter method, a `--csv` flag, tests) across 3 files.
3. Hard: fix planted bugs in the cache layer until `tests/test_cache.py` passes.

"Alone" = Claude Code by itself. "Plugin" = the same prompt with Cheap Agent: the main model plans, the plugin's `deepseek` preset (deepseek-flash through OpenCode) writes the code, takeover set to `self` in `cheapag.json` so no Claude model is called when the worker fails.
Both roles ran on DeepSeek: Claude Code was pointed at DeepSeek's Anthropic-compatible endpoint (`https://api.deepseek.com/anthropic`) and every model alias was mapped to `deepseek-flash`. Nothing was billed by Anthropic. `scripts/check.py` is the per-process network check that counted connections to Anthropic addresses from the Claude Code process tree (0 in all six runs).

## Results
Dollars = tokens x DeepSeek list price (peak). Tests = our own pytest acceptance run.

| task | run | planner tokens | worker tokens | cost $ | tests | wall |
|---|---|---|---|---|---|---|
| 1 easy | alone | 236,433 | 0 | 0.0111 | 8/8 | 53 s |
| 1 easy | plugin | 50,207 | 68,296 | 0.0119 | 9/9 | 97 s |
| 2 medium | alone | 315,058 | 0 | 0.0152 | 13/13 | 64 s |
| 2 medium | plugin | 90,112 | 124,362 | 0.0185 | 9/9 | 724 s |
| 3 hard | alone | 550,274 | 0 | 0.0233 | 7/7 | 1,739 s |
| 3 hard | plugin | 90,013 | 88,581 | 0.0134 | 7/7 | 107 s |
| total | alone | 1,101,765 | 0 | 0.0496 | 28/28 | 1,856 s |
| total | plugin | 230,332 | 281,239 | 0.0438 | 25/25 | 928 s |

Planner tokens fell 79 percent, total tokens 54 percent, dollars only 12 percent (a cent or two). The plugin cost slightly more on the easy and medium jobs and 43 percent less on the hard one.

## Caveats
- One run per cell. Test counts differ because each run adds its own tests.
- Wall time depends mostly on DeepSeek API load (the same task ranged from 53 s to 247 s alone), so no speed claim.
- Dollars use DeepSeek list prices at the peak rate. The README of the tool quotes savings on Claude Opus; those figures were not reproduced here, and anything in Opus prices would be arithmetic, not a measurement.
- Raw stream logs of the runs are not included.

## Rerun it on Windows
1. Install Git for Windows, Python 3 and Node.js, and Claude Code. `pip install pytest psutil`.
2. In PowerShell: `Set-ExecutionPolicy -Scope Process Bypass -Force` (otherwise `npx` is blocked), then `npx cheap-agent`, answer Y to "Add cheapag to Claude Code", and log in with your DeepSeek key (`npx cheap-agent login`).
3. Make a work folder and set `CHEAP_WORK` to it. Copy `project/` to `base/` and `acceptance/` to `accept/` in it (put `prices.json` there too), and put `claude.exe` in `bin/`. Set `CHEAP_RESULTS` to a results folder. Set `DEEPSEEK_API_KEY` to your key.
4. `python scripts/run.py 1 plain`, then `python scripts/run.py 1 plugin`, and the same for 2 and 3. Tasks 1 and 2 remove `tests/test_cache.py` first; task 3 keeps it. `python scripts/table.py` builds the table.

Files: `results/` has results.json, results.md and cost_tally.md (with the price table). Each run costs a cent or two.

All names and data in the project are made up. The scripts are provided as-is for learning, under the MIT licence.
