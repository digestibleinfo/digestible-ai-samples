# ComfyUI + Qwen-Image-2.1 GGUF (Q3_K_S) workflow

The ComfyUI workflow from the Digestible AI video that runs [Qwen-Image-2.1](https://huggingface.co/Qwen/Qwen-Image-2.1)
from unsloth's 2.7 GB [Q3_K_S GGUF](https://huggingface.co/unsloth/Qwen-Image-2.1-GGUF). Tested on Windows 11 with
portable ComfyUI v0.42.1 on an NVIDIA RTX 5060 Ti (16 GB): about 64 seconds for a 1024x1024 image at 25 steps.

| File | What it does |
|---|---|
| `qwen-image-2.1-gguf-workflow.json` | The workflow: Unet Loader (GGUF), Load CLIP, Load VAE, Text Encode Qwen Image 2.1, Empty Latent Image (1024x1024), KSampler (25 steps, cfg 1, euler, simple, seed 1 fixed), VAE Decode, Save Image. Drag it onto the ComfyUI canvas. |

## Files it expects

| Folder (inside `ComfyUI_windows_portable\ComfyUI`) | File | From |
|---|---|---|
| `models\unet` | `qwen-image-2.1-Q3_K_S.gguf` | [unsloth/Qwen-Image-2.1-GGUF](https://huggingface.co/unsloth/Qwen-Image-2.1-GGUF) |
| `models\text_encoders` | `qwen3vl_8b_w4a8.safetensors` | [Comfy-Org/Qwen-Image-2.1](https://huggingface.co/Comfy-Org/Qwen-Image-2.1/tree/main/text_encoders) |
| `models\vae` | `qwen_image_2.1_vae_bf16.safetensors` | [Comfy-Org/Qwen-Image-2.1](https://huggingface.co/Comfy-Org/Qwen-Image-2.1/tree/main/vae) |
| `custom_nodes` | `ComfyUI-GGUF` | [leejet/ComfyUI-GGUF](https://github.com/leejet/ComfyUI-GGUF) (see below) |

## Two problems we hit

- **"Unknown model architecture!"** The usual ComfyUI-GGUF node (city96) does not recognise this GGUF yet. leejet's
  fork adds Qwen-Image-2.1 support:
  `git clone https://github.com/leejet/ComfyUI-GGUF ComfyUI\custom_nodes\ComfyUI-GGUF`, then
  `python_embeded\python.exe -m pip install -r ComfyUI\custom_nodes\ComfyUI-GGUF\requirements.txt`.
- **PyTorch crashes on start** (`WinError 1114 ... c10.dll`) on PCs with an old Visual C++ runtime. Without admin rights:
  `python_embeded\python.exe -m pip install msvc-runtime`, then
  `copy python_embeded\Scripts\*.dll python_embeded\Lib\site-packages\torch\lib`.

Qwen-Image-2.1 is released under the [Qwen Research License](https://huggingface.co/Qwen/Qwen-Image-2.1/blob/main/LICENSE);
check it before any commercial use. The workflow file is provided as-is under the MIT licence.
