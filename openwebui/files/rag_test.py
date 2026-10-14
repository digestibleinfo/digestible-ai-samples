"""Open WebUI document test: uploads the test documents into a knowledge base, then asks 14 questions
with known answers three ways and scores each: (1) no documents, (2) documents with the default
settings, (3) documents with a larger context window.

    python rag_test.py <model> [email] [password]        (Open WebUI must be running on port 8080)
"""

import json
import re
import sys
import time
from pathlib import Path

import requests

BASE = "http://localhost:8080"
MODEL = sys.argv[1]
EMAIL = sys.argv[2] if len(sys.argv) > 2 else "test@example.com"
PASSWORD = sys.argv[3] if len(sys.argv) > 3 else "Test-pass-123"
HERE = Path(__file__).parent

r = requests.post(f"{BASE}/api/v1/auths/signin", json={"email": EMAIL, "password": PASSWORD})
r.raise_for_status()
H = {"Authorization": "Bearer " + r.json()["token"]}

kb = requests.post(f"{BASE}/api/v1/knowledge/create", headers=H,
                   json={"name": f"Invoices {time.strftime('%H%M%S')}", "description": "test documents"}).json()
for f in sorted((HERE / "docs").glob("*.txt")):
    up = requests.post(f"{BASE}/api/v1/files/", headers=H, files={"file": (f.name, f.read_bytes())})
    up.raise_for_status()
    requests.post(f"{BASE}/api/v1/knowledge/{kb['id']}/file/add", headers=H, json={"file_id": up.json()["id"]}).raise_for_status()
print(f"uploaded {len(list((HERE / 'docs').glob('*.txt')))} documents to knowledge base {kb['id']}", flush=True)

QUESTIONS = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))


def squash(s):
    """Only letters and digits count, so R 20 424,51 and R 20,424.51 are the same amount."""
    return re.sub(r"[^0-9a-z]+", "", s.lower())


def ask(question, use_docs, num_ctx=None):
    body = {"model": MODEL, "stream": False,
            "messages": [{"role": "user", "content": question + " Answer in one short line."}]}
    if use_docs:
        body["files"] = [{"type": "collection", "id": kb["id"]}]
    if num_ctx:
        body["options"] = {"num_ctx": num_ctx}
    t = time.time()
    resp = requests.post(f"{BASE}/api/chat/completions", headers=H, json=body, timeout=600)
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"]
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip(), time.time() - t


results = {}
for label, use_docs, ctx in (("no documents", False, None), ("documents, default settings", True, None),
                             ("documents, context 8192", True, 8192)):
    right, secs, rows = 0, 0.0, []
    for item in QUESTIONS:
        answer, s = ask(item["q"], use_docs, ctx)
        ok = squash(item["a"]) in squash(answer)
        right += ok
        secs += s
        rows.append({"q": item["q"], "expected": item["a"], "answer": answer[:160], "right": ok})
        print(f"{'OK  ' if ok else 'MISS'} [{label}] {item['q'][:55]:55s} -> {answer[:70]!r}", flush=True)
    results[label] = {"right": right, "total": len(QUESTIONS), "seconds": round(secs), "rows": rows}
    print(f"== {label}: {right} of {len(QUESTIONS)} right, {secs:.0f} s\n", flush=True)

json.dump(results, open("rag_result.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("SUMMARY", {k: f"{v['right']}/{v['total']} in {v['seconds']} s" for k, v in results.items()})
