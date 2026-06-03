import pandas as pd
import numpy as np
from datetime import date

print(f"Volume analysis as of: {date.today()}")

def analyze_volume(symbol, lookback=20):
    df = pd.read_csv(f"data/{symbol}.csv", index_col="Date", parse_dates=True)
    df.columns = [c.strip() for c in df.columns]

    # Relative volume : today vs 20 day average
    df["avg_volume"]  = df["Volume"].rolling(lookback).mean()
    df["rvol"]        = df["Volume"] / df["avg_volume"]

    # Volume trend : is volume expanding or contracting?
    df["vol_5d_avg"]  = df["Volume"].rolling(5).mean()
    df["vol_expanding"] = df["vol_5d_avg"] > df["avg_volume"]

    # Price range as % : measures volatility
    df["range_pct"]   = (df["High"] - df["Low"]) / df["Close"] * 100

    # Latest values
    latest            = df.iloc[-1]
    prev              = df.iloc[-2]

    rvol              = latest["rvol"]
    volume            = int(latest["Volume"])
    avg_vol           = int(latest["avg_volume"])
    expanding         = latest["vol_expanding"]
    price             = latest["Close"]
    change_pct        = ((latest["Close"] - prev["Close"]) / prev["Close"]) * 100

    # Volume signal
    if rvol >= 2.0:
        vol_signal = "VERY HIGH : strong institutional activity"
    elif rvol >= 1.5:
        vol_signal = "HIGH : above average activity"
    elif rvol >= 0.8:
        vol_signal = "NORMAL : nothing unusual"
    else:
        vol_signal = "LOW : avoid trading today"

    # Price + volume confluence
    if rvol >= 1.5 and change_pct > 0:
        confluence = "BULLISH : price up on high volume"
    elif rvol >= 1.5 and change_pct < 0:
        confluence = "BEARISH : price down on high volume"
    elif rvol < 0.8 and change_pct > 0:
        confluence = "WEAK RALLY : price up but low volume, suspect"
    elif rvol < 0.8 and change_pct < 0:
        confluence = "WEAK SELLOFF : low volume drop, may recover"
    else:
        confluence = "NEUTRAL : no strong signal"

    print(f"\n{'='*52}")
    print(f"  {symbol:<6}  |  Price: {price:.2f}  ({change_pct:+.1f}%)")
    print(f"{'='*52}")
    print(f"  Volume today : {volume:>12,}")
    print(f"  20d avg vol  : {avg_vol:>12,}")
    print(f"  RVOL         : {rvol:>12.2f}x")
    print(f"  Vol expanding: {'Yes' if expanding else 'No'}")
    print(f"  Signal       : {vol_signal}")
    print(f"  Confluence   : {confluence}")

    return {
        "symbol":     symbol,
        "price":      price,
        "change_pct": round(change_pct, 2),
        "rvol":       round(rvol, 2),
        "volume":     volume,
        "avg_volume": avg_vol,
        "expanding":  expanding,
        "confluence": confluence
    }


WATCHLIST = ["ENGRO", "FFC", "OGDC", "NCL", "LUCK", "HUBC", "TRG", "MARI", "MCB"]

results = []
for symbol in WATCHLIST:
    try:
        r = analyze_volume(symbol)
        results.append(r)
    except Exception as e:
        print(f"\n✗ {symbol}: {e}")

# Summary ranking, best volume setups today
print(f"\n{'='*52}")
print(f"  TOP VOLUME SETUPS TODAY")
print(f"{'='*52}")
ranked = sorted(results, key=lambda x: x["rvol"], reverse=True)
for i, r in enumerate(ranked, 1):
    print(f"  {i}. {r['symbol']:<6}  RVOL: {r['rvol']:.2f}x   {r['confluence']}")