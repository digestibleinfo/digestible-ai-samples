"""The README's example on real data: hide the last part of a price file, let Kronos forecast it,
and compare with what really happened. Saves the chart as forecast.png.

    python forecast.py btc_1h.csv            (forecast the last 24 hours from the 400 before them)
    python forecast.py npn_1d.csv 5          (forecast the last 5 days)
"""

import sys
import time

import matplotlib

matplotlib.use("Agg")  # save the chart to a file instead of opening a window
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, "Kronos-master")
from model import Kronos, KronosPredictor, KronosTokenizer  # noqa: E402

LOOKBACK = 400

csv = sys.argv[1]
pred_len = int(sys.argv[2]) if len(sys.argv) > 2 else 24
df = pd.read_csv(csv)
df["timestamps"] = pd.to_datetime(df["timestamps"])

start = time.time()
tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
model = Kronos.from_pretrained("NeoQuasar/Kronos-small")
predictor = KronosPredictor(model, tokenizer, max_context=512)
print(f"model ready in {time.time() - start:.1f} s on {predictor.device}")

cut = len(df) - pred_len
x = df.iloc[cut - LOOKBACK:cut]
y = df.iloc[cut:]
start = time.time()
pred = predictor.predict(df=x[["open", "high", "low", "close", "volume", "amount"]], x_timestamp=x["timestamps"],
                         y_timestamp=y["timestamps"], pred_len=pred_len, T=1.0, top_p=0.9, sample_count=1, verbose=False)
print(f"forecast of {pred_len} candles in {time.time() - start:.1f} s")

last = x["close"].iloc[-1]
real, guess = y["close"].iloc[-1], pred["close"].iloc[-1]
print(f"last known close   {last:,.2f}")
print(f"Kronos said        {guess:,.2f}  ({(guess - last) / last:+.2%})")
print(f"what really came   {real:,.2f}  ({(real - last) / last:+.2%})")
print("direction:", "RIGHT" if (guess > last) == (real > last) else "WRONG")

plt.figure(figsize=(10, 5))
plt.plot(df["timestamps"].iloc[cut - 120:], df["close"].iloc[cut - 120:], label="What really happened", color="#2563eb")
plt.plot(y["timestamps"], pred["close"].values, label="Kronos forecast", color="#dc2626")
plt.axvline(y["timestamps"].iloc[0], color="#888", linestyle="--")
plt.legend()
plt.title(f"{csv}: the last {pred_len} candles, forecast vs real")
plt.tight_layout()
plt.savefig("forecast.png", dpi=120)
print("chart saved: forecast.png")
