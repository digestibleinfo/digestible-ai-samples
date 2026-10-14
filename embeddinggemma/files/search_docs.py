import json
import re
import time
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.bfloat16 if device == "cuda" else torch.float32
model = SentenceTransformer("google/embeddinggemma-2", model_kwargs={"torch_dtype": dtype}, device=device)

files = sorted(Path("files").glob("*.txt"))
texts = [f.read_text(encoding="utf-8").strip() for f in files]
questions = json.loads(Path("doc_queries.json").read_text(encoding="utf-8"))

start = time.perf_counter()
docs = model.encode(texts, prompt_name="Document")
print(f"Embedded {len(files)} files in {time.perf_counter() - start:.2f} s\n")

STOP = set("a an the of to is it my me i do what how which who for and or on in at that this with about when are was we you".split())
def keyword_rank(query):
    words = set(re.findall(r"[a-z']+", query.lower())) - STOP
    scores = [(len(words & set(re.findall(r"[a-z']+", t.lower()))), f.name) for f, t in zip(files, texts)]
    return [name for score, name in sorted(scores, key=lambda s: -s[0])]

hits = {"meaning": [0, 0], "keyword": [0, 0]}
for item in questions:
    q = model.encode(item["query"], prompt_name="SearchQuery")
    scores = model.similarity(q, docs)[0]
    ranked = [files[i].name for i in scores.argsort(descending=True).tolist()]
    kw = keyword_rank(item["query"])
    for label, r in (("meaning", ranked), ("keyword", kw)):
        hits[label][0] += r[0] == item["answer"]
        hits[label][1] += item["answer"] in r[:3]
    mark = "OK  " if ranked[0] == item["answer"] else "MISS"
    kmark = "OK  " if kw[0] == item["answer"] else "MISS"
    print(f"{mark} {item['query'][:56]:56s} -> {ranked[0]}")
    print(f"{kmark} (keyword search found: {kw[0]})")

n = len(questions)
print(f"\nMeaning search: first answer right {hits['meaning'][0]}/{n}, in top 3: {hits['meaning'][1]}/{n}")
print(f"Keyword search: first answer right {hits['keyword'][0]}/{n}, in top 3: {hits['keyword'][1]}/{n}")
