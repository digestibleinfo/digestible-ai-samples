# Kronos sample pack

Scripts from the Digestible AI videos on [Kronos](https://github.com/shiyu-coder/Kronos), the open
foundation model for financial candlestick charts. Tested on Windows 11 with an NVIDIA RTX 5060 Ti.

Unpack `kronos-samples.zip` in the folder that holds `Kronos-master` (the repo's code, downloaded as a zip):

| File | What it does |
|---|---|
| `get_prices.py` | Downloads real price history: Bitcoin per hour (Binance public data) and Naspers per day (Yahoo Finance chart data). No account or key. |
| `forecast.py` | The README example on real data: hides the last candles, forecasts them, compares with what happened, saves `forecast.png`. |
| `backtest.py` | Scores Kronos on many past moments against the "price stays the same" baseline. `repeat` runs it three times to check consistency. |
| `speed.py` | Time and memory for one forecast with Kronos-mini, small and base, on the graphics card and the processor. |

```
python get_prices.py
python forecast.py btc_1h.csv
python backtest.py btc_1h.csv 24 40
python backtest.py npn_1d.csv 5 40
python backtest.py btc_1h.csv 24 40 repeat
python speed.py btc_1h.csv
```

This is a test of a research model, not financial advice. Kronos's own README says its
fine-tuning example is a demonstration, not a trading system.
