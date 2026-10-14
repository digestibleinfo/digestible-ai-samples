"""Do the numbers on a receipt add up? Reads the text files in the out folder and, for every
receipt, adds up the item prices and compares the sum with the printed total.

    python check_totals.py            (receipts read normally)
    python check_totals.py notag      (receipts read with the wrongly typed prompt)
"""

import re
import sys
from pathlib import Path

suffix = "_notag" if "notag" in sys.argv[1:] else ""


def amount(text):
    """'R 1 234,56' -> 1234.56"""
    m = re.search(r"R\s*([\d ]+),(\d{2})", text)
    return float(m.group(1).replace(" ", "") + "." + m.group(2)) if m else None


files = [f for f in sorted(Path("out").glob("*receipt*.txt")) if f.stem.endswith("_notag") == bool(suffix)]
bad = 0
for f in files:
    items, total = [], None
    for line in f.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) == 2 and amount(cells[1]) is not None:
            if cells[0].upper().startswith("TOTAL"):
                total = amount(cells[1])
            else:
                items.append(amount(cells[1]))
    if total is None:
        verdict = "NO TOTAL FOUND: do not trust this one"
    elif abs(sum(items) - total) < 0.005:
        verdict = f"OK    items add up to R {total:.2f}"
    else:
        verdict = f"WRONG items add up to R {sum(items):.2f}, the receipt says R {total:.2f}"
    bad += not verdict.startswith("OK")
    print(f"{f.stem:24s} {verdict}")
print(f"\n{len(files) - bad} of {len(files)} receipts add up")
