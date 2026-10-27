# ComfyUI LOW VRAM: MOSS-Image GGUF

The three selected workflows and Windows memory-limit launcher from the Digestible AI MOSS-Image Low V-RAM test.
The GGUFs are from [unsloth/MOSS-Image-Base-GGUF](https://huggingface.co/unsloth/MOSS-Image-Base-GGUF/tree/main).
Tested with portable ComfyUI on a 16 GB NVIDIA GPU, using 1024x1024 images, seed 1, and 32 GB RAM caps.

| File | What it does |
|---|---|
| `moss-image-12gb-q8.json` | 8-step ComfyUI workflow using `MOSS-Image-Base-Q8_0.gguf`. |
| `moss-image-8gb-q6.json` | 8-step workflow using `MOSS-Image-Base-UD-Q6_K_XL.gguf`. |
| `moss-image-4gb-q4.json` | 8-step workflow using `MOSS-Image-Base-UD-Q4_K_XL.gguf`. |
| `lowvram_launch.py` | Starts portable ComfyUI with a VRAM reserve and Windows Job Object RAM cap. |

## Model files

Download the model weights yourself; they are not included in this pack. Put them here, inside
`ComfyUI_windows_portable\ComfyUI\models`:

| Folder | File |
|---|---|
| `unet` | The three GGUF files listed above |
| `text_encoders` | `qwen3.5_9b_w4a8_gptq.safetensors` from [Comfy-Org/MOSS-Image](https://huggingface.co/Comfy-Org/MOSS-Image) |
| `vae` | `flux2-vae_small.safetensors` from [Comfy-Org/MOSS-Image](https://huggingface.co/Comfy-Org/MOSS-Image) |
| `custom_nodes` | [ComfyUI-GGUF](https://github.com/leejet/ComfyUI-GGUF) |

Restart ComfyUI after installing the custom node and weights. Drag the matching workflow JSON onto the ComfyUI canvas.
The workflows use the same text encoder and VAE as the native reference, and their GGUF model loader is supplied by
ComfyUI-GGUF.

## Launch under the tested memory limits

Run these commands in PowerShell from the folder containing `lowvram_launch.py`. Set `COMFY_PORTABLE` to your own
`ComfyUI_windows_portable` directory. The launcher assumes a 16 GB GPU; change `CARD_GB` in the script if yours differs.
It sets the VRAM reserve automatically from the tier and margin, and caps the ComfyUI process tree at 32 GB RAM.

```powershell
$env:COMFY_PORTABLE = 'E:\ComfyUI_windows_portable'
$env:COMFY_VRAM_RESERVE_MARGIN_GB = '0.5'
python .\lowvram_launch.py 12 32
```

For the 8 GB tier, keep the 0.5 GB reserve margin and run:

```powershell
python .\lowvram_launch.py 8 32
```

For the 4 GB tier, use the larger margin measured for that run:

```powershell
$env:COMFY_VRAM_RESERVE_MARGIN_GB = '1.0'
python .\lowvram_launch.py 4 32
```

The tested values were 4.5 GB reserve for 12 GB, 8.5 GB for 8 GB, and 13 GB for 4 GB. Results on other hardware
may differ.

## What passed

The 12, 8 and 4 GB tiers passed with a 32 GB RAM cap. The selected bakery-prompt runs measured 26.2 seconds / 7.87 GB
VRAM, 38.7 seconds / 6.72 GB, and 61.2 seconds / 2.96 GB, respectively. VRAM is measured above the idle baseline.

**2 GB did not pass.** Both attempts exceeded the cap: 3.20 GB VRAM with the default device placement and 2.67 GB
with the text encoder on CPU. The second attempt took 764.6 seconds. No 2 GB workflow is included because it would
misrepresent the result.

This pack is provided as-is under the MIT licence. Model and custom-node licences remain with their respective authors.
