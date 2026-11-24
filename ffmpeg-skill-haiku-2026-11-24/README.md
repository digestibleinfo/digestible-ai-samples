# ffmpeg-skill on Claude Code Haiku: sample pack

Used in the Digestible AI video "Claude Code Edits My Video on Haiku: What Does One Edit Really Cost?". The tool is [ffmpeg-skill](https://github.com/kajisho5/ffmpeg-skill) (42 FFmpeg tools as an Agent Skill, MIT), installed project-local with `npx ffmpeg-skill --project`. Claude Code ran headless (`claude -p`) on the Haiku model.

**Download:** [ffmpeg-skill-samples.zip](https://github.com/digestibleinfo/digestible-ai-samples/raw/main/ffmpeg-skill-haiku-2026-11-24/ffmpeg-skill-samples.zip). The same files are in [files](files).

## What was tested
Three edits, one run each, no retries, on our own 62 s source clip (`files/source/source.mp4`): our own synthetic narration (14 sentences, 186 words) over our own screen recording, with 6 pauses we inserted (1.0, 1.2, 1.5, 1.5, 2.0, 2.0 s). It is not camera footage. The ground truth (sentence times, pauses) is in `files/source/truth.json`. The exact prompts and flags are in `files/source/prompts.txt`. Every output was judged by our own script (`files/scripts/check.py`: ffprobe, ffmpeg silencedetect, faster-whisper plus word error rate, sampled frames), never by the agent's own claim.

## Results (cost = `total_cost_usd` reported by Claude Code, list price basis)
| job | prompt | cost | wall time | turns | result |
|---|---|---|---|---|---|
| 1 | cut pauses of 0.5 s or more | 0.80 cents | 28 s | 6 | PASS: 0 silences left, 1 of 186 words differs (same as the untouched clip) |
| 2 | captions with faster-whisper | 1.64 cents | 126 s | 17 | PASS: 14 cues, worst start offset 0.073 s. The skill's own transcribe step failed on this PC (PyAV rejected an option); Haiku wrote its own script |
| 3 | 9:16 Short with a 2 s title card | 1.04 cents | 56 s | 8 | FAIL: the title was drawn over the first 2 s instead of a 2 s card (length 62.0 s, expected 64.0 s), the title sits about 20 px from the top, and the centre crop keeps 32% of the width so the screen text is cut mid-word |

Total of the three counted runs: 3.48 cents. All spend for the video is about 4 cents: add a 0.25 cent preflight and 0.62 cents for an earlier blocked attempt (see below), plus one aborted job-2 attempt whose cost was not readable (under the 30 cent cap per job).

Haiku 5.5 price read on 2026-11-24: $0.10 per million input tokens, $0.50 per million output tokens (prompts up to 100,000 tokens), cache read $0.01. Check the current page before you reuse the numbers.

## Files
- `files/source/`: `source.mp4` and its sha256, `truth.json`, `prompts.txt`, `build_audio.py`, `build_video.py`, `page.html` (the screen recording's page).
- `files/results/jobN/run*.json`: the Claude Code JSON result of each run (tokens, cost, turns, permission denials, the agent's final message). Session id and local paths removed.
- `files/results/jobN/check*.json`: our checker's output. `baseline_check_on_source.json`: the same checks on the untouched clip.
- `files/outputs/`: `cut.mp4`, `captions.srt`, `short.mp4` as the agent made them.
- `files/scripts/check.py`: the checker.

## Setup used
Windows 11 PC, Claude Code 2.1.331, flags `--model haiku --output-format json --max-budget-usd 0.30 --setting-sources project --allowedTools "Bash,PowerShell,Read,Write,Skill"`. The skill was installed into an empty project folder, not into the user-level skills folder, and uninstalled afterwards. Windows has no `python3`, so job 1's frozen prompt says "use `python`".

## Rerun
Install the skill in an empty folder (`npx ffmpeg-skill --project`), copy `source/source.mp4` in, run each prompt from `source/prompts.txt` with the flags above, then `python scripts/check.py job1 <project_folder> <source_folder> <out.json>` (needs ffmpeg and ffprobe on PATH and a venv with `faster-whisper` and `jiwer`).

## Caveats
- One run each. A second run can come out differently, better or worse; the results are not an average.
- Our own clip of about one minute with synthetic voice. A long camera video will cost more and I did not measure it.
- Only Haiku was run; no bigger Claude model.
- An earlier first attempt used a tool list without PowerShell: Haiku's PowerShell calls were refused, job 1 produced nothing (0.62 cents). That was our flag mistake, not the model's; the three counted runs are the re-runs with PowerShell allowed. The first job-2 attempt was aborted by us.
- The cost is what Claude Code reports at list price; it is not a bill from a plan. The speech model download (141 MB, faster-whisper base) is setup on the PC, not Haiku's cost.