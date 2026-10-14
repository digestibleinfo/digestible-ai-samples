"""Ask OpenJev a typed decision through llama-server, and get a probability for every option.

    from decide import choice, yes_no, score
    choice("Customer: my parcel never arrived", "Which team handles this?", ["billing", "shipping", "returns"])

The three question types follow the model card: choice (pick one of a set), yes/no (a probability),
and score (ordered levels). Each answer is read from the probabilities of the option letters at the
first output position, the way the card describes.
"""

import json
import math
import os
import string
import time
import urllib.request

SERVER = os.environ.get("OPENJEV_URL", "http://127.0.0.1:8080") + "/v1/chat/completions"
LETTERS = string.ascii_uppercase


def _ask(state, question, options):
    lines = [f"[{LETTERS[i]}] {opt}" for i, opt in enumerate(options)]
    prompt = (f"State:\n{state}\n\nQuestion: {question}\nOptions:\n" + "\n".join(lines) +
              "\n\nAnswer with the letter of the best option only.")
    body = {"messages": [{"role": "user", "content": prompt}], "max_tokens": 1, "temperature": 0,
            "logprobs": True, "top_logprobs": 20, "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(SERVER, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    t = time.time()
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.load(r)
    seconds = time.time() - t
    top = data["choices"][0]["logprobs"]["content"][0]["top_logprobs"]
    probs = {LETTERS[i]: 0.0 for i in range(len(options))}
    for item in top:
        letter = item["token"].strip().lstrip("[")
        if letter in probs:
            probs[letter] = max(probs[letter], math.exp(item["logprob"]))
    total = sum(probs.values()) or 1.0
    ranked = {options[LETTERS.index(k)]: v / total for k, v in probs.items()}
    return ranked, seconds


def choice(state, question, options):
    """Returns (best option, {option: probability}, seconds)."""
    ranked, seconds = _ask(state, question, options)
    return max(ranked, key=ranked.get), ranked, seconds


def yes_no(state, question):
    """Returns (probability of yes, seconds)."""
    ranked, seconds = _ask(state, question, ["yes", "no"])
    return ranked["yes"], seconds


def score(state, question, levels):
    """Ordered levels, lowest first. Returns (most likely level, expected position 0..1, seconds)."""
    ranked, seconds = _ask(state, question, levels)
    expected = sum(levels.index(k) * v for k, v in ranked.items()) / max(1, len(levels) - 1)
    return max(ranked, key=ranked.get), expected, seconds
