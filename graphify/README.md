# Graphify sample pack

The checking script from the Digestible AI videos on [Graphify](https://github.com/Graphify-Labs/graphify),
which turns a codebase into a knowledge graph. Tested on Windows 11 with the command-line tool only.

| File | What it does |
|---|---|
| `check_callers.py` | Checks graphify's call graph against the truth from Python's own parser (`ast`). For every function defined exactly once, it compares the real callers with graphify's `calls` links and prints how many real calls graphify found and how many of its links are real. |

```
graphify extract <project folder> --code-only
python check_callers.py <project folder>
```

What counts as a real call: `f()`, `self.f()`, or `f` passed by name to be called later, inside the
function's body. Calls through another object (`other.f()`) are reported separately, because the
name may belong to a library. Code that runs at the top level of a file is not checked.
