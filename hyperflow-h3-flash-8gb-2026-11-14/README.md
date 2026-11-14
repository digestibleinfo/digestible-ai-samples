# HyperFlow H3 Flash on an 8 GB GPU: sample pack

Used in the Digestible AI video "HyperFlow H3 Flash on an 8 GB GPU: Built for 24 GB, Tested on 8". The model is [VideoRebirthAI/hyperflow-h3-flash](https://huggingface.co/VideoRebirthAI/hyperflow-h3-flash), a compressed, few-step version of MiniMax H3 (13.7B parameters), released under the MiniMax H3 Community License (read it before use: it lists regions that need prior authorization and a revenue limit). The model files are not in this pack.

**Download:** [hyperflow-h3-samples.zip](https://github.com/digestibleinfo/digestible-ai-samples/raw/main/hyperflow-h3-flash-8gb-2026-11-14/hyperflow-h3-samples.zip). The same files are in [files](files).

## What was tested
Five text-to-video clips, one run each, same seed (42), default settings, 1344x768, 124 frames (5.2 s at 24 fps, with audio), 6 sampling steps, euler. Prompts are in `files/prompts.txt`, the exact ComfyUI API graphs in `files/workflow/`.

## Results
| clip | minutes | first step after (s) | sampling (s) | peak VRAM (GB) | peak RAM (GB) | verdict |
|---|---|---|---|---|---|---|
| 1 cheetah | 8.9 | 119 | 341 | 7.58 | 25.27 | pass |
| 2 woman, red coat | 9.0 | 123 | 344 | 7.70 | 25.25 | pass |
| 3 retriever shakes off water | 8.8 | 114 | 342 | 7.61 | 25.25 | partial |
| 4 chalkboard "OPEN 24 HOURS" | 8.8 | 114 | 342 | 7.62 | 25.24 | partial (OPEN 24 readable, HOURS cropped; OCR not run) |
| 5 birthday candles | 8.8 | 115 | 342 | 7.57 | 25.25 | fail (candles not seen going out) |

Verdicts are my judgement from the frames. Minutes = time from pressing queue to the finished file. The raw VRAM and RAM samples and the click marks are in `files/results/ui_clipN_marks_and_samples.json`.

## Setup used
- GPU: a 16 GB card held to 8 GB. `scripts/lowvram_launch.py 8 32` passes `--reserve-vram 8.5` to ComfyUI (so the models see about 8 GB) and puts the ComfyUI process tree in a Windows Job Object capped at 32 GB of RAM (the PC has 32 GB). So "8 GB" is a software cap on a 16 GB card, not a physical 8 GB card.
- ComfyUI 0.45.0 (portable, fresh install; an older one did not run the model) plus two node packs: ComfyUI-GGUF and ComfyUI-HyperFlow-Flash.
- Files: GGUF `minimax_h3_fl2va_hyperflow_flash_14b-Q3_K_M.gguf` (7.2 GB), text encoder `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` (15.7 GB), video VAE `minimax_h3_video_vae_fp16.safetensors` (5.2 GB), audio VAE `minimax_h3_audio_vae_fp32.safetensors` (0.6 GB). About 29 GB in total, from the model's Hugging Face page and the node pack's instructions.
- No extra ComfyUI flags beyond the cap.

## Rerun it
1. Install ComfyUI (portable), the two node packs and download the four files above into the folders the HyperFlow node pack README names.
2. Start ComfyUI normally (or with the cap: `python scripts/lowvram_launch.py 8 32`, after setting `COMFY_PORTABLE` to your portable folder; it assumes a 16 GB card, see `CARD_GB`).
3. In ComfyUI choose Workflow, Open, and load a graph from `files/workflow/` (API format: use the node pack's template and paste the prompt and seed if your build cannot import API JSON), then press Queue.
4. `scripts/record_h3.py` is the screen-recorder driver I used (Playwright; it needs my recorder helper, so treat it as reference, not a one-command rerun).

## Caveats
- One machine, one seed, one run per clip: times and verdicts will vary. 5 clips is not a benchmark.
- The model page says 24 GB is the smallest GPU the authors tested and that 16 GB is not measured; this is a separate, unofficial test. Base MiniMax H3 was not run, so there is no base comparison.
- Peak RAM is about 25 GB: with less than 32 GB of RAM it may not run.
- The 5 clips are the model's output and carry the same licence terms as the model.

The scripts are provided as-is for learning, under the MIT licence.
