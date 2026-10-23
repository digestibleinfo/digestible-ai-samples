"""Scores Kronos on many past moments where we already know what happened next.

For each test window: give Kronos the 400 candles before a moment, ask for the next N, and compare
the forecast with reality. The baseline is the dumbest honest guess: "the price stays where it is".

    python backtest.py btc_1h.csv 24 40           (40 moments, forecast 24 hours each)
    python backtest.py npn_1d.csv 5 40            (40 moments, forecast 5 trading days each)
    python backtest.py btc_1h.csv 24 40 repeat    (the same 40 forecasts 3 times: how consistent is it?)
    python backtest.py btc_1h.csv 24 40 mini      (the mini model instead of small; also: base)
    python backtest.py btc_1h.csv 24 40 avg5      (average 5 sampled futures per forecast, the README's sample_count=5)
"""

import sys
import time

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, "Kronos-master")
from model import Kronos, KronosPredictor, KronosTokenizer  # noqa: E402

LOOKBACK = 400
MODELS = {"mini": ("NeoQuasar/Kronos-mini", "NeoQuasar/Kronos-Tokenizer-2k", 2048),
          "small": ("NeoQuasar/Kronos-small", "NeoQuasar/Kronos-Tokenizer-base", 512),
          "base": ("NeoQuasar/Kronos-base", "NeoQuasar/Kronos-Tokenizer-base", 512)}
COLS = ["open", "high", "low", "close", "volume", "amount"]

csv, pred_len, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
flags = sys.argv[4:]
size = next((f for f in flags if f in MODELS), "small")
runs = 3 if "repeat" in flags else 1
samples = 5 if "avg5" in flags else 1

df = pd.read_csv(csv)
df["timestamps"] = pd.to_datetime(df["timestamps"])
name, tok_name, ctx = MODELS[size]
predictor = KronosPredictor(Kronos.from_pretrained(name), KronosTokenizer.from_pretrained(tok_name), max_context=ctx)

# n moments, evenly spaced over the part of the file that has 400 candles before and N after
cuts = np.linspace(LOOKBACK, len(df) - pred_len, n).astype(int)
xs = [df.iloc[c - LOOKBACK:c] for c in cuts]
ys = [df.iloc[c:c + pred_len] for c in cuts]
last = np.array([x["close"].iloc[-1] for x in xs])
real = np.array([y["close"].iloc[-1] for y in ys])
real_up = real > last

print(f"{csv}: {n} moments, {LOOKBACK} candles in, {pred_len} out, Kronos-{size} on {predictor.device}, "
      f"{samples} sampled future{'s' if samples > 1 else ''} per forecast")
directions = []
for run in range(1, runs + 1):
    torch.manual_seed(run)
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    start = time.time()
    preds = predictor.predict_batch([x[COLS] for x in xs], [x["timestamps"] for x in xs], [y["timestamps"] for y in ys],
                                    pred_len=pred_len, T=1.0, top_p=0.9, sample_count=samples, verbose=False)
    secs = time.time() - start
    guess = np.array([p["close"].iloc[-1] for p in preds])
    up = guess > last
    directions.append(up)
    k_err = np.mean(np.abs(guess - real) / real)
    n_err = np.mean(np.abs(last - real) / real)
    right = int(np.sum(up == real_up))
    print(f"run {run}: direction right {right} of {n} ({right / n:.0%})  |  average price error: Kronos {k_err:.2%}, "
          f"'no change' {n_err:.2%}  |  {secs:.1f} s")
    if run == 1:
        for i in range(min(n, 5)):
            print(f"   {xs[i]['timestamps'].iloc[-1]}  last {last[i]:,.2f}  Kronos {guess[i]:,.2f}  real {real[i]:,.2f}  "
                  f"{'RIGHT' if up[i] == real_up[i] else 'WRONG'}")
        if "volume" in df and pred_len >= 24:
            # Busy or quiet: Kronos's volume forecast against "the same as the last 24 candles"
            k_vol = np.mean([np.abs(p["volume"].values - y["volume"].values).mean() / y["volume"].mean() for p, y in zip(preds, ys)])
            n_vol = np.mean([np.abs(x["volume"].values[-pred_len:] - y["volume"].values).mean() / y["volume"].mean() for x, y in zip(xs, ys)])
            print(f"   volume error per candle: Kronos {k_vol:.1%}, 'same as the last {pred_len}' {n_vol:.1%}")

up_share = np.mean(real_up)
print(f"reality went up {int(np.sum(real_up))} of {n} times ({up_share:.0%}), so always saying 'up' scores {max(up_share, 1 - up_share):.0%}")
if runs > 1:
    same = int(np.sum(np.all(np.array(directions) == directions[0], axis=0)))
    print(f"same direction in all {runs} runs: {same} of {n}")
if torch.cuda.is_available():
    print(f"peak GPU memory {torch.cuda.max_memory_allocated() / 2**30:.2f} GB")
