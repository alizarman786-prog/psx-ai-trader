from groq import Groq
from dotenv import load_dotenv
import os
import json
from datetime import date
from utils import load_stock, find_sr_levels, count_touches, get_volume_metrics, WATCHLIST

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_scan_data():
    results = []
    for symbol in WATCHLIST:
        try:
            df       = load_stock(symbol)
            current  = df["Close"].iloc[-1]
            prev     = df["Close"].iloc[-2]
            change   = ((current - prev) / prev) * 100
            vol      = get_volume_metrics(df)
            rvol     = vol["rvol"]

            res, sup  = find_sr_levels(df)
            r_above   = sorted([r for r in res if r > current])
            s_below   = sorted([s for s in sup if s < current], reverse=True)

            nearest_r = r_above[0] if r_above else None
            nearest_s = s_below[0] if s_below else None
            r_dist    = ((nearest_r - current) / current * 100) if nearest_r else None
            s_dist    = ((current - nearest_s) / current * 100) if nearest_s else None
            r_touches = count_touches(nearest_r, df["High"]) if nearest_r else 0
            s_touches = count_touches(nearest_s, df["Low"])  if nearest_s else 0

            score, setup_type = 0, "NO SETUP"

            if rvol >= 2.0:   score += 4
            elif rvol >= 1.5: score += 3
            elif rvol >= 1.0: score += 1

            near_r = nearest_r and r_dist <= 3.0
            near_s = nearest_s and s_dist <= 3.0

            if near_r or near_s:              score += 3
            elif nearest_r and r_dist <= 6.0: score += 1

            best_touches = max(r_touches if near_r else 0,
                               s_touches if near_s else 0)
            if best_touches >= 8:   score += 2
            elif best_touches >= 4: score += 1

            if rvol >= 1.5 and change > 0 and near_r:
                score += 1; setup_type = "BREAKOUT"
            elif rvol >= 1.5 and change < 0 and near_s:
                score += 1; setup_type = "BREAKDOWN"
            elif near_s and change >= 0:
                setup_type = "BOUNCE"
            elif near_r and change <= 0:
                setup_type = "REJECTION"

            if score >= 8:   rating = "STRONG"
            elif score >= 6: rating = "GOOD"
            elif score >= 4: rating = "WATCH"
            else:            rating = "SKIP"

            results.append({
                "symbol":     symbol,
                "price":      round(current, 2),
                "change_pct": round(change, 2),
                "rvol":       round(rvol, 2),
                "score":      score,
                "rating":     rating,
                "setup":      setup_type,
                "resistance": round(nearest_r, 2) if nearest_r else None,
                "support":    round(nearest_s, 2) if nearest_s else None,
                "r_distance": round(r_dist, 1) if r_dist else None,
                "s_distance": round(s_dist, 1) if s_dist else None,
                "r_touches":  r_touches,
                "s_touches":  s_touches,
            })

        except Exception as e:
            print(f"Error scanning {symbol}: {e}")

    return sorted(results, key=lambda x: x["score"], reverse=True)

def format_scan_for_prompt(results):
    lines = [f"PSX SCAN RESULTS — {date.today()}", "="*50]
    for r in results:
        lines.append(f"\n{r['rating']} | {r['symbol']} | Score: {r['score']}/10 | {r['setup']}")
        lines.append(f"Price: {r['price']} ({r['change_pct']:+.1f}%) | RVOL: {r['rvol']}x")
        if r["resistance"]:
            lines.append(f"Resistance: {r['resistance']} ({r['r_distance']:+.1f}%, {r['r_touches']} touches)")
        if r["support"]:
            lines.append(f"Support: {r['support']} ({r['s_distance']:.1f}%, {r['s_touches']} touches)")
    return "\n".join(lines)

def ask_groq():
    print(f"PSX AI Trader (Groq) — {date.today()}")
    print("="*60)
    print("Running scan...")

    results    = get_scan_data()
    scan_text  = format_scan_for_prompt(results)
    actionable = sum(1 for r in results if r["score"] >= 6)

    print(f"Scan complete — {actionable} actionable setups found")
    print("Asking Groq for analysis...")
    print("="*60)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are an expert PSX (Pakistan Stock Exchange) technical analyst.
You will receive scan data showing trade setups scored by an algorithm.

When analyzing setups:
- Focus only on STRONG and GOOD rated setups
- For each actionable setup provide:
  * Trade direction (BUY or SELL)
  * Entry price (specific level)
  * Stop loss level and why
  * Target level (next S/R)
  * Risk/reward ratio
  * Confidence and reasoning

PSX specific rules:
- T+2 settlement
- Trading hours 9:30 AM to 3:30 PM PKT
- Be conservative with small caps
- Always state invalidation level
- Keep risk per trade to 1-2% of capital

Be direct and specific. No fluff."""
            },
            {
                "role": "user",
                "content": f"Here is today's PSX scan data:\n\n{scan_text}\n\nSetups are already ranked by score from highest to lowest. Focus on the top ranked setups first. Give me full trade plans for all STRONG and GOOD rated setups, then briefly mention WATCH setups worth monitoring."
            }
        ],
        max_tokens=2000
    )

    print("\nGroq Analysis:")
    print("="*60)
    print(response.choices[0].message.content)

if __name__ == "__main__":
    ask_groq()