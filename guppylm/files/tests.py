"""Scores a GuppyLM model on the 16 held-out conversations that ship with GuppyLM (guppylm/eval_cases.py).
A reply passes when it contains one of the case's expected keywords - the repo's own checklist.

    python tests.py mine                 (the model you trained: mine\\best_model.pt + mine\\tokenizer.json)
    python tests.py official             (the author's published model, downloaded into official\\)
    python tests.py mine turns           (one long conversation: does it get worse after a few turns?)

Every test runs three times (replies are sampled), and the consistency across runs is reported.
"""

import os
import sys
import time

import torch

sys.path.insert(0, ".")
from guppylm.eval_cases import EVAL_CASES  # noqa: E402
from guppylm.inference import GuppyInference  # noqa: E402

folder = sys.argv[1]
mode = sys.argv[2] if len(sys.argv) > 2 else "cases"
device = "cuda" if torch.cuda.is_available() else "cpu"
engine = GuppyInference(os.path.join(folder, "best_model.pt"), os.path.join(folder, "tokenizer.json"), device)


def reply(messages):
    return engine.chat_completion(messages, temperature=0.7, max_tokens=64)["choices"][0]["message"]["content"]


def passes(case, text):
    return any(k in text.lower() for k in case["expect_keywords"])


if mode == "cases":
    passed_all = {c["id"]: True for c in EVAL_CASES}
    for run in (1, 2, 3):
        torch.manual_seed(run)
        start, right = time.time(), 0
        for case in EVAL_CASES:
            text = reply([{"role": "user", "content": case["prompt"]}])
            ok = passes(case, text)
            right += ok
            passed_all[case["id"]] &= ok
            if run == 1:
                print(f"{'PASS' if ok else 'MISS'}  {case['prompt'][:38]:38}  -> {text[:70]!r}")
        print(f"run {run}: {right} of {len(EVAL_CASES)} replies contain an expected keyword  "
              f"({(time.time() - start) / len(EVAL_CASES):.2f} s per reply on {device})")
    print(f"passed in all 3 runs: {sum(passed_all.values())} of {len(EVAL_CASES)}")
else:
    # Six of the held-out prompts as ONE conversation: each turn sees all the earlier turns.
    script = [c for c in EVAL_CASES if c["id"] in ("greeting_basic", "food_excited", "temp_cold", "light_on",
                                                    "loud_noise", "goodnight")]
    per_turn = [0] * len(script)
    for run in (1, 2, 3):
        torch.manual_seed(run)
        messages = []
        for turn, case in enumerate(script):
            messages.append({"role": "user", "content": case["prompt"]})
            try:
                text = reply(messages)
            except Exception as e:  # the model only has room for 128 tokens
                text = f"ERROR: {type(e).__name__}: {e}"
            messages.append({"role": "assistant", "content": text})
            per_turn[turn] += passes(case, text)
            if run == 1:
                tokens = len(engine.tokenizer.encode(engine._format_prompt(messages[:-1])).ids)
                print(f"turn {turn + 1} ({tokens:3} tokens in)  {'PASS' if passes(case, text) else 'MISS'}  "
                      f"{case['prompt'][:28]:28} -> {text[:60]!r}")
    print("right per turn, out of 3 runs:", "  ".join(f"turn {i + 1}: {n}" for i, n in enumerate(per_turn)))
