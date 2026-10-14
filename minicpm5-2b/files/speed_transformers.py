"""The model card's Transformers quick start, timed: loads MiniCPM5-2B on the graphics card and
measures tokens per second.

    python speed_transformers.py <model folder or openbmb/MiniCPM5-2B>
"""

import sys
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = sys.argv[1] if len(sys.argv) > 1 else "openbmb/MiniCPM5-2B"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.bfloat16, device_map="cuda")
messages = [{"role": "user", "content": "Explain in a short paragraph why the sky is blue."}]
inputs = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, enable_thinking=False,
                                       return_dict=True, return_tensors="pt").to(model.device)
for run in (1, 2):
    t = time.time()
    out = model.generate(**inputs, max_new_tokens=128, do_sample=True, temperature=1.0, top_p=0.95)
    n = out.shape[-1] - inputs["input_ids"].shape[-1]
    print(f"run {run}: {n} tokens in {time.time() - t:.1f} s = {n / (time.time() - t):.1f} tokens per second")
print(tokenizer.decode(out[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True))
