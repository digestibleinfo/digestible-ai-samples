"""Asks MiniCPM5-2B one question through llama-server (llama.cpp), with the model card's sampling
settings (temperature 1.0, top_p 0.95, min_p 0.0).

    from mini import ask
    answer, seconds, tokens = ask("What is 17 * 23?", think=True)
"""

import json
import os
import time
import urllib.error
import urllib.request

SERVER = os.environ.get("MINICPM_URL", "http://127.0.0.1:8080") + "/v1/chat/completions"


def ask(prompt, think=True, max_new_tokens=4096):
    """Returns (the answer without its thinking, seconds, new tokens)."""
    body = {"messages": [{"role": "user", "content": prompt}], "max_tokens": max_new_tokens,
            "temperature": 1.0, "top_p": 0.95, "min_p": 0.0, "chat_template_kwargs": {"enable_thinking": think}}
    req = urllib.request.Request(SERVER, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=1800) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        # Show the server's own explanation, not just "Bad Request".
        raise SystemExit(f"Server error {e.code}: {e.read().decode(errors='replace')[:400]}")
    seconds = time.time() - t
    answer = data["choices"][0]["message"].get("content") or ""
    if "</think>" in answer:
        answer = answer.split("</think>", 1)[1]
    return answer.strip(), seconds, data["usage"]["completion_tokens"]
