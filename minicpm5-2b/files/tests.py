"""MiniCPM5-2B tests with known answers: everyday maths, reading invoices into fields, small coding
jobs (checked by running them), and finding facts hidden in a long document.

    python tests.py              (all tests, thinking on)
    python tests.py maths        (one group)
    python tests.py maths nothink
"""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from mini import ask

HERE = Path(__file__).parent
THINK = "nothink" not in sys.argv
GROUPS = [a for a in sys.argv[1:] if a in ("maths", "invoices", "code", "long", "rands")] or ["maths", "invoices", "code", "long"]
results = {}


def number(text):
    found = re.findall(r"-?\d[\d ,]*\.?\d*", text.replace("R ", "R"))
    return float(found[-1].replace(" ", "").replace(",", "")) if found else None


def run(group, items, check):
    right, secs, toks = 0, 0.0, 0
    print(f"\n== {group} (thinking {'on' if THINK else 'off'})", flush=True)
    for item in items:
        answer, s, n = ask(item["prompt"], think=THINK)
        ok = check(item, answer)
        right += ok
        secs += s
        toks += n
        print(f"{'OK  ' if ok else 'MISS'} {s:5.1f}s {n:5d} tok  {item.get('name', item['prompt'][:60])}", flush=True)
        if not ok:
            print(f"        answer: {' '.join(answer.split())[-110:]!r}", flush=True)
    results[group] = {"right": right, "total": len(items), "seconds": round(secs, 1), "tokens": toks}
    print(f"   {right} of {len(items)} right, {secs:.0f} s, {toks / max(secs, 0.01):.0f} tokens per second", flush=True)


TESTS = json.loads((HERE / "tests.json").read_text(encoding="utf-8"))

if "maths" in GROUPS:
    run("maths", TESTS["maths"], lambda it, a: number(a) is not None and abs(number(a) - it["answer"]) < 0.01)

if "invoices" in GROUPS:
    items = []
    for f in sorted((HERE / "docs").glob("invoice_*.txt")):
        text = f.read_text(encoding="utf-8")
        truth = {"invoice_number": re.search(r"Invoice number: (\S+)", text).group(1),
                 "date": re.search(r"Date: (.+)", text).group(1).strip(),
                 "total": re.search(r"TOTAL DUE: (.+)", text).group(1).strip()}
        items.append({"name": f.name, "truth": truth, "prompt": "Read this invoice and reply with only a JSON object with the keys "
                      "invoice_number, date and total (copy them exactly as written).\n\n" + text})

    def invoice_ok(it, answer):
        m = re.search(r"\{.*\}", answer, re.S)
        try:
            got = json.loads(m.group(0)) if m else {}
        except json.JSONDecodeError:
            return False
        squash = lambda s: re.sub(r"[^0-9a-z]", "", str(s).lower())  # noqa: E731
        # Right when the true value is there, even with a label in front ("TOTAL DUE: R 20 424,51").
        return all(squash(v) in squash(got.get(k, "")) for k, v in it["truth"].items())
    run("invoices", items, invoice_ok)

if "code" in GROUPS:
    def code_ok(it, answer):
        m = re.search(r"```(?:python)?\n(.*?)```", answer, re.S)
        source = (m.group(1) if m else answer) + "\n\n" + it["tests"]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.py"
            p.write_text(source, encoding="utf-8")
            try:
                return subprocess.run([sys.executable, "-I", str(p)], capture_output=True, timeout=20, cwd=d).returncode == 0
            except subprocess.TimeoutExpired:
                return False
    run("code", TESTS["code"], code_ok)

if "long" in GROUPS:
    doc = (HERE / "long_document.txt").read_text(encoding="utf-8")
    items = [{"name": q["q"], "prompt": f"{doc}\n\nUsing only the document above, answer briefly: {q['q']}", "answer": q["a"]}
             for q in TESTS["long"]]
    run("long", items, lambda it, a: re.sub(r"\W", "", it["answer"].lower()) in re.sub(r"\W", "", a.lower()))

if "rands" in GROUPS:
    # The same three sums, written the South African way (R1 500) and without the space (R1500).
    for style in ("spaced", "plain"):
        items = [{"name": f"{it['name']} ({'R1 500' if style == 'spaced' else 'R1500'} style)", "prompt": it[style], "answer": it["answer"]}
                 for it in TESTS["rands"] for _ in range(3)]
        run(f"rands-{style}", items, lambda it, a: number(a) is not None and abs(number(a) - it["answer"]) < 0.01)

total = sum(r["right"] for r in results.values())
count = sum(r["total"] for r in results.values())
print(f"\nTOTAL: {total} of {count} right, thinking {'on' if THINK else 'off'}")
name = "results_" + "_".join(GROUPS) + ("" if THINK else "_nothink") + ".json"
Path(name).write_text(json.dumps(results, indent=2), encoding="utf-8")
