"""Scores what the OCR read against the true facts: are the numbers that matter all there?

    python check_results.py          (checks the files in the out folder)
    python check_results.py notag    (checks the files read with the wrongly typed prompt)
"""

import json
import re
import sys
from pathlib import Path

suffix = "_notag" if "notag" in sys.argv[1:] else ""
facts = json.loads(Path("facts.json").read_text(encoding="utf-8"))


def squash(s):
    return re.sub(r"[\s |]+", "", s).replace("R", "")


perfect = checked = got_all = want_all = 0
for name, wanted in facts.items():
    path = Path(f"out/{name}{suffix}.txt")
    if not path.exists():
        continue
    flat = squash(path.read_text(encoding="utf-8"))
    missing = [f for f in wanted if squash(f) not in flat]
    checked += 1
    perfect += not missing
    got_all += len(wanted) - len(missing)
    want_all += len(wanted)
    print(f"{path.stem:24s} {len(wanted) - len(missing):2d}/{len(wanted):2d} facts" + (f"   MISSING: {missing}" if missing else ""))
print(f"\n{perfect} of {checked} documents perfect, {got_all} of {want_all} facts found")
