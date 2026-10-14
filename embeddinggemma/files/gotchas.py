import json
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer

files = sorted(Path("files").glob("*.txt"))
texts = [f.read_text(encoding="utf-8").strip() for f in files]
questions = json.loads(Path("doc_queries.json").read_text(encoding="utf-8"))
long_text = " ".join(texts)  # about 1,800 tokens: every file in one go


def load(dtype):
    return SentenceTransformer("google/embeddinggemma-2", model_kwargs={"torch_dtype": dtype}, device="cuda")


print("1. float16 against bfloat16")
for name, dtype in (("bfloat16", torch.bfloat16), ("float16", torch.float16)):
    model = load(dtype)
    short = model.encode(texts[0], convert_to_tensor=True)
    long = model.encode(long_text, convert_to_tensor=True)
    print(f"   {name:9s} short file: {'NaN' if torch.isnan(short).any() else 'fine':4s}   long document: {'NaN' if torch.isnan(long).any() else 'fine'}")

print("2. Shorter vectors")
model = load(torch.bfloat16)
docs = model.encode(texts, prompt_name="Document", convert_to_tensor=True)
queries = model.encode([q["query"] for q in questions], prompt_name="SearchQuery", convert_to_tensor=True)


def right(d, q):
    best = (q.float() @ d.float().T).argmax(dim=1).tolist()
    return sum(files[b].name == item["answer"] for b, item in zip(best, questions))


def shorten(x, n, normalise):
    x = x[:, :n]
    return torch.nn.functional.normalize(x, dim=1) if normalise else x


for n in (768, 256, 128):
    print(f"   {n} numbers, re-normalised: {right(shorten(docs, n, True), shorten(queries, n, True))}/{len(questions)} right")
print(f"   128 numbers, NOT re-normalised: {right(shorten(docs, 128, False), shorten(queries, 128, False))}/{len(questions)} right")
