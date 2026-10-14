"""AirLLM batch test: eight short questions with known answers, asked together in ONE pass over the
model, then scored.

    python batch_test.py <model folder> [new tokens] [padded]

"padded" uses the usual padding instead of equal-length prompts, to show what goes wrong.
"""

import json
import re
import sys
import time

import torch
from airllm import AutoModel

MODEL = sys.argv[1]
NEW_TOKENS = int(sys.argv[2]) if len(sys.argv) > 2 else 6
PADDED = len(sys.argv) > 3 and sys.argv[3] == "padded"

QUESTIONS = [
    ("What is 17 * 23? Answer with just the number.", "391"),
    ("What is the capital of Australia? Answer with one word.", "canberra"),
    ("What does the Python expression len([1, 2, 3]) return? Answer with just the number.", "3"),
    ("What is the chemical symbol for gold? Answer with just the symbol.", "au"),
    ("Write the word 'stone' backwards. Answer with just the word.", "enots"),
    ("How many days are in a leap year? Answer with just the number.", "366"),
    ("What is 2 to the power of 10? Answer with just the number.", "1024"),
    ("Which Python keyword defines a function? Answer with one word.", "def"),
]

t0 = time.time()
model = AutoModel.from_pretrained(MODEL, layer_shards_saving_path="shards")
print(f"model ready in {time.time() - t0:.0f} s", flush=True)

tok = model.tokenizer


def chat(question):
    return tok.apply_chat_template([{"role": "user", "content": question}], tokenize=False, add_generation_prompt=True)


def length(question):
    return len(tok(chat(question))["input_ids"])


if PADDED:
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    batch = tok([chat(q) for q, _ in QUESTIONS], return_tensors="pt", padding=True)
    extra = {"attention_mask": batch["attention_mask"].cuda()}
else:
    # AirLLM returns NaN for the padded rows of a batch (shown as "!"), so every prompt gets the same
    # token length instead: a one-token filler word is added to the shorter questions.
    target = max(length(q) for q, _ in QUESTIONS)
    padded = []
    for q, _ in QUESTIONS:
        while length(q) < target:
            q += " Thanks"
        padded.append(q)
    assert len({length(q) for q in padded}) == 1, "prompts still differ in length"
    batch = tok([chat(q) for q in padded], return_tensors="pt", padding=False)
    extra = {}

t1 = time.time()
out = model.generate(batch["input_ids"].cuda(), **extra,
                     max_new_tokens=NEW_TOKENS, use_cache=True, return_dict_in_generate=True,
                     do_sample=False, temperature=None, top_p=None, top_k=None, output_scores=True)
seconds = time.time() - t1
bad = sum(int((~torch.isfinite(sc)).any().item()) for sc in out.scores)
print(f"steps with non-finite scores: {bad} of {len(out.scores)}", flush=True)

right = 0
rows = []
for (question, expected), seq in zip(QUESTIONS, out.sequences):
    answer = tok.decode(seq[batch["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    ok = re.sub(r"\W+", "", expected) in re.sub(r"\W+", "", answer.lower())
    right += ok
    rows.append({"question": question, "expected": expected, "answer": answer, "right": ok})
    print(f"{'OK  ' if ok else 'MISS'} {question[:58]:58s} -> {answer!r}")
print(f"\n{right} of {len(QUESTIONS)} right, {NEW_TOKENS} new tokens, {seconds:.0f} s for the whole batch "
      f"({seconds / NEW_TOKENS:.0f} s per step), peak GPU memory {torch.cuda.max_memory_allocated() / 1e9:.1f} GB")
json.dump({"right": right, "total": len(QUESTIONS), "seconds": round(seconds), "new_tokens": NEW_TOKENS, "rows": rows},
          open("batch_result.json", "w"), indent=2)
