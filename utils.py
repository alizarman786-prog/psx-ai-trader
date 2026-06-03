import pandas as pd
import numpy as np

def load_stock(symbol):
    df = pd.read_csv(f"data/{symbol}.csv", index_col="Date", parse_dates=True)
    df.columns = [c.strip() for c in df.columns]
    return df

def find_sr_levels(df, window=10):
    highs = df["High"].values
    lows  = df["Low"].values
    dates = df.index

    swing_highs, swing_lows = [], []

    for i in range(window, len(df) - window):
        if highs[i] == max(highs[i - window: i + window + 1]):
            swing_highs.append((dates[i], highs[i]))
        if lows[i] == min(lows[i - window: i + window + 1]):
            swing_lows.append((dates[i], lows[i]))

    def cluster_levels(levels, tolerance=0.015):
        if not levels:
            return []
        prices = sorted([p for _, p in levels])
        clusters, group = [], [prices[0]]
        for price in prices[1:]:
            if (price - group[-1]) / group[-1] < tolerance:
                group.append(price)
            else:
                clusters.append(round(np.mean(group), 2))
                group = [price]
        clusters.append(round(np.mean(group), 2))
        return clusters

    return cluster_levels(swing_highs), cluster_levels(swing_lows)

def count_touches(level, price_series, tolerance=0.015, cooldown=10):
    touches, last_touch = 0, -cooldown
    for i, price in enumerate(price_series):
        if abs(price - level) / level < tolerance:
            if i - last_touch >= cooldown:
                touches += 1
                last_touch = i
    return touches

def get_volume_metrics(df, lookback=20):
    avg_vol   = df["Volume"].rolling(lookback).mean().iloc[-1]
    today_vol = df["Volume"].iloc[-1]
    rvol      = today_vol / avg_vol if avg_vol > 0 else 0
    expanding = df["Volume"].rolling(5).mean().iloc[-1] > avg_vol
    return {
        "volume":    int(today_vol),
        "avg_volume": int(avg_vol),
        "rvol":      round(rvol, 2),
        "expanding": expanding
    }

WATCHLIST = ["ENGRO", "FFC", "OGDC", "NCL", "LUCK", "HUBC", "TRG", "MARI", "MCB"]