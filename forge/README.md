# Forge sample pack

The scoring script from the Digestible AI videos on [Forge](https://github.com/antoinezambelli/forge),
the guardrails layer for tool calling with self-hosted models. Tested on Windows 11 with llama.cpp
(llama-server) and Ministral-3-8B-Instruct-2512 (Q8_0) on an NVIDIA RTX 5060 Ti.

| File | What it does |
|---|---|
| `score.py` | Runs forge's own eval harness (`tests.eval.eval_runner`) on its 26 non-compaction scenarios and adds the runs up into one scoreboard: the baseline tier (OG-18), the hard tier (advanced reasoning), and the total. |

Unpack `forge-samples.zip` inside `forge-main` (the repo's code, downloaded as a zip, installed with
`pip install -e "forge-main[dev]"`), start llama-server on port 8080, then:

```
python score.py ..\Ministral-3-8B-Instruct-2512-Q8_0.gguf bare 3        (all guardrails off)
python score.py ..\Ministral-3-8B-Instruct-2512-Q8_0.gguf reforged 3    (forge's guardrails on)
```

`bare` and `reforged` are forge's own ablation presets (see its `docs/EVAL_GUIDE.md`). Whether a
scenario run is right is decided by forge's harness; this script only adds the runs up.
