import yfinance as yf
import pandas as pd
import os
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

def refresh():
    print(f"Refreshing PSX data : {date.today()}")
    print("="*50)

    os.makedirs("data", exist_ok=True)
    success, failed = [], []

    for name, ticker in WATCHLIST.items():
        try:
            # Load existing data
            path = f"data/{name}.csv"
            if os.path.exists(path):
                existing = pd.read_csv(path, index_col="Date", parse_dates=True)
                last_date = existing.index[-1].date()
                start     = last_date.strftime("%Y-%m-%d")
            else:
                existing  = None
                start     = "2015-01-01"

            # Download only new data since last update
            new_df = yf.download(ticker, start=start, end=date.today(), progress=False)

            if new_df.empty:
                print(f"  : {name}: already up to date")
                success.append(name)
                continue

            new_df.columns = [col[0] for col in new_df.columns]

            # Merge with existing
            if existing is not None:
                combined = pd.concat([existing, new_df])
                combined = combined[~combined.index.duplicated(keep="last")]
                combined = combined.sort_index()
            else:
                combined = new_df

            combined.to_csv(path)
            print(f"  + {name}: updated to {combined.index[-1].date()} ({len(combined)} rows total)")
            success.append(name)

        except Exception as e:
            print(f"  x {name}: {e}")
            failed.append(name)

    print(f"\n  Done : {len(success)} updated, {len(failed)} failed")
    if failed:
        print(f"  Failed: {failed}")

if __name__ == "__main__":
    refresh()