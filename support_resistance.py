from utils import load_stock, find_sr_levels, count_touches, WATCHLIST
from datetime import date

print(f"Analysis as of: {date.today()}")

def print_sr_levels(symbol, window=10, min_touches=2):
    df            = load_stock(symbol)
    current_price = df["Close"].iloc[-1]
    resistance_levels, support_levels = find_sr_levels(df, window)

    print(f"\n{'='*50}")
    print(f"  {symbol}  |  Current price: {current_price:.2f}")
    print(f"{'='*50}")

    print(f"\n  RESISTANCE LEVELS (above current price)")
    print(f"  {'-'*40}")
    for level in sorted([r for r in resistance_levels if r > current_price])[:5]:
        touches  = count_touches(level, df["High"])
        distance = ((level - current_price) / current_price) * 100
        strength = "STRONG" if touches >= 3 else "moderate" if touches == 2 else "weak"
        if touches >= min_touches:
            print(f"  {level:>10.2f}   {distance:>+6.1f}%   touches: {touches}   [{strength}]")

    print(f"\n  SUPPORT LEVELS (below current price)")
    print(f"  {'-'*40}")
    for level in sorted([s for s in support_levels if s < current_price], reverse=True)[:5]:
        touches  = count_touches(level, df["Low"])
        distance = ((level - current_price) / current_price) * 100
        strength = "STRONG" if touches >= 3 else "moderate" if touches == 2 else "weak"
        if touches >= min_touches:
            print(f"  {level:>10.2f}   {distance:>+6.1f}%   touches: {touches}   [{strength}]")

for symbol in WATCHLIST:
    try:
        print_sr_levels(symbol)
    except Exception as e:
        print(f"\n✗ {symbol}: {e}")