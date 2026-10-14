"""AirLLM, one prompt, a few tokens: how fast is an 80 GB model on a small GPU?

    python first_try.py <model folder> [new tokens]
"""

import sys
import time

import torch
from airllm import AutoModel

MODEL = sys.argv[1]
NEW_TOKENS = int(sys.argv[2]) if len(sys.argv) > 2 else 2

t0 = time.time()
model = AutoModel.from_pretrained(MODEL, layer_shards_saving_path="shards")
print(f"model ready in {time.time() - t0:.0f} s", flush=True)

text = ["Write a Python function is_palindrome(s) that ignores case and spaces."]
tok = model.tokenizer(text, return_tensors="pt", return_attention_mask=False, truncation=True, max_length=128, padding=False)
t1 = time.time()
out = model.generate(tok["input_ids"].cuda(), max_new_tokens=NEW_TOKENS, use_cache=True, return_dict_in_generate=True,
                     do_sample=False, temperature=None, top_p=None, top_k=None)
print(model.tokenizer.decode(out.sequences[0]))
print(f"{NEW_TOKENS} new tokens took {time.time() - t1:.0f} s ({(time.time() - t1) / NEW_TOKENS:.0f} s per token); "
      f"peak GPU memory {torch.cuda.max_memory_allocated() / 1e9:.1f} GB")
