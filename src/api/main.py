from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from typing import List, Optional, Dict
from urllib.parse import parse_qs
import asyncio
import json
import io
import csv
import os
import logging

from ..services.prediction_engine_v2 import prediction_engine_v2
from ..services.nse_service import nse_service, market_hours_service
from ..services.india_specific import india_service
from ..services.alert_service import alert_manager
from ..services.scheduler_service import market_hours_scheduler
from ..services.kite_auth_service import kite_auth_service, KiteAuthError
from ..models.models import DashboardData
from ..utils.config import config

prediction_engine = prediction_engine_v2
dashboard_data: DashboardData = None
news_data = []
websocket_connections: List[WebSocket] = []
logger = logging.getLogger(__name__)

portfolio_data: List[dict] = []
watchlist: List[str] = []
fcm_tokens: Dict[str, dict] = {}


async def init_data_task():
    global dashboard_data
    try:
        dashboard_data = await prediction_engine.refresh_data()
    except Exception as e:
        print(f"Initial data load failed: {e}")


async def init_news_task():
    global news_data
    try:
        news_data = await prediction_engine.refresh_news(force=True)
    except Exception as e:
        logger.error("Initial news load failed: %s", e)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global dashboard_data
    # Fire and forget the first load so Cloud Run binds port immediately
    asyncio.create_task(init_data_task())
    asyncio.create_task(init_news_task())

    asyncio.create_task(periodic_refresh())
    asyncio.create_task(periodic_news_refresh())
    asyncio.create_task(websocket_broadcast())

    market_hours_scheduler.start()

    yield

    market_hours_scheduler.stop()


async def periodic_refresh():
    global dashboard_data
    while True:
        await asyncio.sleep(config.app.get('refresh_interval', 300))

        if market_hours_service.should_run_scheduler():
            try:
                dashboard_data = await prediction_engine.refresh_data()
                await asyncio.gather(
                    *(alert_manager.process_alert(alert) for alert in dashboard_data.alerts),
                    return_exceptions=True,
                )
                logger.info("Data refreshed during market hours")
            except Exception as e:
                logger.error("Periodic market refresh failed: %s", e)


async def periodic_news_refresh():
    global news_data
    while True:
        await asyncio.sleep(config.app.get('news_refresh_interval', 60))
        try:
            news_data = await prediction_engine.refresh_news(force=True)
        except Exception as e:
            logger.error("Periodic news refresh failed: %s", e)


async def websocket_broadcast():
    global dashboard_data
    while True:
        await asyncio.sleep(30)
        if websocket_connections and dashboard_data:
            data = {
                'type': 'update',
                'last_updated': dashboard_data.last_updated.isoformat(),
                'alerts_count': len(dashboard_data.alerts),
                'news_count': len(dashboard_data.latest_news),
                'market_status': market_hours_service.is_market_open()
            }
            for ws in websocket_connections:
                try:
                    await ws.send_json(data)
                except:
                    pass


def create_app() -> FastAPI:
    app = FastAPI(
        title=config.app.get('name', 'GeoPolitical Stock Monitor'),
        version=config.app.get('version', '2.0.0'),
        lifespan=lifespan
    )
    return app


app = create_app()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/dashboard")
async def get_dashboard():
    global dashboard_data
    if dashboard_data is None:
        # Prevent stampeding broker/news providers if the server is still booting
        raise HTTPException(
            status_code=503,
            detail="The AI engine is still cold-booting and downloading market data. Please refresh in 30-60 seconds."
        )
    return dashboard_data


@app.get("/api/news")
async def get_news():
    global dashboard_data, news_data
    if news_data:
        return news_data
    if dashboard_data:
        return dashboard_data.latest_news
    return []


@app.get("/api/news/status")
async def get_news_status():
    return prediction_engine.news_service.last_fetch_status


@app.get("/api/sectors")
async def get_sectors():
    global dashboard_data
    if dashboard_data:
        return dashboard_data.sector_analysis
    return []


@app.get("/api/predictions")
async def get_predictions():
    global dashboard_data
    if dashboard_data:
        return dashboard_data.top_predictions
    return []


@app.get("/api/alerts")
async def get_alerts():
    global dashboard_data
    if dashboard_data:
        return dashboard_data.alerts
    return []


@app.post("/api/refresh")
async def refresh_data():
    global dashboard_data
    dashboard_data = await prediction_engine.refresh_data()
    return {"status": "success", "last_updated": dashboard_data.last_updated.isoformat()}


@app.get("/api/broker/status")
async def broker_status():
    kite_status = kite_auth_service.status()
    return {
        **kite_status,
        "source": "Zerodha Kite" if kite_status["authenticated"] else "Yahoo Finance",
        "fallback_source": "Yahoo Finance",
        "login_url": "/auth/kite/login" if kite_status["configured"] else None,
    }


@app.get("/auth/kite/login")
async def kite_login():
    try:
        response = RedirectResponse(kite_auth_service.create_login_url(), status_code=302)
        response.headers["Cache-Control"] = "no-store"
        return response
    except KiteAuthError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/auth/kite/callback", response_class=HTMLResponse)
async def kite_callback(
    request: Request,
    request_token: Optional[str] = None,
    status: Optional[str] = None,
):
    state = request.query_params.get("state")
    if not state:
        redirect_params = request.query_params.get("redirect_params", "")
        state = parse_qs(redirect_params).get("state", [None])[0]
    try:
        kite_auth_service.validate_state(state)
        if status and status.lower() != "success":
            raise KiteAuthError("Kite login was not completed successfully.")
        await kite_auth_service.exchange_request_token(request_token or "")
    except KiteAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response = HTMLResponse(
        """
        <!doctype html>
        <html lang="en">
          <head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Kite connected</title></head>
          <body style="font-family:system-ui;background:#08111f;color:#e7eef8;display:grid;place-items:center;min-height:100vh;margin:0">
            <main style="max-width:34rem;padding:2rem;border:1px solid #2d3b50;border-radius:16px;background:#101b2b">
              <h1 style="margin-top:0;color:#35efbd">Kite connected</h1>
              <p>Authentication completed successfully. You can close this window and return to Confluence Terminal.</p>
            </main>
          </body>
        </html>
        """
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/auth/kite/status")
async def kite_status():
    response = JSONResponse(kite_auth_service.status())
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/macro")
async def get_macro_quotes():
    from ..services.technical_analysis_service import technical_service

    usd_inr, crude = await asyncio.gather(
        india_service.currency.get_usd_inr_quote(),
        technical_service.get_crude_ltp(),
        return_exceptions=True
    )

    if isinstance(usd_inr, Exception):
        usd_inr = {"label": "USD/INR", "value": None, "source": "Unavailable"}
    if isinstance(crude, Exception):
        crude = {"label": "WTI Crude", "symbol": "CL=F", "value": None, "currency": "USD", "source": "Unavailable"}

    return {"usd_inr": usd_inr, "crude": crude}


@app.get("/api/market-status")
async def get_market_status():
    return {
        "is_open": market_hours_service.is_market_open(),
        "next_open": market_hours_service.get_next_open_time().isoformat() if market_hours_service.get_next_open_time() else None,
        "time_until_open": str(market_hours_service.get_time_until_open()) if market_hours_service.get_time_until_open() else None
    }


@app.get("/api/technical")
async def get_technical_data():
    from ..services.technical_analysis_service import technical_service
    data = technical_service.get_cached()
    return {
        "stocks": {k: v.__dict__ for k, v in data.items()},
        "summary": technical_service.compute_market_summary()
    }


@app.get("/api/stocks/{symbol}")
async def get_stock_quote(symbol: str):
    quote = await nse_service.get_quote(symbol.upper())
    if quote:
        return quote
    raise HTTPException(status_code=404, detail="Stock not found")


@app.get("/api/stocks")
async def get_multiple_stocks(symbols: str):
    symbol_list = symbols.split(',')
    quotes = await nse_service.get_multiple_quotes(symbol_list)
    return quotes


@app.get("/api/india")
async def get_india_data():
    return await india_service.get_all_data()


@app.post("/api/portfolio/upload")
async def upload_portfolio(file: UploadFile = File(...)):
    global portfolio_data

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode()))

    portfolio_data = []
    for row in reader:
        symbol = row.get('symbol', '').strip().upper()
        if symbol:
            portfolio_data.append({
                'symbol': symbol,
                'quantity': float(row.get('quantity', 0)),
                'avg_price': float(row.get('avg_price', 0)),
                'sector': row.get('sector', 'Unknown')
            })

    for holding in portfolio_data:
        quote = await nse_service.get_quote(holding['symbol'])
        if quote:
            holding['current_price'] = quote.get('current_price', 0)
            holding['current_value'] = holding['quantity'] * holding['current_price']
            holding['pnl'] = holding['current_value'] - (holding['quantity'] * holding['avg_price'])
            holding['pnl_percent'] = (holding['pnl'] / (holding['quantity'] * holding['avg_price'])) * 100 if holding['avg_price'] > 0 else 0

    return {"status": "success", "holdings": portfolio_data}


@app.get("/api/portfolio")
async def get_portfolio():
    global portfolio_data
    return portfolio_data


@app.post("/api/watchlist/add")
async def add_to_watchlist(symbol: str):
    global watchlist
    symbol = symbol.upper()
    if symbol not in watchlist:
        watchlist.append(symbol)
    return {"watchlist": watchlist}


@app.delete("/api/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str):
    global watchlist
    symbol = symbol.upper()
    if symbol in watchlist:
        watchlist.remove(symbol)
    return {"watchlist": watchlist}


@app.get("/api/watchlist")
async def get_watchlist():
    global watchlist
    if watchlist:
        quotes = await nse_service.get_multiple_quotes(watchlist)
        return quotes
    return {}


@app.get("/api/scheduler/jobs")
async def get_scheduler_jobs():
    return market_hours_scheduler.get_jobs()


@app.post("/api/alerts/test")
async def test_alert():
    from ..models.models import Alert
    test_alert = Alert(
        id="test123",
        timestamp=__import__('datetime').datetime.now(),
        title="Test Alert",
        message="This is a test alert from the geo-political monitor",
        severity="info",
        related_sectors=["IT"],
        related_stocks=["TCS", "INFY"]
    )
    await alert_manager.process_alert(test_alert)
    return {"status": "success", "message": "Test alert sent"}


@app.get("/api/charts/sentiment")
async def get_sentiment_chart():
    global dashboard_data
    if not dashboard_data:
        return []

    sentiment_counts = {
        'strong_bullish': 0,
        'bullish': 0,
        'neutral': 0,
        'bearish': 0,
        'strong_bearish': 0
    }

    for news in dashboard_data.latest_news:
        label = news.sentiment_label.value
        if label in sentiment_counts:
            sentiment_counts[label] += 1

    return [
        {'sentiment': k, 'count': v}
        for k, v in sentiment_counts.items()
    ]


@app.get("/api/charts/sector-heatmap")
async def get_sector_heatmap():
    global dashboard_data
    if not dashboard_data:
        return []

    return [
        {
            'sector': s.name,
            'sentiment': s.overall_sentiment.value,
            'confidence': s.confidence,
            'news_count': s.news_count
        }
        for s in dashboard_data.sector_analysis
    ]


@app.get("/dashboard/manifest.json")
async def get_manifest():
    manifest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "dashboard", "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            return JSONResponse(json.load(f))
    return JSONResponse({"error": "Manifest not found"}, status_code=404)


@app.get("/dashboard/sw.js")
async def get_service_worker():
    sw_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "dashboard", "sw.js")
    if os.path.exists(sw_path):
        with open(sw_path, "r") as f:
            return StreamingResponse(
                f.read(),
                media_type="application/javascript",
                headers={"Cache-Control": "no-cache"}
            )
    return HTMLResponse("Service Worker not found", status_code=404)


@app.get("/dashboard/app.js")
async def get_app_js():
    app_js_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "dashboard", "app.js")
    if os.path.exists(app_js_path):
        with open(app_js_path, "r") as f:
            return StreamingResponse(
                f.read(),
                media_type="application/javascript",
                headers={"Cache-Control": "no-cache"}
            )
    return HTMLResponse("app.js not found", status_code=404)


@app.get("/dashboard/firebase-messaging.js")
async def get_firebase_messaging():
    fb_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "dashboard", "firebase-messaging.js")
    if os.path.exists(fb_path):
        with open(fb_path, "r") as f:
            return StreamingResponse(
                f.read(),
                media_type="application/javascript",
                headers={"Cache-Control": "no-cache"}
            )
    return HTMLResponse("firebase-messaging.js not found", status_code=404)


@app.get("/dashboard/index.html")
async def get_dashboard_pwa():
    html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "dashboard", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("Dashboard not found", status_code=404)


@app.get("/dashboard/icons/{icon_name}")
async def get_icon(icon_name: str):
    icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "dashboard", "icons", icon_name)
    if os.path.exists(icon_path):
        with open(icon_path, "rb") as f:
            return StreamingResponse(
                f.read(),
                media_type="image/svg+xml",
                headers={"Cache-Control": "max-age=86400"}
            )
    return HTMLResponse("Icon not found", status_code=404)


@app.post("/api/notifications/token")
async def save_fcm_token(request: dict):
    global fcm_tokens
    token = request.get("token")
    if token:
        fcm_tokens[token] = {
            "subscribed_at": str(asyncio.get_event_loop().time()),
            "alerts": {"sector": True, "news": True, "portfolio": True}
        }
        return {"status": "success", "message": "Token saved"}
    raise HTTPException(status_code=400, detail="No token provided")


@app.post("/api/notifications/subscribe")
async def subscribe_to_alerts(request: dict):
    global fcm_tokens
    token = request.get("token")
    alerts = request.get("alerts", {})

    if token:
        if token in fcm_tokens:
            fcm_tokens[token]["alerts"] = alerts
        else:
            fcm_tokens[token] = {
                "subscribed_at": str(asyncio.get_event_loop().time()),
                "alerts": alerts
            }
        return {"status": "success", "message": "Subscribed to alerts", "alerts": alerts}
    raise HTTPException(status_code=400, detail="No token provided")


@app.delete("/api/notifications/token/{token}")
async def unsubscribe_token(token: str):
    global fcm_tokens
    if token in fcm_tokens:
        del fcm_tokens[token]
        return {"status": "success", "message": "Unsubscribed"}
    raise HTTPException(status_code=404, detail="Token not found")


@app.post("/api/notifications/send")
async def send_notification(request: dict):
    global fcm_tokens
    title = request.get("title", "Stock Monitor")
    body = request.get("body", "")
    alert_type = request.get("type", "news")

    if not fcm_tokens:
        return {"status": "success", "message": "No subscribers"}

    sent_count = 0
    for token, data in fcm_tokens.items():
        alerts = data.get("alerts", {})
        if alerts.get(alert_type, False):
            sent_count += 1

    return {"status": "success", "sent": sent_count, "total": len(fcm_tokens)}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)


@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "dashboard", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r") as f:
            return f.read()
    return get_dashboard_html()


def get_dashboard_html() -> str:
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GeoPolitical Stock Monitor - Pro Terminal</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <style>
        :root {
            --bg-base: #020617;
            --bg-glass: rgba(15, 23, 42, 0.65);
            --bg-card: rgba(30, 41, 59, 0.5);
            --border-light: rgba(255, 255, 255, 0.08);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-primary: #3b82f6;
            --accent-glow: rgba(59, 130, 246, 0.5);
            --positive: #10b981;
            --positive-bg: rgba(16, 185, 129, 0.15);
            --negative: #ef4444;
            --negative-bg: rgba(239, 68, 68, 0.15);
            --warning: #f59e0b;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: radial-gradient(circle at top right, #0f172a, #020617 60%);
            background-attachment: fixed;
            min-height: 100vh;
            color: var(--text-main);
            -webkit-font-smoothing: antialiased;
        }

        /* Layout Grid */
        .container { max-width: 1920px; margin: 0 auto; padding: 1.5rem; display: flex; flex-direction: column; gap: 1.5rem; }
        .main-grid { display: grid; grid-template-columns: 280px 1fr 320px; gap: 1.5rem; height: calc(100vh - 180px); }

        /* Header / Navbar */
        .header {
            background: var(--bg-glass);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--border-light);
            position: sticky; top: 0; z-index: 100;
            padding: 1rem 1.5rem;
            display: flex; flex-direction: column; gap: 1rem;
        }
        .header-top { display: flex; justify-content: space-between; align-items: center; gap: 1rem; }

        .logo { display: flex; align-items: center; gap: 0.8rem; font-size: 1.25rem; font-weight: 700; letter-spacing: -0.02em; }
        .logo-icon {
            width: 32px; height: 32px;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1rem;
            box-shadow: 0 0 15px var(--accent-glow);
        }

        .status-badge { display: flex; align-items: center; gap: 0.5rem; padding: 0.35rem 0.8rem; border-radius: 99px; font-size: 0.75rem; font-weight: 600; font-family: 'JetBrains Mono', monospace; text-transform: uppercase;}
        .market-open { background: var(--positive-bg); color: var(--positive); border: 1px solid rgba(16, 185, 129, 0.3); }
        .market-closed { background: var(--negative-bg); color: var(--negative); border: 1px solid rgba(239, 68, 68, 0.3); }
        .status-dot { width: 6px; height: 6px; border-radius: 50%; animation: pulse 2s infinite; }
        .market-open .status-dot { background: var(--positive); box-shadow: 0 0 8px var(--positive); }
        .market-closed .status-dot { background: var(--negative); }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; transform: scale(0.8); } }

        .header-tools { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; justify-content: flex-end; }
        .macro-tape { display: flex; align-items: center; gap: 0.5rem; }
        .macro-chip {
            display: grid; grid-template-columns: auto auto; column-gap: 0.55rem; row-gap: 0.1rem;
            min-width: 118px; padding: 0.45rem 0.65rem;
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 8px;
            background: rgba(2, 6, 23, 0.32);
        }
        .macro-label { color: var(--text-muted); font-size: 0.62rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; grid-column: 1 / -1; }
        .macro-value { font-family: 'JetBrains Mono', monospace; font-size: 0.86rem; font-weight: 700; color: var(--text-main); white-space: nowrap; }
        .macro-delta { font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; font-weight: 700; align-self: end; white-space: nowrap; }
        .macro-source { color: #64748b; font-size: 0.58rem; font-weight: 600; grid-column: 1 / -1; text-transform: uppercase; letter-spacing: 0.06em; }

        /* Nifty Banner */
        .nifty-banner {
            background: linear-gradient(90deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.2));
            border: 1px solid var(--border-light);
            border-radius: 10px; padding: 0.75rem 1.5rem;
            display: flex; justify-content: space-between; align-items: center;
        }
        .nifty-left { display: flex; gap: 1.25rem; align-items: center; }
        .nifty-label { color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; font-size: 0.8rem;}
        .nifty-ltp { font-size: 1.25rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
        .nifty-signal { padding: 0.25rem 0.6rem; border-radius: 6px; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;}
        .signal-bullish { background: var(--positive-bg); color: var(--positive); box-shadow: 0 0 10px rgba(16, 185, 129, 0.2); }
        .signal-bearish { background: var(--negative-bg); color: var(--negative); box-shadow: 0 0 10px rgba(239, 68, 68, 0.2); }
        .nifty-right { display: flex; gap: 2rem; }
        .nifty-metric { display: flex; flex-direction: column; align-items: flex-end; }
        .nifty-metric-label { font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.2rem;}
        .nifty-metric-val { font-weight: 600; font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; }

        /* KPI Grid */
        .stats-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 1rem; }
        .stat-card {
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: 12px; padding: 1.25rem;
            backdrop-filter: blur(8px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        .stat-card::before {
            content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
            transform: translateX(-100%); transition: transform 0.5s ease;
        }
        .stat-card:hover { transform: translateY(-4px); border-color: rgba(255,255,255,0.2); box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        .stat-card:hover::before { transform: translateX(100%); }
        .stat-label { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.75rem; font-weight: 600;}
        .stat-value { font-size: 1.75rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;}

        /* Cards */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: 16px;
            overflow: hidden; display: flex; flex-direction: column;
            backdrop-filter: blur(12px);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        .card-header {
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid var(--border-light);
            background: rgba(15, 23, 42, 0.4);
            display: flex; justify-content: space-between; align-items: center;
        }
        .card-title { font-weight: 600; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; display: flex; align-items: center; gap: 0.75rem; color: #fff;}
        .card-body { padding: 1rem; overflow-y: auto; flex: 1; position: relative;}

        /* News Sidebar */
        .news-list { display: flex; flex-direction: column; gap: 0.75rem; }
        .news-item {
            padding: 1rem; border-radius: 10px;
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid rgba(255,255,255,0.03);
            transition: all 0.2s;
            cursor: pointer;
            animation: fadeIn 0.5s ease-out;
        }
        .news-item:hover { background: rgba(30, 41, 59, 0.8); border-color: rgba(255,255,255,0.1); transform: translateX(2px); }
        .news-source { font-size: 0.7rem; color: var(--text-muted); margin-bottom: 0.5rem; display: flex; justify-content: space-between; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;}
        .news-title { font-size: 0.9rem; font-weight: 500; line-height: 1.5; margin-bottom: 0.75rem; color: #fff; }
        .news-link { color: inherit; text-decoration: none; display: block; }
        .news-meta { display: flex; gap: 0.5rem; flex-wrap: wrap; }

        .event-list { display: flex; flex-direction: column; gap: 0.75rem; }
        .event-item {
            padding: 0.9rem;
            border-radius: 8px;
            background: rgba(15, 23, 42, 0.42);
            border: 1px solid rgba(255,255,255,0.06);
            border-left: 4px solid var(--accent-primary);
        }
        .event-item.high { border-left-color: var(--negative); }
        .event-top { display: flex; justify-content: space-between; gap: 0.75rem; align-items: center; color: var(--text-muted); font: 700 0.68rem/1 'JetBrains Mono', monospace; letter-spacing: 0.05em; text-transform: uppercase; }
        .event-title { margin-top: 0.55rem; color: #fff; font-weight: 700; font-size: 0.85rem; line-height: 1.35; }
        .event-note { margin-top: 0.45rem; color: rgba(255,255,255,0.68); font-size: 0.75rem; line-height: 1.45; }
        .cmp-stack { display: grid; gap: 0.22rem; justify-items: end; }
        .cmp-price { color: #fff; font-family: 'JetBrains Mono', monospace; }
        .cmp-change { font: 800 0.68rem/1 'JetBrains Mono', monospace; letter-spacing: 0.04em; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        /* Badges */
        .badge { font-size: 0.65rem; padding: 0.25rem 0.6rem; border-radius: 6px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; font-family: 'JetBrains Mono', monospace;}
        .badge-sentiment-strong_bullish { background: var(--positive-bg); color: var(--positive); border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge-sentiment-bullish { background: rgba(52, 211, 153, 0.1); color: #34d399; }
        .badge-sentiment-neutral { background: rgba(148, 163, 184, 0.1); color: var(--text-muted); }
        .badge-sentiment-bearish { background: rgba(248, 113, 113, 0.1); color: #f87171; }
        .badge-sentiment-strong_bearish { background: var(--negative-bg); color: var(--negative); border: 1px solid rgba(239, 68, 68, 0.3); }

        /* Confluence Table */
        .table-container { width: 100%; height: 100%; overflow-y: auto; overflow-x: hidden; padding-right: 0.5rem;}
        .confluence-table { width: 100%; border-collapse: separate; border-spacing: 0 4px; font-size: 0.85rem; }
        .confluence-table th {
            position: sticky; top: 0;
            background: rgba(2, 6, 23, 0.95); backdrop-filter: blur(12px);
            padding: 1rem 0.75rem; text-align: left;
            color: var(--text-muted); font-weight: 600; font-size: 0.75rem;
            text-transform: uppercase; letter-spacing: 0.05em;
            z-index: 10; cursor: pointer; user-select: none; transition: color 0.2s;
            border-bottom: 1px solid var(--border-light);
        }
        .confluence-table th:hover { color: #fff; }
        .confluence-table tbody tr {
            transition: all 0.2s;
            background: rgba(15, 23, 42, 0.3);
        }
        .confluence-table td {
            padding: 0.8rem 0.75rem;
            border-top: 1px solid transparent; border-bottom: 1px solid transparent;
            font-family: 'JetBrains Mono', monospace;
            vertical-align: middle;
        }
        .confluence-table tbody tr:hover {
            background: rgba(30, 41, 59, 0.6)!important;
            transform: scale(1.01);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            position: relative; z-index: 5;
            border-radius: 8px;
        }
        .confluence-table tbody tr:hover td:first-child { border-top-left-radius: 8px; border-bottom-left-radius: 8px; }
        .confluence-table tbody tr:hover td:last-child { border-top-right-radius: 8px; border-bottom-right-radius: 8px; }

        .col-script { font-family: 'Inter', sans-serif !important; font-weight: 700; color: #fff; font-size: 0.95rem; display: flex; align-items: center; gap: 0.5rem;}

        /* Alignment Classes */
        th.col-left, td.col-left { text-align: left !important; justify-content: flex-start !important; }
        th.col-center, td.col-center { text-align: center !important; justify-content: center !important; }
        th.col-right, td.col-right { text-align: right !important; justify-content: flex-end !important; }

        /* Confluence Bar */
        .conf-cell { display: flex; align-items: center; gap: 0.75rem; justify-content: flex-end;}
        .conf-score { width: 45px; text-align: right; font-weight: 600; }
        .conf-bar-wrapper {
            width: 70px; height: 6px;
            background: rgba(0,0,0,0.5);
            border-radius: 3px; overflow: hidden; position: relative;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.3);
        }
        .conf-bar-fill { position: absolute; top: 0; bottom: 0; border-radius: 3px; transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
        .conf-pos { background: linear-gradient(90deg, #10b981, #34d399); left: 50%; box-shadow: 0 0 8px rgba(16,185,129,0.5); }
        .conf-neg { background: linear-gradient(270deg, #ef4444, #f87171); right: 50%; box-shadow: 0 0 8px rgba(239,68,68,0.5); }

        /* Alerts */
        .alert-item {
            padding: 1rem; border-radius: 10px; margin-bottom: 0.75rem;
            font-size: 0.85rem; position: relative; overflow: hidden;
            animation: fadeIn 0.5s ease-out;
        }
        .alert-high { background: linear-gradient(90deg, rgba(239, 68, 68, 0.15), rgba(239,68,68,0.05)); border-left: 4px solid var(--negative); }
        .alert-medium { background: linear-gradient(90deg, rgba(245, 158, 11, 0.15), rgba(245,158,11,0.05)); border-left: 4px solid var(--warning); }
        .alert-title { font-weight: 600; color: #fff; margin-bottom: 0.4rem; font-family: 'Inter', sans-serif; display: flex; align-items: center; gap: 0.5rem;}
        .alert-time { font-size: 0.7rem; color: var(--text-muted); margin-top: 0.6rem; font-family: 'JetBrains Mono', monospace;}

        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: rgba(0,0,0,0.2); border-radius: 4px;}
        ::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.3); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(148, 163, 184, 0.5); }

        /* Utility */
        .val-pos { color: var(--positive); }
        .val-neg { color: var(--negative); }
        .text-glow-pos { text-shadow: 0 0 10px rgba(16,185,129,0.4); }
        .text-glow-neg { text-shadow: 0 0 10px rgba(239,68,68,0.4); }

        .skeleton { background: linear-gradient(90deg, #1e293b 25%, #334155 50%, #1e293b 75%); background-size: 400% 100%; animation: skeletonLoading 1.5s infinite; border-radius: 4px;}
        @keyframes skeletonLoading { 0% { background-position: 100% 50%; } 100% { background-position: 0 50%; } }

        /* Mobile Responsiveness */
        .sidebar-col { display: flex; flex-direction: column; gap: 1.5rem; width: 380px; flex-shrink: 0; overflow-y: hidden; }

        @media (max-width: 1200px) {
            .main-grid { grid-template-columns: 1fr; height: auto; }
            .sidebar-col { width: 100%; overflow-y: visible; gap: 1rem; }
            .card { min-height: 400px; }
            .card-body { overflow-y: visible !important; }
            .nifty-banner { flex-direction: column; gap: 1rem; text-align: center; }
            .nifty-left, .nifty-right { justify-content: center; width: 100%; }
            .nifty-center { min-height: auto; margin: 1rem 0; }
        }

        @media (max-width: 768px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); padding: 0.2rem; }
            .container { padding: 0.5rem; gap: 0.75rem; }
            .header-top { flex-direction: row; flex-wrap: wrap; gap: 0.5rem; align-items: center; justify-content: space-between; }
            .header-tools { width: 100%; gap: 0.5rem; justify-content: space-between; }
            .macro-tape { order: -1; width: 100%; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.5rem; }
            .macro-chip { min-width: 0; width: 100%; }

            /* Banner re-layout for mobile to save vertical space */
            .nifty-banner { flex-direction: row; flex-wrap: wrap; gap: 0.5rem; padding: 0.75rem; align-items: center; justify-content: space-between; }
            .nifty-left { flex: 1 1 100%; display: flex; flex-direction: row; justify-content: space-between; align-items: center; gap: 0.5rem; }
            .nifty-center { display: none; } /* Hide the macro bias pie chart on mobile to save massive space */
            .nifty-right { flex: 1 1 100%; display: flex; flex-direction: row; justify-content: space-between; gap: 0.5rem; padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.1); }
            .nifty-metric { align-items: flex-start; }
            .nifty-metric-label { font-size: 0.55rem; line-height: 1; margin-bottom: 0; }
            .nifty-metric-val { font-size: 0.85rem; line-height: 1; }

            .card { min-height: 350px; }
            .conf-cell { justify-content: center; flex-direction: column; gap: 0.25rem; }
        }

        @media (max-width: 480px) {
            .stats-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="header-top">
            <div class="logo">
                <div class="logo-icon">⚡</div>
                <span style="background: linear-gradient(to right, #fff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Confluence Terminal</span>
            </div>
            <div class="header-tools">
                <div class="macro-tape" aria-label="Macro market quotes">
                    <div class="macro-chip">
                        <span class="macro-label">USD/INR</span>
                        <span class="macro-value" id="usdInrValue">--</span>
                        <span class="macro-delta" id="usdInrDelta">--</span>
                        <span class="macro-source" id="usdInrSource">loading</span>
                    </div>
                    <div class="macro-chip">
                        <span class="macro-label">Crude LTP</span>
                        <span class="macro-value" id="crudeValue">--</span>
                        <span class="macro-delta" id="crudeDelta">--</span>
                        <span class="macro-source" id="crudeSource">loading</span>
                    </div>
                </div>
                <div style="background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.28); padding: 0.5rem 0.75rem; color: #86efac; border-radius: 6px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; display: flex; align-items: center; gap: 0.45rem;">
                    <span style="width: 7px; height: 7px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 10px rgba(34,197,94,0.75);"></span>
                    Yahoo Finance
                </div>
                <div style="display: flex; flex-direction: column; align-items: flex-end;">
                    <span style="font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Last Sync</span>
                    <span style="font-size: 0.85rem; font-family: 'JetBrains Mono', monospace; font-weight: 500;" id="lastUpdated">--:--:--</span>
                </div>
                <div class="status-badge market-closed" id="marketStatus">
                    <span class="status-dot"></span>
                    <span id="marketText">Checking...</span>
                </div>
            </div>
        </div>
        <!-- Nifty Banner -->
        <div class="nifty-banner" id="niftyBanner">
            <div class="nifty-left" style="flex: 1;">
                <span class="nifty-label">NIFTY 50 Core Indicator</span>
                <span class="nifty-ltp" id="niftyLtp">--</span>
                <span class="nifty-signal" id="niftySignal">--</span>
            </div>

            <div class="nifty-center" style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 120px;">
                <span style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; margin-bottom: -10px; z-index: 10;">Macro Bias</span>
                <div id="sentimentChart" style="width: 140px; height: 140px; margin-top: -15px;">
                    <div class="skeleton" style="width: 80px; height: 80px; border-radius: 50%; margin: 0 auto; margin-top: 30px;"></div>
                </div>
            </div>

            <div class="nifty-right" style="flex: 1; justify-content: flex-end;">
                <div class="nifty-metric">
                    <span class="nifty-metric-label">Momentum Velocity</span>
                    <span class="nifty-metric-val" id="niftyVel">--</span>
                </div>
                <div class="nifty-metric">
                    <span class="nifty-metric-label">Awesome Osc (AC)</span>
                    <span class="nifty-metric-val" id="niftyAc">--</span>
                </div>
                <div class="nifty-metric">
                    <span class="nifty-metric-label">Parabolic SAR AF</span>
                    <span class="nifty-metric-val" id="niftyAf" style="color: #60a5fa;">--</span>
                </div>
            </div>
        </div>
    </header>

    <div class="container">
        <!-- KPIs -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Articles Analyzed</div>
                <div class="stat-value" id="kpiNews">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Active Alpha Alerts</div>
                <div class="stat-value" style="color: var(--warning); text-shadow: 0 0 15px rgba(245,158,11,0.3);" id="kpiAlerts">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Bullish PSAR Breadth</div>
                <div class="stat-value val-pos text-glow-pos" id="kpiBullish">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Bearish PSAR Breadth</div>
                <div class="stat-value val-neg text-glow-neg" id="kpiBearish">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Global Avg AC</div>
                <div class="stat-value" id="kpiAf" style="color: #60a5fa;">0.00</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(139,92,246,0.1)); border-color: rgba(59,130,246,0.3);">
                <div class="stat-label" style="color: #93c5fd;">Engine Status</div>
                <div class="stat-value" style="color: #60a5fa; font-size: 1.4rem; display: flex; align-items:center; gap: 0.5rem;">
                    <span style="display:inline-block; width:10px; height:10px; background:#60a5fa; border-radius:50%; box-shadow: 0 0 10px #60a5fa; animation: pulse 2s infinite;"></span>
                    ONLINE
                </div>
            </div>
        </div>

        <div class="main-grid">
            <!-- Left: GeoPolitical News & Sector Sentiments -->
            <div class="sidebar-col">
                <!-- Live Intelligence -->
                <div class="card" style="flex: 1.2; display: flex; flex-direction: column; min-height: 0;">
                    <div class="card-header">
                        <div class="card-title">
                            <span style="font-size: 1.2rem;">📡</span>
                            Live Intelligence
                        </div>
                    </div>
                    <div class="card-body news-list scroll-container" id="newsContainer" style="overflow-y: auto;">
                        <div style="text-align:center; padding: 2rem; color: var(--text-muted);">Syncing feeds...</div>
                    </div>
                </div>

                <!-- Micro Sentiment (Sector Analysis) -->
                <div class="card" style="flex: 1; display: flex; flex-direction: column; min-height: 0;">
                    <div class="card-header">
                        <div class="card-title">
                            <span style="font-size: 1.2rem;">🔬</span>
                            Sector Sentiments
                        </div>
                    </div>
                    <div class="card-body scroll-container" id="sectorContainer" style="padding: 1rem; overflow-y: auto;">
                        <div style="text-align:center; padding: 2rem; color: var(--text-muted);">Fetching analysis data...</div>
                    </div>
                </div>
            </div>

            <!-- Center: Confluence Screener -->
            <div class="card" style="flex: 1; display: flex; flex-direction: column; min-height: 0;">
                <div class="card-header" style="background: linear-gradient(90deg, rgba(15,23,42,0.8), rgba(30,41,59,0.8));">
                    <div class="card-title">
                        <span style="font-size: 1.2rem;">🎯</span>
                        Algorithm Confluence Matrix
                    </div>
                </div>
                <div class="card-body" style="padding: 0;">
                    <div class="table-container">
                        <table class="confluence-table" id="confluenceTable">
                            <thead>
                                <tr>
                                    <th data-sort="symbol" class="col-left"><div style="text-align:left;">Ticker</div></th>
                                    <th data-sort="ltp" class="col-right"><div style="text-align:right;">CMP / % Chg</div></th>
                                    <th data-sort="high_52w" class="col-right"><div style="text-align:right;">52W High (₹)</div></th>
                                    <th data-sort="ac" class="col-right"><div style="text-align:right;">AC Osc</div></th>
                                    <th data-sort="velocity" class="col-right"><div style="text-align:right;">Velocity</div></th>
                                    <th data-sort="psar_af" class="col-right"><div style="text-align:right;">pSAR AF</div></th>
                                    <th data-sort="signal_strength" class="col-center"><div style="text-align:center;">Tech Signal</div></th>
                                    <th data-sort="prediction" class="col-center"><div style="text-align:center;">AI Sentiment</div></th>
                                    <th class="col-right" data-sort="confluence_score"><div style="text-align:right;">Confluence Score</div></th>
                                </tr>
                            </thead>
                            <tbody id="screenerBody">
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Right: Actionable Alerts -->
            <div class="sidebar-col">
                <div class="card" style="flex: 0 0 auto; max-height: 280px;">
                    <div class="card-header">
                        <div class="card-title">
                            <span style="font-size: 1.2rem;">📅</span>
                            Upcoming Events
                        </div>
                    </div>
                    <div class="card-body scroll-container event-list" id="eventsContainer" style="overflow-y: auto;">
                        <div style="text-align:center; padding: 1rem; color: var(--text-muted);">Loading event calendar...</div>
                    </div>
                </div>
                <!-- Alerts -->
                <div class="card" style="flex: 1; display: flex; flex-direction: column; min-height: 0;">
                    <div class="card-header">
                        <div class="card-title">
                            <span style="font-size: 1.2rem;">🚨</span>
                            Actionable Alerts
                        </div>
                    </div>
                    <div class="card-body scroll-container" id="alertsContainer" style="overflow-y: auto;">
                        <div style="text-align:center; padding: 2rem; color: var(--text-muted);">Awaiting signals...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Global State
        let currentData = null;
        let sortCol = 'confluence_score';
        let sortDesc = true;
        let chartInitialized = false;

        // formatters
        const fmtNum = (n, d=2) => (n !== null && n !== undefined) ? Number(n).toFixed(d) : '--';
        const colorClass = (n) => n > 0 ? 'val-pos' : (n < 0 ? 'val-neg' : '');
        const fmtDelta = (n, d=2) => (n === null || n === undefined) ? '--' : `${n >= 0 ? '+' : ''}${Number(n).toFixed(d)}`;

        function renderMacroQuote(prefix, quote, options = {}) {
            const valueEl = document.getElementById(`${prefix}Value`);
            const deltaEl = document.getElementById(`${prefix}Delta`);
            const sourceEl = document.getElementById(`${prefix}Source`);
            if (!valueEl || !deltaEl || !sourceEl) return;

            const value = quote?.value;
            const changePercent = quote?.change_percent;
            const currencyPrefix = quote?.currency === 'USD' ? '$' : (quote?.currency === 'INR' ? '₹' : (options.prefix || ''));
            valueEl.textContent = value === null || value === undefined ? '--' : `${currencyPrefix}${fmtNum(value, options.decimals ?? 2)}`;
            deltaEl.textContent = fmtDelta(changePercent, 2) + (changePercent === null || changePercent === undefined ? '' : '%');
            deltaEl.className = `macro-delta ${colorClass(changePercent || 0)}`;
            sourceEl.textContent = quote?.symbol || quote?.source || 'unavailable';
        }

        function updateMacro() {
            fetch('/api/macro')
                .then(r => r.json())
                .then(data => {
                    renderMacroQuote('usdInr', data.usd_inr, {decimals: 4});
                    renderMacroQuote('crude', data.crude, {decimals: 2});
                })
                .catch(err => {
                    console.error('Macro quote fetch error:', err);
                    renderMacroQuote('usdInr', null);
                    renderMacroQuote('crude', null);
                });
        }

        function updateDashboard() {
            fetch('/api/dashboard')
                .then(r => r.json())
                .then(data => {
                    currentData = data;
                    renderNifty(data.nifty);
                    renderKPIs(data);
                    renderNews(data.latest_news);
                    renderScreener(data.top_predictions);
                    renderSectors(data.sector_analysis);
                    renderEvents(data.upcoming_events);
                    renderAlerts(data.alerts);
                    renderChart(data);
                    document.getElementById('lastUpdated').textContent = data.technical_updated || new Date().toLocaleTimeString();
                })
                .catch(err => console.error('Dashboard fetch error:', err));

            updateMacro();

            fetch('/api/market-status')
                .then(r => r.json())
                .then(data => {
                    const badge = document.getElementById('marketStatus');
                    const text = document.getElementById('marketText');
                    if (data.is_open) {
                        badge.className = 'status-badge market-open';
                        text.textContent = 'Market Open';
                    } else {
                        badge.className = 'status-badge market-closed';
                        text.textContent = `Market Closed`;
                    }
                });
        }

        function renderNifty(nifty) {
            if(!nifty) return;
            document.getElementById('niftyLtp').textContent = `₹${fmtNum(nifty.ltp)}`;

            const sigEl = document.getElementById('niftySignal');
            sigEl.textContent = nifty.trend;
            sigEl.className = `nifty-signal signal-${nifty.trend.toLowerCase()}`;

            const velEl = document.getElementById('niftyVel');
            velEl.textContent = (nifty.velocity >= 0 ? '+' : '') + fmtNum(nifty.velocity, 4);
            velEl.className = `nifty-metric-val ${colorClass(nifty.velocity)}`;

            const acEl = document.getElementById('niftyAc');
            acEl.textContent = (nifty.ac >= 0 ? '+' : '') + fmtNum(nifty.ac, 4);
            acEl.className = `nifty-metric-val ${colorClass(nifty.ac)}`;

            document.getElementById('niftyAf').textContent = fmtNum(nifty.psar_af);
        }

        function renderKPIs(data) {
            document.getElementById('kpiNews').textContent = data.latest_news?.length || 0;
            document.getElementById('kpiAlerts').textContent = data.alerts?.length || 0;
            if(data.market_summary) {
                document.getElementById('kpiBullish').textContent = data.market_summary.bullish || 0;
                document.getElementById('kpiBearish').textContent = data.market_summary.bearish || 0;
                document.getElementById('kpiAf').textContent = fmtNum(data.market_summary.avg_ac, 4);
            }
        }

        function renderNews(news) {
            const c = document.getElementById('newsContainer');
            if(!news || !news.length) { c.innerHTML = '<div style="padding:2rem; text-align:center; color:var(--text-muted);">No news events detected.</div>'; return; }

            const newHtml = news.map(n => `
                <div class="news-item">
                    <div class="news-source">
                        <span>${n.source}</span>
                        <span style="font-family:'JetBrains Mono', monospace;">${new Date(n.published_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                    </div>
                    <div class="news-title">
                        <a href="${n.url}" target="_blank" class="news-link">${n.title}</a>
                    </div>
                    <div class="news-meta">
                        <span class="badge badge-sentiment-${n.sentiment_label}">${n.sentiment_label.replace('strong_', 'Strong ')}</span>
                        ${n.affected_sectors[0] ? `<span class="badge" style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: var(--text-muted);">${n.affected_sectors[0]}</span>` : ''}
                        ${n.is_breaking ? `<span class="badge" style="background: var(--negative-bg); color: var(--negative); border: 1px solid rgba(239,68,68,0.3); box-shadow: 0 0 10px rgba(239,68,68,0.2);">BREAKING</span>` : ''}
                    </div>
                </div>
            `).join('');

            // Only update if changed to prevent animation flicker
            if(c.innerHTML !== newHtml) {
                c.innerHTML = newHtml;
            }
        }

        function renderScreener(preds) {
            const tbody = document.getElementById('screenerBody');
            if(!preds || !preds.length) { tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding: 2rem; color:var(--text-muted);">Fetching analysis data...</td></tr>'; return; }

            // Sort
            const sorted = [...preds].sort((a,b) => {
                let valA = a[sortCol];
                let valB = b[sortCol];

                if(sortCol === 'prediction') { valA = a.prediction; valB = b.prediction; }

                if(valA === null || valA === undefined) return 1;
                if(valB === null || valB === undefined) return -1;

                if(typeof valA === 'string') return sortDesc ? valB.localeCompare(valA) : valA.localeCompare(valB);
                return sortDesc ? valB - valA : valA - valB;
            });

            const sigEmoji = { 'STRONG_BUY': '🔥', 'BUY': '✨', 'NEUTRAL': '➖', 'SELL': '⚠️', 'STRONG_SELL': '⛔' };

            const newHtml = sorted.map((p, idx) => {
                const ac = p.ac || 0;
                const vel = p.velocity || 0;
                const changePercent = Number(p.change_percent || 0);
                const confScore = p.confluence_score || 0;

                const barWidth = Math.min(Math.abs(confScore) * 100, 100);
                const barHtml = confScore >= 0
                    ? `<div class="conf-bar-fill conf-pos" style="width: ${barWidth/2}%;"></div>`
                    : `<div class="conf-bar-fill conf-neg" style="width: ${barWidth/2}%;"></div>`;

                const techSigClass = typeof p.signal_strength === 'string' && p.signal_strength.includes('BUY') ? 'val-pos' : (typeof p.signal_strength === 'string' && p.signal_strength.includes('SELL') ? 'val-neg' : 'text-muted');

                return `
                <tr style="animation: fadeIn 0.3s ease-out ${idx * 0.02}s both;">
                    <td class="col-script col-left">
                        <span style="opacity:0.5; font-size:0.7rem; font-family:'JetBrains Mono', monospace; width:15px; display:inline-block; text-align:right; margin-right:8px;">${idx+1}</span>
                        ${p.symbol}
                    </td>
                    <td class="col-right">
                        <span class="cmp-stack">
                            <span class="cmp-price">₹${fmtNum(p.ltp)}</span>
                            <span class="cmp-change ${colorClass(changePercent)}">${changePercent >= 0 ? '+':''}${fmtNum(changePercent, 2)}%</span>
                        </span>
                    </td>
                    <td class="col-right" style="color: var(--text-muted);">${fmtNum(p.high_52w)}</td>
                    <td class="${colorClass(ac)} col-right">${ac >= 0 ? '+':''}${fmtNum(ac, 4)}</td>
                    <td class="${colorClass(vel)} col-right">${vel >= 0 ? '+':''}${fmtNum(vel, 4)}</td>
                    <td style="color: #cbd5e1;" class="col-right">${fmtNum(p.psar_af, 2)}</td>
                    <td style="font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.05em;" class="${techSigClass} col-center">
                        ${sigEmoji[p.signal_strength] || '➖'} ${p.signal_strength?.replace('_', ' ') || '-'}
                    </td>
                    <td class="col-center">
                        <span class="badge badge-sentiment-${p.prediction}">${p.prediction.replace('strong_', 'Strong ')}</span>
                    </td>
                    <td class="col-right">
                        <div class="conf-cell" title="Confluence Score: ${confScore}">
                            <span class="conf-score ${colorClass(confScore)}">${confScore >= 0 ? '+':''}${fmtNum(confScore, 2)}</span>
                            <div class="conf-bar-wrapper">${barHtml}</div>
                        </div>
                    </td>
                </tr>
            `}).join('');

            // To avoid losing scroll position completely wiping table, check if html changed
            // Usually we'd want a virtual DOM, but for this simple dash, diffing HTML string prevents most stutter
            if(tbody.innerHTML !== newHtml) {
                tbody.innerHTML = newHtml;
            }
        }

        function renderSectors(sectors) {
            const c = document.getElementById('sectorContainer');
            if(!sectors || !sectors.length) { c.innerHTML = '<div style="color:var(--text-muted); text-align:center;">No sector data</div>'; return; }

            const newHtml = sectors.map(s => `
                <div style="background: rgba(15,23,42,0.4); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem; box-shadow: inset 0 2px 10px rgba(0,0,0,0.2);">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.5rem;">
                        <span style="font-weight: 600; font-size: 0.95rem; color: #f8fafc;">${s.name}</span>
                        <span class="badge badge-sentiment-${s.overall_sentiment}">${s.overall_sentiment.replace('strong_', 'Strong ')}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size: 0.8rem; color: #94a3b8;">
                        <div>Algorithmic Signal: <strong class="${s.tech_signal.includes('BUY') ? 'val-pos' : (s.tech_signal.includes('SELL') ? 'val-neg' : '')}">${s.tech_signal.replace('_', ' ')}</strong></div>
                        <div>News: ${s.news_count}</div>
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--text-muted);">
                        Avg AC: <span class="${colorClass(s.avg_ac)}">${fmtNum(s.avg_ac, 3)}</span> | Confidence: ${(s.confidence * 100).toFixed(0)}%
                    </div>
                    ${s.top_url ? `<div style="margin-top: 0.25rem;"><a href="${s.top_url}" target="_blank" style="color:var(--accent-primary); font-size:0.75rem; text-decoration:none;">View Top Story →</a></div>` : ''}
                </div>
            `).join('');

            if(c.innerHTML !== newHtml) {
                c.innerHTML = newHtml;
            }
        }

        function renderEvents(events) {
            const c = document.getElementById('eventsContainer');
            if(!c) return;
            if(!events || !events.length) {
                c.innerHTML = '<div style="padding:1rem; text-align:center; color:var(--text-muted); font-size:0.85rem;">No upcoming major market events.</div>';
                return;
            }

            const newHtml = events.slice(0, 6).map(e => {
                const days = Number(e.days_until);
                const countdown = days === 0 ? 'TODAY' : (days === 1 ? 'T-1 ALERT' : `T-${days}`);
                const dateText = e.date ? new Date(`${e.date}T00:00:00+05:30`).toLocaleDateString('en-IN', {day: '2-digit', month: 'short'}) : '--';
                const impactClass = e.impact === 'high' ? 'high' : 'medium';
                return `
                    <div class="event-item ${impactClass}">
                        <div class="event-top"><span>${e.category || 'Market'}</span><span>${dateText} / ${countdown}</span></div>
                        <div class="event-title">${e.title || 'Market event'}</div>
                        <div class="event-note">${e.note || ''}</div>
                    </div>
                `;
            }).join('');

            if(c.innerHTML !== newHtml) {
                c.innerHTML = newHtml;
            }
        }

        function renderAlerts(alerts) {
            const c = document.getElementById('alertsContainer');
            if(!alerts || !alerts.length) { c.innerHTML = '<div style="padding:2rem; text-align:center; color:var(--text-muted); font-size:0.9rem;">No actionable alerts. System monitoring...</div>'; return; }

            const newHtml = alerts.map(a => {
                const clickStyle = a.url ? 'cursor: pointer; transition: transform 0.2s;' : '';
                const clickAttr = a.url ? `onclick="window.open('${a.url}', '_blank')"` : '';
                const titleStyle = a.url ? 'text-decoration: underline; text-underline-offset: 4px; text-decoration-color: rgba(255,255,255,0.3);' : '';
                return `
                <div class="alert-item alert-${a.severity}" style="${clickStyle}" ${clickAttr} onmouseover="this.style.transform='translateX(4px)'" onmouseout="this.style.transform='translateX(0)'">
                    <div class="alert-title" style="${titleStyle}">
                        ${a.severity === 'high' ? '⚠️' : '⚡'} ${a.title}
                        ${a.url ? '<span style="font-size: 0.7rem; opacity: 0.5; margin-left: auto;">↗</span>' : ''}
                    </div>
                    <div style="color: rgba(255,255,255,0.7); line-height: 1.5; font-size: 0.8rem;">${a.message}</div>
                    <div class="alert-time">${new Date(a.timestamp).toLocaleTimeString()}</div>
                </div>
                `;
            }).join('');

            if(c.innerHTML !== newHtml) {
                c.innerHTML = newHtml;
            }
        }

        function renderChart(data) {
            if(!data.sector_analysis) return;

            const counts = {'Bullish':0, 'Bearish':0, 'Neutral':0};
            data.top_predictions.forEach(p => {
                const sentiment = (p.prediction || '').toLowerCase();
                if(sentiment.includes('bullish')) counts['Bullish']++;
                else if(sentiment.includes('bearish')) counts['Bearish']++;
                else counts['Neutral']++;
            });

            const total = counts['Bullish'] + counts['Bearish'] + counts['Neutral'];
            if(total === 0) return;

            const plotData = [{
                values: [counts['Bullish'], counts['Neutral'], counts['Bearish']],
                labels: ['Bullish', 'Neutral', 'Bearish'],
                type: 'pie',
                hole: 0.65,
                rotation: 90,
                direction: 'clockwise',
                domain: {x: [0, 1], y: [0, 1]},
                marker: {
                    colors: ['#10b981', '#475569', '#ef4444'],
                    line: {color: 'rgba(0,0,0,0)', width: 0}
                },
                textinfo: 'percent',
                textfont: { color: '#ffffff', size: 10, family: 'Inter', weight: 'bold' },
                hoverinfo: 'label+value',
                hovertemplate: '<b>%{label}</b><br>%{value} signals<extra></extra>'
            }];

            const layout = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                margin: {t:0, b:0, l:0, r:0},
                showlegend: false,
                font: { color: '#f8fafc', family: 'Inter' },
                transition: {duration: 500, easing: 'cubic-in-out'}
            };

            const chartDiv = document.getElementById('sentimentChart');

            if (!chartInitialized) {
                chartDiv.innerHTML = ''; // Clear skeleton
                Plotly.newPlot(chartDiv, plotData, layout, {displayModeBar: false, responsive: true});
                chartInitialized = true;
            } else {
                Plotly.react(chartDiv, plotData, layout, {displayModeBar: false, responsive: true});
            }
        }

        // Sorting Logic
        document.querySelectorAll('.confluence-table th').forEach(th => {
            th.addEventListener('click', () => {
                const col = th.dataset.sort;
                if(!col) return;

                // Add active state styling to headers
                document.querySelectorAll('.confluence-table th').forEach(h => h.style.color = 'var(--text-muted)');
                th.style.color = '#fff';

                if(sortCol === col) {
                    sortDesc = !sortDesc;
                } else {
                    sortCol = col;
                    sortDesc = true;
                }

                // Add visual indicator of sort direction
                document.querySelectorAll('.sort-arrow').forEach(a => a.remove());
                th.innerHTML += `<span class="sort-arrow" style="margin-left:5px; font-size:0.8rem; color:var(--accent-primary)">${sortDesc ? '↓' : '↑'}</span>`;

                if(currentData) renderScreener(currentData.top_predictions);
            });
        });

        // Initialize sort arrow on default column
        const defaultTh = document.querySelector('.confluence-table th[data-sort="confluence_score"]');
        if(defaultTh) {
            defaultTh.style.color = '#fff';
            defaultTh.innerHTML += `<span class="sort-arrow" style="margin-left:5px; font-size:0.8rem; color:var(--accent-primary)">↓</span>`;
        }

        // Init
        updateDashboard();
        updateMacro();

        // Refresh every 15s (won't hang UI anymore thanks to DOM diffing & Plotly.react)
        setInterval(updateDashboard, 15000);
    </script>
</body>
</html>'''

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
