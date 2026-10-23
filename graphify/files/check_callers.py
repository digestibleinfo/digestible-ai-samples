"""Checks graphify's call graph against the truth, taken from Python's own parser (ast).

For every function defined exactly once in the project, the truth is the set of functions whose body
calls it. graphify's answer is its "calls" links in graphify-out/graph.json. The script prints how
many real calls graphify found (recall), how many of its links are real (precision), and examples.

    python check_callers.py <project folder>          (after: graphify extract <project folder>)
"""

import ast
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

root = Path(sys.argv[1])
files = [p for p in root.rglob("*.py") if "graphify-out" not in p.parts and "venv" not in p.parts]


def norm(label: str) -> str:
    return label.strip().lstrip(".").removesuffix("()").lower()


# ---- the truth: who calls what, from the source code itself ------------------------------------
defined = Counter()
calls = set()  # (file, caller, callee)
other_calls = set()  # other_object.f(): checked separately, because the name may belong to a library
for f in files:
    rel = f.relative_to(root).as_posix()
    try:
        tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        continue
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined[fn.name.lower()] += 1
            # Only the body runs when the function is called (defaults and decorators run at definition),
            # and a name that is a parameter or a local variable is not a function.
            local = {a.arg for a in fn.args.args + fn.args.kwonlyargs + fn.args.posonlyargs}
            local |= {a.arg for a in (fn.args.vararg, fn.args.kwarg) if a}
            body = [n for stmt in fn.body for n in ast.walk(stmt)]
            local |= {n.id for n in body if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
            for node in body:
                # A real call: f(), self.f(), or f passed by name to be called later (data_func = f).
                # other_object.f() is left out: it is usually some library's f (requests.get, loss.backward).
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name) and node.func.value.id in ("self", "cls"):
                        calls.add((rel, fn.name.lower(), node.func.attr.lower()))
                    else:
                        other_calls.add((rel, fn.name.lower(), node.func.attr.lower()))
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id not in local:
                    calls.add((rel, fn.name.lower(), node.id.lower()))
unique = {n for n, k in defined.items() if k == 1}
truth = {(f, a, b) for f, a, b in calls if b in unique}  # a == b is recursion, a real call too

# ---- graphify's answer -------------------------------------------------------------------------
g = json.loads((root / "graphify-out" / "graph.json").read_text(encoding="utf-8"))
label = {n["id"]: n for n in g["nodes"]}
found = set()
for e in g["links"]:
    if e.get("relation") not in ("calls", "indirect_call"):
        continue
    src, dst = label.get(e["source"]), label.get(e["target"])
    if not src or not dst:
        continue
    callee = norm(dst["label"])
    if callee in unique:
        found.add(((e.get("source_file") or src.get("source_file") or "").replace("\\", "/"), norm(src["label"]), callee))

hits = truth & found
by_callee = defaultdict(lambda: [0, 0])
for _, _, b in truth:
    by_callee[b][1] += 1
for _, _, b in hits:
    by_callee[b][0] += 1
print(f"{len(files)} Python files, {len(unique)} functions defined exactly once, {len(truth)} real calls to them")
print(f"graphify found {len(hits)} of {len(truth)} real calls ({len(hits) / max(1, len(truth)):.0%} recall)")
print(f"of graphify's {len(found)} call links to those functions, {len(hits)} are real ({len(hits) / max(1, len(found)):.0%} precision)")
print("most-called functions (found / real callers):")
for name, (h, t) in sorted(by_callee.items(), key=lambda kv: -kv[1][1])[:8]:
    print(f"  {name:32} {h} / {t}")
missed = sorted(truth - found)[:5]
if missed:
    print("examples graphify missed:")
    for f, a, b in missed:
        print(f"  {f}: {a}() calls {b}()")
extra = found - truth
via_object = extra & other_calls
unexplained = sorted(extra - other_calls)
print(f"of graphify's {len(extra)} other links, {len(via_object)} are calls through another object "
      f"(like self.loader.get_data_config()), which the strict count leaves out")
print(f"links with no matching call in the code: {len(unexplained)}")
for f, a, b in unexplained[:5]:
    print(f"  {f}: {a}() -> {b}()")
