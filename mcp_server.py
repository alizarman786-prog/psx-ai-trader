import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from utils import load_stock, find_sr_levels, count_touches, get_volume_metrics, WATCHLIST

app = Server("psx-trader")

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_sr_levels",
            description="Get support and resistance levels for a PSX stock",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol e.g. TRG, ENGRO, LUCK"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_volume_analysis",
            description="Get volume metrics and signals for a PSX stock",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol e.g. TRG, ENGRO, LUCK"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_trade_score",
            description="Get a trade setup score and analysis for a PSX stock",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol e.g. TRG, ENGRO, LUCK"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="scan_all",
            description="Scan all stocks and return ranked trade setups for today",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):

    # --- TOOL 1: S/R Levels ---
    if name == "get_sr_levels":
        symbol = arguments["symbol"].upper()
        try:
            df            = load_stock(symbol)
            current       = df["Close"].iloc[-1]
            res, sup      = find_sr_levels(df)

            r_above = []
            for level in sorted([r for r in res if r > current])[:5]:
                touches  = count_touches(level, df["High"])
                distance = ((level - current) / current) * 100
                if touches >= 2:
                    r_above.append({
                        "level":    level,
                        "distance": round(distance, 2),
                        "touches":  touches
                    })

            s_below = []
            for level in sorted([s for s in sup if s < current], reverse=True)[:5]:
                touches  = count_touches(level, df["Low"])
                distance = ((level - current) / current) * 100
                if touches >= 2:
                    s_below.append({
                        "level":    level,
                        "distance": round(distance, 2),
                        "touches":  touches
                    })

            result = {
                "symbol":      symbol,
                "price":       round(current, 2),
                "resistance":  r_above,
                "support":     s_below
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    # --- TOOL 2: Volume Analysis ---
    elif name == "get_volume_analysis":
        symbol = arguments["symbol"].upper()
        try:
            df     = load_stock(symbol)
            latest = df.iloc[-1]
            prev   = df.iloc[-2]
            price  = latest["Close"]
            change = ((latest["Close"] - prev["Close"]) / prev["Close"]) * 100
            vol    = get_volume_metrics(df)
            rvol   = vol["rvol"]

            if rvol >= 2.0:
                signal = "VERY HIGH - strong institutional activity"
            elif rvol >= 1.5:
                signal = "HIGH - above average activity"
            elif rvol >= 0.8:
                signal = "NORMAL - nothing unusual"
            else:
                signal = "LOW - avoid trading today"

            if rvol >= 1.5 and change > 0:
                confluence = "BULLISH - price up on high volume"
            elif rvol >= 1.5 and change < 0:
                confluence = "BEARISH - price down on high volume"
            elif rvol < 0.8 and change > 0:
                confluence = "WEAK RALLY - suspect move"
            elif rvol < 0.8 and change < 0:
                confluence = "WEAK SELLOFF - may recover"
            else:
                confluence = "NEUTRAL"

            result = {
                "symbol":      symbol,
                "price":       round(price, 2),
                "change_pct":  round(change, 2),
                "volume":      vol["volume"],
                "avg_volume":  vol["avg_volume"],
                "rvol":        rvol,
                "expanding":   vol["expanding"],
                "signal":      signal,
                "confluence":  confluence
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    # --- TOOL 3: Trade Score ---
    elif name == "get_trade_score":
        symbol = arguments["symbol"].upper()
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

            score, setup_type, reason = 0, "NO SETUP", []

            if rvol >= 2.0:
                score += 4; reason.append("very high volume")
            elif rvol >= 1.5:
                score += 3; reason.append("high volume")
            elif rvol >= 1.0:
                score += 1; reason.append("average volume")
            else:
                reason.append("low volume")

            near_r = nearest_r and r_dist <= 3.0
            near_s = nearest_s and s_dist <= 3.0

            if near_r or near_s:
                score += 3; reason.append("price at key level")
            elif nearest_r and r_dist <= 6.0:
                score += 1; reason.append("price near level")

            best_touches = max(r_touches if near_r else 0,
                               s_touches if near_s else 0)
            if best_touches >= 8:
                score += 2; reason.append(f"strong level ({best_touches} touches)")
            elif best_touches >= 4:
                score += 1; reason.append(f"moderate level ({best_touches} touches)")

            if rvol >= 1.5 and change > 0 and near_r:
                score += 1; setup_type = "BREAKOUT"
            elif rvol >= 1.5 and change < 0 and near_s:
                score += 1; setup_type = "BREAKDOWN"
            elif near_s and change >= 0:
                setup_type = "BOUNCE"
            elif near_r and change <= 0:
                setup_type = "REJECTION"

            if score >= 8:
                rating = "STRONG"
            elif score >= 6:
                rating = "GOOD"
            elif score >= 4:
                rating = "WATCH"
            else:
                rating = "SKIP"

            result = {
                "symbol":     symbol,
                "price":      round(current, 2),
                "change_pct": round(change, 2),
                "rvol":       rvol,
                "score":      score,
                "rating":     rating,
                "setup":      setup_type,
                "nearest_resistance": nearest_r,
                "nearest_support":    nearest_s,
                "r_distance":  round(r_dist, 2) if r_dist else None,
                "s_distance":  round(s_dist, 2) if s_dist else None,
                "r_touches":   r_touches,
                "s_touches":   s_touches,
                "reason":      reason
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    # --- TOOL 4: Scan All ---
    elif name == "scan_all":
        try:
            all_results = []
            for symbol in WATCHLIST:
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

                if near_r or near_s:  score += 3
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

                all_results.append({
                    "symbol":  symbol,
                    "price":   round(current, 2),
                    "change":  round(change, 2),
                    "rvol":    rvol,
                    "score":   score,
                    "rating":  rating,
                    "setup":   setup_type,
                    "nearest_resistance": nearest_r,
                    "nearest_support":    nearest_s,
                })

            all_results = sorted(all_results, key=lambda x: x["score"], reverse=True)
            return [TextContent(type="text", text=json.dumps(all_results, indent=2))]

        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream,
                      app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())