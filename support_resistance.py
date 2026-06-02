import pandas as pd
import numpy as np
from datetime import date
print(f"Analysis as of: {date.today()}")

def load_stock(symbol):
    df = pd.read_csv(f"data/{symbol}.csv", index_col="Date", parse_dates=True)
    df.columns = [c.strip() for c in df.columns]
    return df

def find_sr_levels(symbol, window=10, min_touches=2):
    """
    Finds support and resistance levels using swing highs/lows.
    window      — how many candles either side to confirm a swing point
    min_touches — minimum times a level must be tested to count
    """
    df = load_stock(symbol)
    highs = df["High"].values
    lows  = df["Low"].values
    dates = df.index

    swing_highs = []
    swing_lows  = []

    # Find swing highs and lows
    for i in range(window, len(df) - window):
        if highs[i] == max(highs[i - window: i + window + 1]):
            swing_highs.append((dates[i], highs[i]))
        if lows[i] == min(lows[i - window: i + window + 1]):
            swing_lows.append((dates[i], lows[i]))

    # Cluster nearby levels together (within 1.5% of each other)
    def cluster_levels(levels, tolerance=0.015):
        if not levels:
            return []
        prices = sorted([p for _, p in levels])
        clusters = []
        group = [prices[0]]

        for price in prices[1:]:
            if (price - group[-1]) / group[-1] < tolerance:
                group.append(price)
            else:
                clusters.append(round(np.mean(group), 2))
                group = [price]
        clusters.append(round(np.mean(group), 2))
        return clusters

    resistance_levels = cluster_levels(swing_highs)
    support_levels    = cluster_levels(swing_lows)

    # Count how many times price touched each level
    current_price = df["Close"].iloc[-1]

    def count_touches(level, price_series, tolerance=0.015):
        return int(((price_series - level).abs() / level < tolerance).sum())

    print(f"\n{'='*50}")
    print(f"  {symbol}  |  Current price: {current_price:.2f}")
    print(f"{'='*50}")

    print(f"\n  RESISTANCE LEVELS (above current price)")
    print(f"  {'-'*40}")
    r_above = [r for r in resistance_levels if r > current_price]
    for level in sorted(r_above)[:5]:  # nearest 5
        touches = count_touches(level, df["High"])
        distance = ((level - current_price) / current_price) * 100
        strength = "STRONG" if touches >= 3 else "moderate" if touches == 2 else "weak"
        if touches >= min_touches:
            print(f"  {level:>10.2f}   {distance:>+6.1f}%   touches: {touches}   [{strength}]")

    print(f"\n  SUPPORT LEVELS (below current price)")
    print(f"  {'-'*40}")
    s_below = [s for s in support_levels if s < current_price]
    for level in sorted(s_below, reverse=True)[:5]:  # nearest 5
        touches = count_touches(level, df["Low"])
        distance = ((level - current_price) / current_price) * 100
        strength = "STRONG" if touches >= 3 else "moderate" if touches == 2 else "weak"
        if touches >= min_touches:
            print(f"  {level:>10.2f}   {distance:>+6.1f}%   touches: {touches}   [{strength}]")

    return support_levels, resistance_levels


# Run for all your stocks
WATCHLIST = ["ENGRO", "FFC", "OGDC", "NCL", "LUCK", "HUBC", "TRG", "MARI", "MCB"]

for symbol in WATCHLIST:
    try:
        find_sr_levels(symbol)
    except Exception as e:
        print(f"\n✗ {symbol}: {e}")