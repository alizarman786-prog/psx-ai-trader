from utils import load_stock, find_sr_levels, count_touches, get_volume_metrics, WATCHLIST
from datetime import date

print(f"PSX Trade Scanner : {date.today()}")
print("="*60)

def score_setup(symbol):
    df       = load_stock(symbol)
    current  = df["Close"].iloc[-1]
    prev     = df["Close"].iloc[-2]
    change   = ((current - prev) / prev) * 100
    vol      = get_volume_metrics(df)
    rvol     = vol["rvol"]

    resistance_levels, support_levels = find_sr_levels(df)

    r_above  = sorted([r for r in resistance_levels if r > current])
    s_below  = sorted([s for s in support_levels    if s < current], reverse=True)

    nearest_r = r_above[0] if r_above else None
    nearest_s = s_below[0] if s_below else None
    r_dist    = ((nearest_r - current) / current * 100) if nearest_r else None
    s_dist    = ((current - nearest_s) / current * 100) if nearest_s else None
    r_touches = count_touches(nearest_r, df["High"]) if nearest_r else 0
    s_touches = count_touches(nearest_s, df["Low"])  if nearest_s else 0

    score, setup_type, reason = 0, "NO SETUP", []

    # Volume (max 4 pts)
    if rvol >= 2.0:
        score += 4; reason.append("very high volume")
    elif rvol >= 1.5:
        score += 3; reason.append("high volume")
    elif rvol >= 1.0:
        score += 1; reason.append("average volume")
    else:
        reason.append("low volume")

    # Proximity to S/R (max 3 pts)
    near_r = nearest_r and r_dist <= 3.0
    near_s = nearest_s and s_dist <= 3.0

    if near_r or near_s:
        score += 3; reason.append("price at key level")
    elif nearest_r and r_dist <= 6.0:
        score += 1; reason.append("price near level")

    # Level strength (max 2 pts)
    best_touches = max(r_touches if near_r else 0, s_touches if near_s else 0)
    if best_touches >= 8:
        score += 2; reason.append(f"strong level ({best_touches} touches)")
    elif best_touches >= 4:
        score += 1; reason.append(f"moderate level ({best_touches} touches)")

    # Confluence (1 pt)
    if rvol >= 1.5 and change > 0 and near_r:
        score += 1; setup_type = "BREAKOUT";   reason.append("breakout attempt")
    elif rvol >= 1.5 and change < 0 and near_s:
        score += 1; setup_type = "BREAKDOWN";  reason.append("breakdown warning")
    elif near_s and change >= 0:
        setup_type = "BOUNCE";    reason.append("bounce from support")
    elif near_r and change <= 0:
        setup_type = "REJECTION"; reason.append("rejected at resistance")

    if score >= 8:
        rating = "STRONG"
    elif score >= 6:
        rating = "GOOD"
    elif score >= 4:
        rating = "WATCH"
    else:
        rating = "SKIP"

    return {
        "symbol": symbol, "price": current, "change": round(change, 2),
        "rvol": rvol, "score": score, "rating": rating, "setup": setup_type,
        "nearest_r": nearest_r, "nearest_s": nearest_s,
        "r_dist": round(r_dist, 1) if r_dist else None,
        "s_dist": round(s_dist, 1) if s_dist else None,
        "reason": ", ".join(reason)
    }

results = []
for symbol in WATCHLIST:
    try:
        results.append(score_setup(symbol))
    except Exception as e:
        print(f"✗ {symbol}: {e}")

for r in sorted(results, key=lambda x: x["score"], reverse=True):
    print(f"\n  [{r['rating']}]  {r['symbol']}  :  Score: {r['score']}/10  |  {r['setup']}")
    print(f"  Price: {r['price']:.2f} ({r['change']:+.1f}%)   RVOL: {r['rvol']:.2f}x")
    if r["nearest_r"]:
        print(f"  Resistance: {r['nearest_r']:.2f} ({r['r_dist']:+.1f}%)")
    if r["nearest_s"]:
        print(f"  Support:    {r['nearest_s']:.2f} ({r['s_dist']:-.1f}%)")
    print(f"  Reason: {r['reason']}")

print(f"\n{'='*60}")
print(f"  {sum(1 for r in results if r['score'] >= 6)} actionable setups found today")
print(f"{'='*60}")