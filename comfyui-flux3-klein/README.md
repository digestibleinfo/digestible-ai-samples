# ComfyUI + FLUX 3 Klein (NVFP4) workflows

The ComfyUI workflows from the Digestible AI video on [FLUX 3 Image Klein](https://huggingface.co/black-forest-labs/flux-3-image-klein-comfy),
Black Forest Labs' 5.6B image model, with the smallest files, and on Qwen-Image-2.1-Turbo as the comparison. Tested on
Windows 11 with portable ComfyUI v0.42.1 on an NVIDIA RTX 5060 Ti (16 GB). Drag any of these onto the ComfyUI canvas.

| File | What it does |
|---|---|
| `flux3-klein-nvfp4-workflow.json` | Text to image **with** Black Forest Labs' prompt upsampler, its two subgraphs opened up so every step is visible: the upsampler (Load CLIP, their system prompt, Generate Text, Preview as Text), then Load Diffusion Model, Load CLIP, Load VAE, CLIP Text Encode, Empty Flux 2 Latent (1024x1024), ModelSamplingFlux (shift 2.77), KSampler (16 steps, cfg 1, euler, simple, seed 1 fixed), VAE Decode, Save Image. |
| `flux3-klein-nvfp4-raw-workflow.json` | The same without the upsampler: your prompt goes straight to the text encoder. Used for the step-count tests. **Change the KSampler steps, and set both ModelSamplingFlux shifts to the natural log of the steps** (4 steps: 1.38629, 8: 2.07944, 16: 2.77259), as Black Forest Labs' own workflow does. |
| `flux3-klein-nvfp4-edit-workflow.json` | Black Forest Labs' own image-to-image workflow, switched to the NVFP4 model: the reference image (`mug_product.png` in `ComfyUI\input`), the edit prompt, the upsampler and the sampler. Put your own picture in Load Image. |
| `qwen-image-2.1-turbo-workflow.json` | The comparison: Qwen-Image-2.1-Turbo from Comfy-Org's template, 8 steps on the checkpoint's fixed sigma list in `ManualSigmas` (cut the list to `1.0, 0.95418, 0.89508, 0.704534, 0` for 4 steps), cfg 1, euler. |

## Files they expect

FLUX 3 Klein: the repo is gated, so accept the licence on the model page and use a Hugging Face access token.

| Folder (inside `ComfyUI_windows_portable\ComfyUI\models`) | File | Size |
|---|---|---|
| `diffusion_models` | `flux3-image-klein-nvfp4.safetensors` (needs an RTX 50 / Blackwell card; otherwise use `flux3-image-klein-int8-convrot.safetensors`) | 5.3 GB |
| `text_encoders` | `qwen3vl_4b_int8_convrot.safetensors` | 4.9 GB |
| `text_encoders` | `qwen3.5_9b_flux3_prompt_upsampler_w4a8.safetensors` | 6.7 GB |
| `vae` | `flux2-vae.safetensors` | 0.3 GB |

All four are in [black-forest-labs/flux-3-image-klein-comfy](https://huggingface.co/black-forest-labs/flux-3-image-klein-comfy).

Qwen-Image-2.1-Turbo (open), from [Comfy-Org/Qwen-Image-2.1](https://huggingface.co/Comfy-Org/Qwen-Image-2.1):

| Folder | File | Size |
|---|---|---|
| `diffusion_models` | `qwen_image_2.1_turbo_int8_convrot.safetensors` | 7.3 GB |
| `text_encoders` | `qwen3vl_8b_w4a8.safetensors` | 6.3 GB |
| `vae` | `qwen_image_2.1_vae_bf16.safetensors` | 0.7 GB |

## A problem we hit

**PyTorch crashes on start** (`WinError 1114 ... c10.dll`) on PCs with an old Visual C++ runtime. Without admin rights:
`python_embeded\python.exe -m pip install msvc-runtime`, then
`copy python_embeded\Scripts\*.dll python_embeded\Lib\site-packages\torch\lib`.

The upsampler's system prompt in these workflows is Black Forest Labs' own, from their workflow files (MIT). Klein is
under the FLUX Kommunity License v1.0: free for non-commercial use, and commercial output for businesses under US$5M a
year in revenue; read it before business use. Qwen-Image-2.1 is under the Qwen Research License. These workflow files are
provided as-is under the MIT licence.
