"""Time and memory for one 24-hour forecast with each open Kronos model, on the graphics card and the processor.

    python speed.py btc_1h.csv
"""

import sys
import time

import pandas as pd
import torch

sys.path.insert(0, "Kronos-master")
from model import Kronos, KronosPredictor, KronosTokenizer  # noqa: E402

MODELS = [("mini", "NeoQuasar/Kronos-mini", "NeoQuasar/Kronos-Tokenizer-2k", 2048),
          ("small", "NeoQuasar/Kronos-small", "NeoQuasar/Kronos-Tokenizer-base", 512),
          ("base", "NeoQuasar/Kronos-base", "NeoQuasar/Kronos-Tokenizer-base", 512)]

df = pd.read_csv(sys.argv[1])
df["timestamps"] = pd.to_datetime(df["timestamps"])
x, y = df.iloc[-424:-24], df.iloc[-24:]
cols = ["open", "high", "low", "close", "volume", "amount"]

for device in (["cuda:0"] if torch.cuda.is_available() else []) + ["cpu"]:
    for size, name, tok, ctx in MODELS:
        model = Kronos.from_pretrained(name)
        params = sum(p.numel() for p in model.parameters()) / 1e6
        predictor = KronosPredictor(model, KronosTokenizer.from_pretrained(tok), device=device, max_context=ctx)
        predictor.predict(df=x[cols], x_timestamp=x["timestamps"], y_timestamp=y["timestamps"], pred_len=24, verbose=False)  # warm-up
        if device != "cpu":
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats()
        start = time.time()
        predictor.predict(df=x[cols], x_timestamp=x["timestamps"], y_timestamp=y["timestamps"], pred_len=24, verbose=False)
        secs = time.time() - start
        mem = f"{torch.cuda.max_memory_allocated() / 2**20:,.0f} MB GPU" if device != "cpu" else "processor"
        print(f"{size:6} {params:6.1f}M parameters  {device:7}  one 24-hour forecast in {secs:5.2f} s  ({mem})")
        del predictor, model
        if device != "cpu":
            torch.cuda.empty_cache()
