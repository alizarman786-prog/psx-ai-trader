import anthropic
import json
import subprocess
import sys
from datetime import date
from dotenv import load_dotenv
import os

load_dotenv()

def ask_claude():
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Start MCP server as subprocess
    server = subprocess.Popen(
        [sys.executable, "mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    print(f"PSX AI Trader — {date.today()}")
    print("="*60)
    print("Connecting Claude to your PSX data...")

    response = client.beta.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        betas=["mcp-client-2025-04-04"],
        mcp_servers=[
            {
                "type": "stdio",
                "command": sys.executable,
                "args": ["mcp_server.py"],
                "name": "psx-trader"
            }
        ],
        system="""You are an expert PSX (Pakistan Stock Exchange) technical analyst.
You have access to real market data tools for stocks on the Karachi exchange.

When analyzing setups:
- Always call scan_all first to see the full picture
- Focus on STRONG and GOOD rated setups only
- For each actionable setup provide:
  * Trade type (BUY breakout / SELL rejection / BUY bounce)
  * Entry price (specific level)
  * Stop loss (below support for buys, above resistance for sells)
  * Target (next S/R level)
  * Risk/reward ratio
  * Confidence level and why

PSX specific rules:
- T+2 settlement — factor this into timing
- Trading hours 9:30 AM to 3:30 PM PKT
- Be conservative with small caps — wider spreads
- Always mention invalidation level
- Keep risk per trade to 1-2% of capital

Speak directly and confidently. No fluff.""",
        messages=[
            {
                "role": "user",
                "content": "Scan all PSX stocks in my watchlist and give me today's best trade setups with full entry, stop loss, and target levels."
            }
        ]
    )

    print("\nClaude's Analysis:")
    print("="*60)
    for block in response.content:
        if hasattr(block, "text"):
            print(block.text)

    server.terminate()

if __name__ == "__main__":
    ask_claude()