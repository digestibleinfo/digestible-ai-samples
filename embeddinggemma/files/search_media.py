import json
import sys
import time
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer

kind = sys.argv[1]  # "photos" or "voicenotes"
pattern = "*.jpg" if kind == "photos" else "*.wav"
field = "image" if kind == "photos" else "audio"
queries_file = "photo_queries.json" if kind == "photos" else "voice_queries.json"

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.bfloat16 if device == "cuda" else torch.float32
model = SentenceTransformer("google/embeddinggemma-2", model_kwargs={"torch_dtype": dtype}, device=device)

files = sorted(Path(kind).glob(pattern))
questions = json.loads(Path(queries_file).read_text(encoding="utf-8"))

start = time.perf_counter()
items = model.encode([{field: str(f)} for f in files])
print(f"Embedded {len(files)} {kind} in {time.perf_counter() - start:.2f} s\n")

first = top3 = 0
for item in questions:
    q = model.encode(item["query"], prompt_name="SearchQuery")
    scores = model.similarity(q, items)[0]
    ranked = [files[i].name for i in scores.argsort(descending=True).tolist()]
    first += ranked[0] == item["answer"]
    top3 += item["answer"] in ranked[:3]
    mark = "OK  " if ranked[0] == item["answer"] else "MISS"
    print(f"{mark} {item['query'][:50]:50s} -> {ranked[0]}  (expected {item['answer']})" if mark == "MISS" else f"{mark} {item['query'][:50]:50s} -> {ranked[0]}")
print(f"\nFirst answer right {first}/{len(questions)}, in top 3: {top3}/{len(questions)}")
