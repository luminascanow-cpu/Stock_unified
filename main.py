"""
🚀 Unified Stock Analysis Platform
Merges technical analysis (PSAR + AC) with sentiment analysis (NLP + news)
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import uvicorn

from models.unified import StockSignal, NewsArticle, SectorAnalysis, Alert, DashboardData
from services.technical_service import TechnicalService
from services.sentiment_service import SentimentService
from services.confluence_engine import ConfluenceEngine
from utils.config import config

# ----------------------------------
# Logging
# ----------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_unified.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ----------------------------------
# Global Services
# ----------------------------------
technical_service = TechnicalService()
sentiment_service = SentimentService()
confluence_engine = ConfluenceEngine()

# ----------------------------------
# Lifespan
# ----------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Unified Stock Platform...")
    # Start background refresh loop
    asyncio.create_task(refresh_loop())
    yield
    # Shutdown
    logger.info("Shutting down...")

# ----------------------------------
# FastAPI App
# ----------------------------------
app = FastAPI(
    title="🚀 Unified Stock Analysis Platform",
    description="Technical + Sentiment analysis for Indian stocks",
    version="1.0.0",
    lifespan=lifespan
)

# ----------------------------------
# Background Refresh
# ----------------------------------
async def refresh_loop():
    """Main data refresh loop"""
    while True:
        try:
            logger.info("📊 Refreshing data...")
            
            # Fetch technical data (Yahoo Finance)
            tech_data = await technical_service.fetch_all_tickers()
            
            # Fetch sentiment data (News)
            news_data = await sentiment_service.fetch_news()
            
            # Generate confluence signals
            signals = confluence_engine.generate_signals(tech_data, news_data)
            
            logger.info(f"✅ Generated {len(signals)} confluence signals")
            
            # Sleep until next refresh
            await asyncio.sleep(config.refresh_interval_seconds)
            
        except Exception as e:
            logger.error(f"Refresh loop error: {e}")
            await asyncio.sleep(60)

# ----------------------------------
# API Routes
# ----------------------------------

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "technical": technical_service.is_healthy(),
            "sentiment": sentiment_service.is_healthy()
        }
    }

@app.get("/api/stocks")
async def get_all_stocks():
    """Get all stocks with confluence signals"""
    signals = confluence_engine.get_all_signals()
    return {
        "stocks": signals,
        "last_updated": datetime.now().isoformat(),
        "total": len(signals)
    }

@app.get("/api/ticker/{symbol}")
async def get_ticker_detail(symbol: str):
    """Get detailed data for specific ticker"""
    signal = confluence_engine.get_signal(symbol.upper())
    if signal:
        return signal
    return JSONResponse(
        status_code=404,
        content={"error": "Ticker not found"}
    )

@app.get("/api/news")
async def get_news(limit: int = 20):
    """Get latest news"""
    news = await sentiment_service.fetch_news()
    return {"news": news[:limit]}

@app.get("/api/sectors")
async def get_sectors():
    """Get sector analysis"""
    sectors = confluence_engine.get_sector_analysis()
    return {"sectors": sectors}

@app.get("/api/alerts")
async def get_alerts():
    """Get active alerts"""
    alerts = confluence_engine.get_alerts()
    return {"alerts": alerts}

@app.get("/api/confluence/{symbol}")
async def get_confluence_score(symbol: str):
    """Get confluence score for a stock"""
    score = confluence_engine.calculate_confluence(symbol.upper())
    return score

# ----------------------------------
# WebSocket for real-time updates
# ----------------------------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Send updated data every refresh cycle
            data = {
                "type": "update",
                "stocks": confluence_engine.get_all_signals(),
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_json(data)
            await asyncio.sleep(config.refresh_interval_seconds)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")

# ----------------------------------
# Main
# ----------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info"
    )
