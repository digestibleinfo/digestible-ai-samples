# ComfyUI LOW VRAM: FLUX 3 Klein GGUF

The workflow and the memory-limit launcher from the Digestible AI video on running FLUX 3 Klein from
[unsloth's GGUF files](https://huggingface.co/unsloth/flux-3-image-klein-GGUF) on a limited graphics card. Tested on
Windows 11 with portable ComfyUI v0.42.1 on an NVIDIA RTX 5060 Ti (16 GB), limited to 4, 8 and 12 GB of VRAM and 32 GB of RAM.

| File | What it does |
|---|---|
| `flux3-klein-gguf-workflow.json` | Unet Loader (GGUF), Load CLIP (the Qwen3-VL text encoder), Load VAE, two CLIP Text Encode nodes, Empty Flux 2 Latent (1024x1024), ModelSamplingFlux (shift 2.77259, never changed), KSampler (steps 4, 8 or 16, cfg 1, euler, simple), VAE Decode, Save Image. Pick the GGUF file in the loader and change only the steps. |
| `lowvram_launch.py` | Starts ComfyUI with a VRAM limit and a RAM limit: `python lowvram_launch.py <VRAM GB> <RAM GB>`. VRAM: it passes ComfyUI's `--reserve-vram` (card size minus the tier, plus 0.5 GB for ComfyUI's own overhead). RAM: it puts ComfyUI in a Windows Job Object with a memory cap. Edit `PORTABLE` and `CARD_GB` at the top for your PC. |

## Files

| Folder (inside `ComfyUI_windows_portable\ComfyUI\models`) | File | Size |
|---|---|---|
| `unet` | the GGUF files from [unsloth/flux-3-image-klein-GGUF](https://huggingface.co/unsloth/flux-3-image-klein-GGUF): UD-Q2_K_XL 2.62 GB, Q3_K_M 3.01, Q4_K_M 3.67, Q6_K 4.80, Q8_0 6.09, BF16 11.1 | |
| `text_encoders` | `qwen3vl_4b_int8_convrot.safetensors` from [black-forest-labs/flux-3-image-klein-comfy](https://huggingface.co/black-forest-labs/flux-3-image-klein-comfy) (gated: accept the licence) | 4.9 GB |
| `vae` | `flux2-vae.safetensors`, same repository | 0.3 GB |
| `custom_nodes` | [leejet/ComfyUI-GGUF](https://github.com/leejet/ComfyUI-GGUF) | |

## What we measured (bakery sign, seed 1, real seconds)

| VRAM tier | File | 4 steps | 8 steps | 16 steps |
|---|---|---|---|---|
| 4 GB | UD-Q2_K_XL | 30 s | 21 s | 38 s |
| 8 GB | Q4_K_M | 27 s | 16 s | 27 s |
| 12 GB | Q8_0 | 27 s | 11 s | 19 s |
| 16 GB | BF16 | 20 s | 12 s | 24 s |

The first run of each file includes loading it. RAM never needed to go above 32 GB. A PyTorch crash on start (`WinError 1114 ... c10.dll`) on
an old Visual C++ runtime: `python_embeded\python.exe -m pip install msvc-runtime`, then copy `python_embeded\Scripts\*.dll`
into `python_embeded\Lib\site-packages\torch\lib`.

FLUX 3 Klein is under the FLUX Kommunity License v1.0: free for non-commercial use, and commercial output for businesses under US$5M
a year in revenue; read it before business use. These files are provided as-is under the MIT licence.
