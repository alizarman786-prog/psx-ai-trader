import json
import os
from datetime import date, datetime

SIGNALS_FILE = "signals.json"

def load_signals():
    if not os.path.exists(SIGNALS_FILE):
        return []
    with open(SIGNALS_FILE, "r") as f:
        return json.load(f)

def save_signal(symbol, setup, entry, stop_loss, target, confidence, notes=""):
    signals = load_signals()

    rr = round((target - entry) / (entry - stop_loss), 2) if entry != stop_loss else 0

    signal = {
        "id":          len(signals) + 1,
        "date":        str(date.today()),
        "time":        datetime.now().strftime("%H:%M"),
        "symbol":      symbol.upper(),
        "setup":       setup,
        "entry":       entry,
        "stop_loss":   stop_loss,
        "target":      target,
        "risk_reward": rr,
        "confidence":  confidence,
        "notes":       notes,
        "status":      "OPEN",
        "exit_price":  None,
        "exit_date":   None,
        "pnl_pct":     None,
        "outcome":     None
    }

    signals.append(signal)

    with open(SIGNALS_FILE, "w") as f:
        json.dump(signals, f, indent=2)

    print(f"\n  Signal saved: #{signal['id']} {symbol} {setup}")
    print(f"  Entry: {entry}  SL: {stop_loss}  Target: {target}  RR: {rr}x")
    return signal

def close_signal(signal_id, exit_price):
    signals = load_signals()

    for s in signals:
        if s["id"] == signal_id and s["status"] == "OPEN":
            s["exit_price"] = exit_price
            s["exit_date"]  = str(date.today())
            s["status"]     = "CLOSED"

            # Calculate P&L
            if s["setup"] in ["BREAKOUT", "BOUNCE"]:
                pnl = ((exit_price - s["entry"]) / s["entry"]) * 100
            else:
                pnl = ((s["entry"] - exit_price) / s["entry"]) * 100

            s["pnl_pct"] = round(pnl, 2)
            s["outcome"] = "WIN" if pnl > 0 else "LOSS"

            print(f"\n  Signal #{signal_id} closed")
            print(f"  Exit: {exit_price}  P&L: {pnl:+.2f}%  {s['outcome']}")
            break

    with open(SIGNALS_FILE, "w") as f:
        json.dump(signals, f, indent=2)

def print_summary():
    signals = load_signals()

    if not signals:
        print("No signals logged yet.")
        return

    open_signals   = [s for s in signals if s["status"] == "OPEN"]
    closed_signals = [s for s in signals if s["status"] == "CLOSED"]
    wins           = [s for s in closed_signals if s["outcome"] == "WIN"]
    losses         = [s for s in closed_signals if s["outcome"] == "LOSS"]

    win_rate = (len(wins) / len(closed_signals) * 100) if closed_signals else 0
    avg_pnl  = (sum(s["pnl_pct"] for s in closed_signals) / len(closed_signals)) if closed_signals else 0

    print(f"\n{'='*52}")
    print(f"  SIGNAL PERFORMANCE SUMMARY")
    print(f"{'='*52}")
    print(f"  Total signals : {len(signals)}")
    print(f"  Open          : {len(open_signals)}")
    print(f"  Closed        : {len(closed_signals)}")
    print(f"  Win rate      : {win_rate:.1f}%")
    print(f"  Avg P&L       : {avg_pnl:+.2f}%")

    if open_signals:
        print(f"\n  OPEN SIGNALS")
        print(f"  {'-'*40}")
        for s in open_signals:
            print(f"  #{s['id']} {s['symbol']:<6} {s['setup']:<12} "
                  f"Entry: {s['entry']}  SL: {s['stop_loss']}  "
                  f"Target: {s['target']}  RR: {s['risk_reward']}x")

    if closed_signals:
        print(f"\n  CLOSED SIGNALS")
        print(f"  {'-'*40}")
        for s in closed_signals:
            print(f"  #{s['id']} {s['symbol']:<6} {s['setup']:<12} "
                  f"P&L: {s['pnl_pct']:+.2f}%  {s['outcome']}")

if __name__ == "__main__":
    print_summary()