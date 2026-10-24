# ComfyUI + FLUX 3 Klein (NVFP4) workflow

The ComfyUI workflow from the Digestible AI video on [FLUX 3 Image Klein](https://huggingface.co/black-forest-labs/flux-3-image-klein-comfy),
Black Forest Labs' 5.6B image model, with the smallest files. Tested on Windows 11 with portable ComfyUI v0.42.1 on an
NVIDIA RTX 5060 Ti (16 GB): 18 to 21 seconds per 1024x1024 image with the prompt upsampler, about 9 seconds without it.

| File | What it does |
|---|---|
| `flux3-klein-nvfp4-workflow.json` | Black Forest Labs' text-to-image workflow with its two subgraphs opened up, so every step is visible: the prompt upsampler (Load CLIP, their system prompt, Generate Text, Preview as Text), then Load Diffusion Model, Load CLIP, Load VAE, CLIP Text Encode, Empty Flux 2 Latent (1024x1024), ModelSamplingFlux (shift 2.77), KSampler (16 steps, cfg 1, euler, simple, seed 1 fixed), VAE Decode, Save Image. Drag it onto the ComfyUI canvas. |

## Files it expects

The repo is gated: accept the licence on the model page and use a Hugging Face access token.

| Folder (inside `ComfyUI_windows_portable\ComfyUI\models`) | File | Size |
|---|---|---|
| `diffusion_models` | `flux3-image-klein-nvfp4.safetensors` (needs an RTX 50 / Blackwell card; otherwise use `flux3-image-klein-int8-convrot.safetensors`) | 5.3 GB |
| `text_encoders` | `qwen3vl_4b_int8_convrot.safetensors` | 4.9 GB |
| `text_encoders` | `qwen3.5_9b_flux3_prompt_upsampler_w4a8.safetensors` | 6.7 GB |
| `vae` | `flux2-vae.safetensors` | 0.3 GB |

All four are in [black-forest-labs/flux-3-image-klein-comfy](https://huggingface.co/black-forest-labs/flux-3-image-klein-comfy).

## A problem we hit

**PyTorch crashes on start** (`WinError 1114 ... c10.dll`) on PCs with an old Visual C++ runtime. Without admin rights:
`python_embeded\python.exe -m pip install msvc-runtime`, then
`copy python_embeded\Scripts\*.dll python_embeded\Lib\site-packages\torch\lib`.

The upsampler's system prompt in this workflow is Black Forest Labs' own, from their workflow files (MIT). The model is
under the FLUX Kommunity License v1.0: free for non-commercial use, and commercial output for businesses under US$5M a
year in revenue; read it before business use. This workflow file is provided as-is under the MIT licence.
