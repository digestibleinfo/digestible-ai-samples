# Inkling 2 Mini on a 16 GB GPU: sample pack

Used in the Digestible AI video "Inkling 2 Mini on a 16 GB GPU: Can It Replace a $20 Claude Plan?". The model is Inkling 2 Mini, run from the [unsloth GGUF](https://huggingface.co/unsloth/Inkling-2-Mini-GGUF) (Mainline_Support branch, file UD-IQ4_XS, 15.73 GB). The model file is not in this pack.

**Download:** [inkling2-mini-samples.zip](https://github.com/digestibleinfo/digestible-ai-samples/raw/main/inkling-2-mini-16gb-2026-11-22/inkling2-mini-samples.zip). The same files are in [files](files).

## What was tested
Three single runs through llama.cpp's server (plus one run each of Claude Haiku in Claude Code on the same two prompts, see below): a load check ("Say hello in one short sentence."), a Flappy Bird game as one HTML file, and "bouncing ball(s) inside a rotating hexagon with gravity and collisions". Exact prompts are in `files/prompts.txt`. VRAM and RAM were sampled about once a second (`samples.csv`).

## Results
Corrected 2026-11-23. An earlier version of this README (and the first upload of the video) said the Inkling Flappy Bird game passes. That was wrong: my first replay script only pressed Space on a fixed rhythm and read the page text, and a canvas game has no page text, so it missed a bug. The table below is the corrected result.

| run | tokens | tok/s | wall time (s) | peak VRAM by the process (GB) | peak RAM (GB, whole PC) | result |
|---|---|---|---|---|---|---|
| load check | 64 cap (short answer) | 38.5 | - | - | - | pass, 49/49 layers on the GPU |
| Flappy Bird | 4,705 | 25.68 | 184 | 14.97 | 34.8 | FAIL: no ceiling check, see below. Pipes scroll, Space works, score counts, but the bird can leave the top of the screen |
| Hexagon | 12,000 (cap hit) | 41.67 | 289 | 14.93 | 34.6 | fail: the HTML was cut off, no rotation |

Peak RAM includes about 16 GB that the PC already used before the test, so the model added about 18 GB.

### Inkling Flappy Bird: why it fails
- `files/results/flappy/flappy.html` has no check for the top edge. `update()` (lines 111-122) only tests the ground (lines 119-122, `bird.y + radius >= GROUND_Y`); nothing clamps or ends the game at the top, and the upward speed on line 115 has no limit.
- The pipe collision (lines 142-143, `circleRectIntersect` at lines 161-167) uses the top pipe from y = 0 down, so a bird above y = -14 touches no pipe.
- Replay with Space every 0.45 s for 30 s (`flappy_flappy_steady.mp4`, `play_flappy_steady.json`): the bird is off screen from 2.3 s, its drawn y reaches -3,504, it passes every pipe, the score keeps rising to 22 and Game Over comes only after the key presses stop and it falls back. A player who flaps only when the bird is low stays on screen and scores 19+ in 30 s (`flappy_flappy_aim.mp4`, `play_flappy_aim.json`). So it is a game bug; the steady input only exposed it.
- The small "bird y" readout and the "OFF SCREEN" label in the clips are a probe I added for the replay (`scripts/play_pages2.py` wraps the canvas calls to log the bird's drawn y and every string drawn). They are not part of the generated page.
- The aiming bot is crude (a simple rule, not a skilled player); do not read its scores as a benchmark.

### Claude Haiku in Claude Code, same two prompts
Command (one run each, no tools, so the HTML comes back as text like the local run; `scripts/run_claude.py`):
`claude -p "<prompt>" --model haiku --effort low --tools "" --output-format json --max-budget-usd 0.50 --no-session-persistence`
The prompts are the same as in `files/prompts.txt`. Raw JSON with usage and cost is in `files/results/claude_haiku_*/raw.json` (session and request IDs removed; the rest is the CLI output). Pages: `claude_haiku_flappy/flappy.html`, `claude_haiku_hexagon/hexagon.html`. Play clips: `files/results/haiku_flappy_play.mp4`, `haiku_hexagon_play.mp4`.

| | Inkling 2 Mini (local, RTX 5060 Ti 16 GB) | Claude Haiku (Claude Code) | Qwen 3.8 27B Q4_0 (earlier video, not re-run) |
|---|---|---|---|
| Flappy: time | 184 s | 11.8 s | - |
| Flappy: output tokens | 4,705 | 3,248 | - |
| Flappy: result | FAIL (no ceiling check) | pass (ceiling clamped at lines 104-107; ground and pipes end the game) | - |
| Flappy: cost | 0 (own electricity) | $0.0019 | - |
| Hexagon: time | 289 s | 29.5 s | - |
| Hexagon: output tokens | 12,000 (cap hit) | 7,503 | - |
| Hexagon: result | FAIL (truncated page, no rotation) | pass (hexagon rotates, 5 balls stay inside and bounce for 14 s) | - |
| Hexagon: cost | 0 | $0.0041 | - |
| Speed | 25.7 to 41.7 tok/s | not measured per token | 3.32 tok/s |
| VRAM | 15.0 GB | none (cloud) | 11.94 GB |

Cost notes. The dollar figures are what Claude Code reports for the tokens used at Anthropic's API list prices (`costBasis: list` in the JSON). The two recorded runs cost $0.0060 together ($0.0019 + $0.0041). There was also one off-camera practice run of the Flappy prompt ($0.0026, kept in `claude_haiku_flappy_unrecorded_run0/`), so everything I spent on Haiku was $0.0086. Claude Pro ($20 a month, $17 billed yearly, source claude.com/pricing, read 2026-11-22) does not show dollars per run and publishes no message count, so I did not run or price the Pro plan itself.

## Setup used
- GPU: NVIDIA RTX 5060 Ti, 16 GB. PC with 32 GB RAM, Windows.
- llama.cpp b12633, `llama-bin-win-cuda-13.5-x64` prebuilt release (plus the cudart zip).
- Model: unsloth `Inkling-2-Mini` UD-IQ4_XS, 15.73 GB.
- Server flags: `-c 16384 -np 1 -ngl 99 -ctk q8_0 -ctv q8_0 --jinja`.
- Sampling: temperature 0.7, top_p 0.8, top_k 20, presence penalty 1.5, seed 1, max 12,000 tokens (64 for the load check).

## Rerun it
1. Download llama.cpp b12633 (CUDA build) into a `llama` folder and the GGUF into `models/` (names as at the top of `files/scripts/run_inkling.py`).
2. `pip install psutil`, then from that folder: `python run_inkling.py check`, then `flappy`, then `hexagon`. It starts the server, samples VRAM and RAM, streams the answer, stops the server and writes `results/<name>/`.
3. `python play_pages2.py <result-folder> <page> flappy_steady|flappy_aim|hexagon` (the honest replay with the canvas probe; `play_pages.py` is the first replay and misses the ceiling bug); `python play_pages.py flappy` (needs Playwright with Chrome and ffmpeg) replays the saved page and records it.
4. Haiku: `python run_claude.py flappy`, then `hexagon` (needs the Claude Code CLI signed in; it spends a few tenths of a cent).

## Caveats
- One machine, one seed, one run per test (Haiku too): speeds and verdicts will vary.
- The model thinks before it answers and those reasoning tokens count toward the cap. The hexagon run used its 12,000 tokens (about 24,000 characters of reasoning plus a truncated page) and ended with finish reason "length". The fail is the cap, not proof the model cannot do it; a rerun with a larger cap was not made.
- Two tests are not a benchmark. Claude Pro limits are not published as a message count, so no per-message comparison is made; price source: claude.com/pricing, read 2026-11-22 ($20/month, $17 on annual billing).
- The generated pages are the model's output. Verdicts are my judgement from replaying the saved pages.

The scripts are provided as-is for learning, under the MIT licence.
