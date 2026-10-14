"""Runs the 55 test decisions with known answers through OpenJev, then the same choice questions
again with the options in a different order (the makers say answers flip in 2.3% of cases).

    python run_tests.py
"""

import json
import random
import statistics
from pathlib import Path

from decide import choice, score, yes_no

TESTS = json.loads(Path(__file__).with_name("tests.json").read_text(encoding="utf-8"))
random.seed(5)
times, report, flips, flip_total = [], {}, 0, 0

for key, group in TESTS.items():
    right = 0
    print(f"\n== {group['title']} ({group['use']})")
    for item in group["items"]:
        if "options" in group:
            got, probs, s = choice(item["state"], group["question"], group["options"])
            sure = probs[got]
            shuffled = group["options"][:]
            random.shuffle(shuffled)
            again, _, s2 = choice(item["state"], group["question"], shuffled)
            flip_total += 1
            flips += again != got
            times.append(s2)
        elif "levels" in group:
            got, _, s = score(item["state"], group["question"], group["levels"])
            sure = None
        else:
            p_yes, s = yes_no(item["state"], group["question"])
            got, sure = ("yes", p_yes) if p_yes >= 0.5 else ("no", 1 - p_yes)
        times.append(s)
        ok = got == item["answer"]
        right += ok
        conf = f"{sure:.0%}" if sure is not None else "   "
        print(f"{'OK  ' if ok else 'MISS'} {got:18s} {conf:>4s}  {item['state'][:70]}")
    report[key] = (right, len(group["items"]))
    print(f"   {right} of {len(group['items'])} right")

total = sum(r for r, _ in report.values())
count = sum(n for _, n in report.values())
print(f"\nTOTAL: {total} of {count} right ({total / count:.0%})")
print(f"Shuffled options: {flips} of {flip_total} answers changed ({flips / flip_total:.1%})")
print(f"Speed: median {statistics.median(times):.2f} s per decision, slowest {max(times):.2f} s")
Path("results.json").write_text(json.dumps({"report": report, "flips": [flips, flip_total],
                                            "median_s": statistics.median(times)}, indent=2), encoding="utf-8")
