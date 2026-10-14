import time
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer

texts = [f.read_text(encoding="utf-8").strip() for f in sorted(Path("files").glob("*.txt"))]

for device in ("cuda", "cpu"):
    if device == "cuda" and not torch.cuda.is_available():
        continue
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    model = SentenceTransformer("google/embeddinggemma-2", model_kwargs={"torch_dtype": dtype}, device=device)
    model.encode(texts[:2], prompt_name="Document")  # warm-up
    start = time.perf_counter()
    model.encode(texts, prompt_name="Document")
    print(f"{device.upper():4s}: {len(texts)} files embedded in {time.perf_counter() - start:.2f} s")

if torch.cuda.is_available():
    print(f"GPU memory used: {torch.cuda.max_memory_allocated() / 1e9:.1f} GB")
