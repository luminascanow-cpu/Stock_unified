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
cp .env.example .env
```

The default install uses the lightweight sentiment engine. To enable the
optional FinBERT model locally, install `requirements-ml.txt` instead and set
`FINBERT_ENABLED=true`. FinBERT is disabled by default on Render's free tier to
keep startup time and memory usage within the service limits.

Market prices are sourced from Yahoo Finance, so no broker token is required for live technical data. Set `NEWS_API_KEY` in `.env` only if you want the optional NewsAPI feed in addition to RSS sources.

### Zerodha Kite login

Set `KITE_API_KEY` and `KITE_API_SECRET` on the server, then register this
redirect URL in the Kite developer console:

```text
https://stock-monitor-pro.onrender.com/auth/kite/callback
```

The Android app starts the daily login with `POST /auth/kite/app-session`. This
returns a random app-session handle and a one-time Zerodha login URL. The
callback binds that handle to the successful login, exchanges the one-time
request token on the server, and never returns the Kite access token to the
browser. Check connection state at `/auth/kite/status` using the app-session
handle as a Bearer token. `/auth/kite/login` remains available for a manual
backend-only connection but does not authorize an Android quote session.

After the daily login, authorized `POST /api/kite/quotes` calls accept up to 250
validated NSE symbols and return normalized full-quote snapshots for the
Android dashboard. Requests are rate-limited per app session.
The response includes price, change, timestamp, OHLC, and cumulative session
volume; it never includes the Kite access token. Android overlays those fields
onto its native dashboard and keeps Yahoo Finance as a per-symbol fallback.

### GoCharting Premium footprint confirmations

The Android Matrix can combine its existing technical direction with fresh
GoCharting Premium order-flow alerts. Configure `GOCHARTING_WEBHOOK_TOKEN` on
the server and send the GoCharting plain-text webhook to:

```text
https://stock-monitor-pro.onrender.com/api/orderflow/gocharting/webhook
```

The webhook message is a JSON object containing the token, NSE symbol, BUY or
SELL signal, and interval. Signals expire after seven minutes by default; missing
or stale data is shown as `AWAITING DATA`, never inferred from OHLCV candles.
The selected Lens stock links directly to its GoCharting terminal chart. See
[`docs/GOCHARTING_ORDERFLOW_SETUP.md`](docs/GOCHARTING_ORDERFLOW_SETUP.md) for
the complete Premium alert setup.

## Run

```bash
# Start server
DASHBOARD_PORT=8000 python3 run.py

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
| `GET /api/broker/status` | Check current market data source |
| `POST /api/orderflow/gocharting/webhook` | Receive an authenticated GoCharting alert |
| `GET /api/orderflow/signals` | Read fresh order-flow confirmations by symbol |
| `GET /api/orderflow/status` | Check GoCharting receiver status |

## Config

Edit `config.yaml` for:
- Ticker lists
- Sector mappings
- Optional API keys (NewsAPI, etc.)
- Refresh intervals
