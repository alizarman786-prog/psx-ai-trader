# PSX AI Trader

An AI-powered trading assistant for the Pakistan Stock Exchange (PSX) built with Claude AI and MCP (Model Context Protocol).

The system analyzes historical price charts, detects support and resistance levels, scores trade setups using volume confirmation, and generates actionable trade signals with entry, stop-loss, and target levels.

---

## What it does

- Pulls 10 years of OHLCV data for PSX stocks via Yahoo Finance
- Detects support and resistance levels using swing high/low analysis
- Scores every setup out of 10 based on volume and proximity to key levels
- Connects Claude AI via MCP to generate written trade analysis
- Logs every signal with entry, stop-loss, target, and outcome tracking

---

## Project structure
PSX_MCP/
├── utils.py              # Shared functions (data loading, S/R, volume)
├── download_data.py      # Initial historical data download
├── refresh_data.py       # Daily data updater (run every morning)
├── support_resistance.py # S/R level detector and printer
├── volume_analysis.py    # Volume metrics and signals
├── scanner.py            # Combined trade setup scorer
├── mcp_server.py         # MCP server exposing tools to Claude
├── claude_trader.py      # Claude AI integration and analysis
├── signal_logger.py      # Trade signal tracker and performance log
├── data/                 # Historical OHLCV CSVs (gitignored)
└── signals.json          # Signal log (auto-generated)

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/alizarman786-prog/psx-ai-trader.git
cd psx-ai-trader
```

### 2. Install dependencies
```bash
pip install yfinance pandas numpy mcp anthropic python-dotenv
```

### 3. Download historical data
```bash
python download_data.py
```

### 4. Add your Anthropic API key
Create a `.env` file in the project root:
ANTHROPIC_API_KEY=sk-ant-your-key-here
Get your key at console.anthropic.com

---

## Daily workflow

```bash
# 1. Update data to latest close
python refresh_data.py

# 2. Run the scanner to see today's setups
python scanner.py

# 3a. Ask Claude for full analysis (requires Anthropic API credits)
python claude_trader.py

# 3b. Ask Groq for full analysis (free alternative)
python groq_trader.py
```

## Watchlist

Currently tracking 9 PSX stocks:

| Symbol | Company | Sector |
|--------|---------|--------|
| ENGRO | Engro Corporation | Fertilizer / Diversified |
| FFC | Fauji Fertilizer | Fertilizer |
| OGDC | Oil & Gas Dev. Corp | Energy |
| NCL | Nishat Chunian | Textile |
| LUCK | Lucky Cement | Cement |
| HUBC | Hub Power Company | Power |
| TRG | TRG Pakistan | Technology |
| MARI | Mari Petroleum | Energy |
| MCB | MCB Bank | Banking |

---

## Signal tracking

Log a trade signal after Claude analysis:
```python
from signal_logger import save_signal
save_signal("TRG", "BREAKOUT", 74.39, 72.33, 79.93, "HIGH", "Broke resistance on 4x volume")
```

Close a signal when trade is done:
```python
from signal_logger import close_signal
close_signal(1, 79.93)
```

View performance summary:
```bash
python signal_logger.py
```

---

## How the scoring works

Each setup is scored out of 10:

| Factor | Points |
|--------|--------|
| Volume 2x+ above average | 4 |
| Volume 1.5x above average | 3 |
| Price within 3% of S/R level | 3 |
| Level tested 8+ times historically | 2 |
| Price + volume confluence | 1 |

Scores of 8+ are STRONG, 6+ are GOOD, 4+ are WATCH, below 4 are SKIP.

---

## Disclaimer

This tool is for educational and research purposes only. It does not constitute financial advice. Trading involves significant risk, always do your own research and never risk more than you can afford to lose. PSX specific risks include thin liquidity in small caps and T+2 settlement.

---

## Built with

- [Claude AI](https://anthropic.com) — trade analysis and reasoning via Anthropic API
- [Groq](https://groq.com) — free alternative AI analysis using LLaMA 3.3 70B
- [MCP](https://modelcontextprotocol.io) — tool protocol connecting Claude to market data
- [yfinance](https://github.com/ranaroussi/yfinance) — PSX historical data
- [pandas](https://pandas.pydata.org) — data processing
