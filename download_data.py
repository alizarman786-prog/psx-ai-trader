import yfinance as yf
import pandas as pd
import os
import time
from datetime import date

WATCHLIST = {
    "ENGRO":  "ENGRO.KA",
    "FFC":    "FFC.KA",
    "OGDC":   "OGDC.KA",
    "NCL":    "NCL.KA",
    "LUCK":   "LUCK.KA",
    "HUBC":   "HUBC.KA",
    "TRG":    "TRG.KA",
    "MARI":   "MARI.KA",
    "MCB":    "MCB.KA",
}

os.makedirs("data", exist_ok=True)

today      = date.today()
start_date = "2015-01-01"   # ~10 years back, Yahoo will give whatever it has

success = []
failed  = []

for name, ticker in WATCHLIST.items():
    try:
        df = yf.download(ticker, start=start_date, end=today, progress=False)

        if df.empty:
            print(f"✗ {name}: no data returned")
            failed.append(name)
            continue

        df.columns = [col[0] for col in df.columns]
        df.to_csv(f"data/{name}.csv")
        print(f"✓ {name}: {len(df)} rows saved  ({df.index[0].date()} → {df.index[-1].date()})")
        success.append(name)

    except Exception as e:
        print(f"✗ {name}: {e}")
        failed.append(name)

    time.sleep(0.5)

print(f"\n--- Done ---")
print(f"Saved:  {success}")
print(f"Failed: {failed}")