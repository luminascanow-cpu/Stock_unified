# 🚀 Unified Stock Analysis Platform

Merges **technical analysis** (PSAR + Bill Williams AC) with **sentiment analysis** (NLP + news) for Indian stocks.

## Features

- **Confluence Signals**: Technical + Sentiment → Weighted conviction scores
- **138 Indian tickers** (NSE/BSE)
- **Real-time data**: Yahoo Finance + News RSS feeds
- **FastAPI server** on port 8080
- **CLI interface** for quick analysis
- **Backtesting engine** for both signal types
- **Alert system** (technical crossovers + breaking news)

## Setup

```bash
cd ~/Desktop/stock_unified
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
# Start server
python3 main.py

# CLI usage
python3 cli.py --refresh --sectors --alerts
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /api/stocks` | All stocks with signals |
| `GET /api/ticker/<symbol>` | Single stock detail |
| `GET /api/news` | Latest news |
| `GET /api/sectors` | Sector analysis |
| `GET /api/alerts` | Active alerts |

## Config

Edit `config.yaml` for:
- Ticker lists
- Sector mappings
- API keys (NewsAPI, etc.)
- Refresh intervals
