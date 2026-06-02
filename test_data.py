import yfinance as yf
import pandas as pd

# PSX stocks on Yahoo Finance use .KA suffix
df = yf.download("ENGRO.KA", start="2024-01-01", end="2024-12-31")

print(df.head(10))
print(f"\nTotal rows: {len(df)}")
print(f"Columns: {df.columns.tolist()}")