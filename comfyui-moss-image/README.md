# ComfyUI + MOSS-Image-SFT (int8) workflow

The ComfyUI workflow from the Digestible AI video on [MOSS-Image-SFT](https://huggingface.co/OpenMOSS-Team/MOSS-Image-SFT)
(OpenMOSS), with the smallest files from [Comfy-Org/MOSS-Image](https://huggingface.co/Comfy-Org/MOSS-Image). Tested on
Windows 11 with portable ComfyUI v0.42.1 on an NVIDIA RTX 5060 Ti (16 GB).

| File | What it does |
|---|---|
| `moss-image-sft-workflow.json` | Comfy-Org's MOSS-Image text-to-image template with its subgraph opened up: the prompt enhancer (the Qwen3.5-9B text encoder rewrites your prompt with Comfy-Org's system prompt; Preview as Text shows the result), then Load Diffusion Model, Load VAE, CLIP Text Encode (prompt and the template's negative prompt), Empty Flux 2 Latent (1024x1024), KSampler (25 steps, cfg 2.5, er_sde, simple, seed 1 fixed), VAE Decode, Save Image. Drag it onto the ComfyUI canvas. |

## Files it expects (open, no token)

| Folder (inside `ComfyUI_windows_portable\ComfyUI\models`) | File | Size |
|---|---|---|
| `diffusion_models` | `moss_image_sft_int8_convrot.safetensors` | 5.4 GB |
| `text_encoders` | `qwen3.5_9b_w4a8_gptq.safetensors` | 7.3 GB |
| `vae` | `flux2-vae_small.safetensors` | 0.25 GB |

## A problem we hit

**PyTorch crashes on start** (`WinError 1114 ... c10.dll`) on PCs with an old Visual C++ runtime. Without admin rights:
`python_embeded\python.exe -m pip install msvc-runtime`, then
`copy python_embeded\Scripts\*.dll python_embeded\Lib\site-packages\torch\lib`.

The prompt enhancer's system prompt is Comfy-Org's own, from their workflow template. MOSS-Image-SFT is released under the
Apache License 2.0. This workflow file is provided as-is under the MIT licence.
