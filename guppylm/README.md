# GuppyLM sample pack

The test script from the Digestible AI videos on [GuppyLM](https://github.com/arman-bd/guppylm), the
~9M-parameter language model that talks like a fish. Tested on Windows 11 with an NVIDIA RTX 5060 Ti.

Unpack `guppylm-samples.zip` inside the `guppylm-main` folder (the repo's code, downloaded as a zip):

| File | What it does |
|---|---|
| `tests.py` | Scores a GuppyLM model on the 16 held-out conversations that ship with GuppyLM (`guppylm/eval_cases.py`). A reply passes when it contains one of the case's expected keywords. Every test runs three times. |

```
python tests.py mine              (a model you trained, saved in mine\)
python tests.py official          (the published model, saved in official\)
python tests.py mine turns        (one six-turn conversation: does it hold up?)
```

`mine\` and `official\` each need `best_model.pt` and `tokenizer.json` (the official model also has
`config.json`). Copy them out of `checkpoints\` and `data\` after training or after
`python -m guppylm download`, because download overwrites the files that training made.
