"""Downloads real price history to CSV files that Kronos can read (no account or key needed).

    python get_prices.py

btc_1h.csv      Bitcoin in US dollars, one candle per hour, the last 2000 hours (Binance public data)
npn_1d.csv      Naspers (JSE: NPN) in rand, one candle per day, the last 5 years (Yahoo Finance chart data)
"""

import time

import pandas as pd
import requests

COLUMNS = ["timestamps", "open", "high", "low", "close", "volume", "amount"]


def bitcoin_hourly(hours: int = 2000) -> pd.DataFrame:
    rows, end = [], None
    while len(rows) < hours:
        params = {"symbol": "BTCUSDT", "interval": "1h", "limit": 1000}
        if end:
            params["endTime"] = end
        batch = requests.get("https://data-api.binance.vision/api/v3/klines", params=params, timeout=30).json()
        rows = batch + rows
        end = batch[0][0] - 1
        time.sleep(0.2)
    df = pd.DataFrame(rows[-hours:]).iloc[:, :8]
    df.columns = ["t", "open", "high", "low", "close", "volume", "close_t", "amount"]
    df["timestamps"] = pd.to_datetime(df["t"], unit="ms")
    return df[COLUMNS].astype({c: float for c in COLUMNS[1:]})


def jse_daily(symbol: str = "NPN.JO") -> pd.DataFrame:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    data = requests.get(url, params={"range": "5y", "interval": "1d"}, headers={"User-Agent": "Mozilla/5.0"}, timeout=30).json()
    res = data["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    df = pd.DataFrame({"timestamps": pd.to_datetime(res["timestamp"], unit="s").normalize(), "open": q["open"], "high": q["high"],
                       "low": q["low"], "close": q["close"], "volume": q["volume"]}).dropna()
    df = df[df["volume"] > 0]
    df["amount"] = df["volume"] * df["close"]
    return df[COLUMNS].reset_index(drop=True)


if __name__ == "__main__":
    btc = bitcoin_hourly()
    btc.to_csv("btc_1h.csv", index=False)
    print(f"btc_1h.csv  {len(btc)} hours  {btc.timestamps.iloc[0]} to {btc.timestamps.iloc[-1]}  last close {btc.close.iloc[-1]:,.2f} USD")
    npn = jse_daily()
    npn.to_csv("npn_1d.csv", index=False)
    print(f"npn_1d.csv  {len(npn)} days   {npn.timestamps.iloc[0].date()} to {npn.timestamps.iloc[-1].date()}  last close {npn.close.iloc[-1]:,.0f} (cents)")
