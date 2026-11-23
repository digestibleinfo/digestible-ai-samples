# Inkling 2 Mini on a 16 GB GPU: sample pack

Used in the Digestible AI video "Inkling 2 Mini on a 16 GB GPU: Can It Replace a $20 Claude Plan?". The model is Inkling 2 Mini, run from the [unsloth GGUF](https://huggingface.co/unsloth/Inkling-2-Mini-GGUF) (Mainline_Support branch, file UD-IQ4_XS, 15.73 GB). The model file is not in this pack.

**Download:** [inkling2-mini-samples.zip](https://github.com/digestibleinfo/digestible-ai-samples/raw/main/inkling-2-mini-16gb-2026-11-22/inkling2-mini-samples.zip). The same files are in [files](files).

## What was tested
Three single runs through llama.cpp's server: a load check ("Say hello in one short sentence."), a Flappy Bird game as one HTML file, and "bouncing ball(s) inside a rotating hexagon with gravity and collisions". Exact prompts are in `files/prompts.txt`. VRAM and RAM were sampled about once a second (`samples.csv`).

## Results
| run | tokens | tok/s | wall time (s) | peak VRAM by the process (GB) | peak RAM (GB, whole PC) | result |
|---|---|---|---|---|---|---|
| load check | 64 cap (short answer) | 38.5 | - | - | - | pass, 49/49 layers on the GPU |
| Flappy Bird | 4,705 | 25.68 | 184 | 14.97 | 34.8 | pass: pipes scroll, score counts 0 to 20, Game Over shows the score |
| Hexagon | 12,000 (cap hit) | 41.67 | 289 | 14.93 | 34.6 | fail: the HTML was cut off, no rotation |

Verdicts are my judgement from playing the saved pages (`files/results/*/ *.html`, `*_play.mp4`). Peak RAM includes about 16 GB that the PC already used before the test, so the model added about 18 GB. Reference from an earlier video, not re-run here: Qwen 3.8 27B Q4_0 on the same card ran at 3.32 tok/s.

## Setup used
- GPU: NVIDIA RTX 5060 Ti, 16 GB. PC with 32 GB RAM, Windows.
- llama.cpp b12633, `llama-bin-win-cuda-13.5-x64` prebuilt release (plus the cudart zip).
- Model: unsloth `Inkling-2-Mini` UD-IQ4_XS, 15.73 GB.
- Server flags: `-c 16384 -np 1 -ngl 99 -ctk q8_0 -ctv q8_0 --jinja`.
- Sampling: temperature 0.7, top_p 0.8, top_k 20, presence penalty 1.5, seed 1, max 12,000 tokens (64 for the load check).

## Rerun it
1. Download llama.cpp b12633 (CUDA build) into a `llama` folder and the GGUF into `models/` (names as at the top of `files/scripts/run_inkling.py`).
2. `pip install psutil`, then from that folder: `python run_inkling.py check`, then `flappy`, then `hexagon`. It starts the server, samples VRAM and RAM, streams the answer, stops the server and writes `results/<name>/`.
3. `python play_pages.py flappy` (needs Playwright with Chrome and ffmpeg) replays the saved page and records it.

## Caveats
- One machine, one seed, one run per test: speeds and verdicts will vary.
- The model thinks before it answers and those reasoning tokens count toward the cap. The hexagon run used its 12,000 tokens (about 24,000 characters of reasoning plus a truncated page) and ended with finish reason "length". The fail is the cap, not proof the model cannot do it; a rerun with a larger cap was not made.
- Two tests are not a benchmark. Claude Pro limits are not published as a message count, so no per-message comparison is made; price source: claude.com/pricing, read 2026-11-22 ($20/month, $17 on annual billing).
- The generated pages are the model's output.

The scripts are provided as-is for learning, under the MIT licence.
