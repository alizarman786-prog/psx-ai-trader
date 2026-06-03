from utils import load_stock, get_volume_metrics, WATCHLIST
from datetime import date

print(f"Volume analysis as of: {date.today()}")

def analyze_volume(symbol):
    df      = load_stock(symbol)
    latest  = df.iloc[-1]
    prev    = df.iloc[-2]
    price   = latest["Close"]
    change  = ((latest["Close"] - prev["Close"]) / prev["Close"]) * 100
    vol     = get_volume_metrics(df)
    rvol    = vol["rvol"]

    if rvol >= 2.0:
        vol_signal = "VERY HIGH : strong institutional activity"
    elif rvol >= 1.5:
        vol_signal = "HIGH : above average activity"
    elif rvol >= 0.8:
        vol_signal = "NORMAL : nothing unusual"
    else:
        vol_signal = "LOW : avoid trading today"

    if rvol >= 1.5 and change > 0:
        confluence = "BULLISH : price up on high volume"
    elif rvol >= 1.5 and change < 0:
        confluence = "BEARISH : price down on high volume"
    elif rvol < 0.8 and change > 0:
        confluence = "WEAK RALLY : price up but low volume, suspect"
    elif rvol < 0.8 and change < 0:
        confluence = "WEAK SELLOFF : low volume drop, may recover"
    else:
        confluence = "NEUTRAL : no strong signal"

    print(f"\n{'='*52}")
    print(f"  {symbol:<6}  |  Price: {price:.2f}  ({change:+.1f}%)")
    print(f"{'='*52}")
    print(f"  Volume today : {vol['volume']:>12,}")
    print(f"  20d avg vol  : {vol['avg_volume']:>12,}")
    print(f"  RVOL         : {rvol:>12.2f}x")
    print(f"  Vol expanding: {'Yes' if vol['expanding'] else 'No'}")
    print(f"  Signal       : {vol_signal}")
    print(f"  Confluence   : {confluence}")

    return {"symbol": symbol, "price": price, "change_pct": round(change, 2),
            "rvol": rvol, "confluence": confluence}

results = []
for symbol in WATCHLIST:
    try:
        results.append(analyze_volume(symbol))
    except Exception as e:
        print(f"\n✗ {symbol}: {e}")

print(f"\n{'='*52}")
print(f"  TOP VOLUME SETUPS TODAY")
print(f"{'='*52}")
for i, r in enumerate(sorted(results, key=lambda x: x["rvol"], reverse=True), 1):
    print(f"  {i}. {r['symbol']:<6}  RVOL: {r['rvol']:.2f}x   {r['confluence']}")