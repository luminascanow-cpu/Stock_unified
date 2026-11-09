import hashlib
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

import numpy as np

from ..models.models import (
    NewsArticle, StockPrediction, SectorAnalysis,
    SentimentType, ImpactLevel, Alert, DashboardData
)
from ..services.news_service import NewsService
from ..services.advanced_sentiment import advanced_sentiment_service
from ..services.nse_service import nse_service, market_hours_service
from ..services.technical_analysis_service import technical_service, TechnicalData
from ..services.news_matching import contains_any
from ..utils.config import config

logger = logging.getLogger(__name__)


# ---- Sentiment → numeric helper ----
SENTIMENT_SCORE = {
    SentimentType.STRONG_BULLISH: 1.0,
    SentimentType.BULLISH: 0.5,
    SentimentType.NEUTRAL: 0.0,
    SentimentType.BEARISH: -0.5,
    SentimentType.STRONG_BEARISH: -1.0,
}

SIGNAL_SCORE = {
    'STRONG_BUY': 1.0,
    'BUY': 0.5,
    'NEUTRAL': 0.0,
    'SELL': -0.5,
    'STRONG_SELL': -1.0,
}

MARKET_EVENTS = [
    {
        "id": "rbi-mpc-2026-08",
        "title": "RBI MPC policy decision",
        "date": "2026-08-05",
        "category": "Rates",
        "impact": "high",
        "note": "Policy decision can move banks, NBFCs, INR, bonds, and rate-sensitive stocks.",
    },
    {
        "id": "india-cpi-2026-07",
        "title": "India CPI for July 2026",
        "date": "2026-08-12",
        "category": "Inflation",
        "impact": "high",
        "note": "Domestic inflation can reset RBI expectations and move banks, FMCG, INR, and bond yields.",
    },
    {
        "id": "us-cpi-2026-07",
        "title": "U.S. CPI for July 2026",
        "date": "2026-08-12",
        "category": "Global macro",
        "impact": "high",
        "note": "U.S. inflation can move Nasdaq, USD/INR, gold, IT stocks, and broader risk appetite.",
    },
    {
        "id": "jackson-hole-2026",
        "title": "Jackson Hole Symposium begins",
        "date": "2026-08-27",
        "category": "Central banks",
        "impact": "medium",
        "note": "Central-bank remarks can reset rate expectations, liquidity assumptions, and global risk tone.",
    },
    {
        "id": "fomc-2026-09",
        "title": "FOMC policy decision",
        "date": "2026-09-16",
        "category": "Global rates",
        "impact": "high",
        "note": "Fed decision and projections can move global equities, USD/INR, gold, and foreign flows.",
    },
    {
        "id": "us-cpi-2026-08",
        "title": "U.S. CPI for August 2026",
        "date": "2026-09-11",
        "category": "Global macro",
        "impact": "high",
        "note": "U.S. inflation can shift Fed pricing and spill into Indian IT, metals, and risk assets.",
    },
    {
        "id": "fomc-2026-10",
        "title": "FOMC policy decision",
        "date": "2026-10-28",
        "category": "Global rates",
        "impact": "high",
        "note": "Fed rates guidance can affect foreign flows, currency pressure, and valuation multiples.",
    },
    {
        "id": "us-cpi-2026-09",
        "title": "U.S. CPI for September 2026",
        "date": "2026-10-14",
        "category": "Global macro",
        "impact": "high",
        "note": "A major inflation print ahead of year-end Fed pricing and global asset allocation.",
    },
]


def get_upcoming_market_events(now: Optional[datetime] = None, limit: int = 8) -> List[Dict]:
    today = (now or datetime.now()).date()
    upcoming = []

    for event in MARKET_EVENTS:
        event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
        days_until = (event_date - today).days
        if days_until < 0:
            continue

        item = dict(event)
        item["days_until"] = days_until
        item["alert_on"] = (event_date - timedelta(days=1)).isoformat()
        item["source"] = "Built-in major market calendar"
        upcoming.append(item)

    upcoming.sort(key=lambda item: item["date"])
    return upcoming[:limit]


def compute_confluence(
    sentiment: SentimentType,
    tech: Optional[TechnicalData],
) -> Tuple[float, str]:
    """
    Blend sentiment + technical data into a confluence score [-1, +1].
    Formula: 0.5 * sentiment_score + 0.3 * psar_bias + 0.2 * ac_norm
    """
    s_score = SENTIMENT_SCORE.get(sentiment, 0.0)

    if tech is None:
        # No technical data — use sentiment only
        score = s_score
    else:
        psar_bias = 1.0 if tech.psar_trend == 'bull' else (-1.0 if tech.psar_trend == 'bear' else 0.0)
        # Normalise AC: clamp to [-0.01, 0.01] then scale to [-1, 1]
        ac_norm = max(-1.0, min(1.0, tech.ac / 0.005))
        score = 0.5 * s_score + 0.3 * psar_bias + 0.2 * ac_norm

    score = max(-1.0, min(1.0, score))

    if score >= 0.6:
        label = "Strong Confluence"
    elif score >= 0.2:
        label = "Aligned"
    elif score <= -0.6:
        label = "Strong Divergence"
    elif score <= -0.2:
        label = "Conflicting"
    else:
        label = "Neutral"

    return round(score, 3), label


@dataclass
class BacktestResult:
    symbol: str
    start_date: str
    end_date: str
    predicted_direction: str
    actual_direction: str
    predicted_return: float
    actual_return: float
    accuracy: bool
    confidence: float


class BacktestEngine:
    def __init__(self):
        self.prediction_config = config.prediction
        self.enabled = self.prediction_config.get('backtest_enabled', True)
        self.history: Dict[str, List[Dict]] = defaultdict(list)

    def record_prediction(self, symbol: str, prediction: Dict):
        if not self.enabled:
            return
        self.history[symbol].append({
            'timestamp': datetime.now(),
            'prediction': prediction.get('prediction'),
            'confidence': prediction.get('confidence', 0),
            'sentiment_score': prediction.get('sentiment_score', 0)
        })
        if len(self.history[symbol]) > 100:
            self.history[symbol] = self.history[symbol][-100:]


class PredictionEngineV2:
    def __init__(self):
        self.news_service = NewsService()
        self.nse_service = nse_service
        self.backtest_engine = BacktestEngine()
        self.alerts: List[Alert] = []
        self.prediction_config = config.prediction
        self._refresh_task: Optional[asyncio.Task] = None
        self._news_task: Optional[asyncio.Task] = None
        self._news_cache: List[NewsArticle] = []
        self._news_updated_at: Optional[datetime] = None

    async def generate_dashboard_data(self) -> DashboardData:
        import time
        start_time = time.time()
        print("Starting news fetch...")
        news_task = self.refresh_news()
        print("Starting technical fetch...")
        tech_task = technical_service.fetch_all()
        print("Starting Nifty fetch...")
        nifty_task = technical_service.get_nifty()

        news, tech_map, nifty = await asyncio.gather(
            news_task, tech_task, nifty_task,
            return_exceptions=True
        )
        print(f"Async gather completed in {time.time() - start_time:.1f}s")

        if isinstance(news, Exception):
            print(f"News error: {news}")
            news = []
        if isinstance(tech_map, Exception):
            print(f"Tech error: {tech_map}")
            tech_map = {}
        if isinstance(nifty, Exception):
            print(f"Nifty error: {nifty}")
            nifty = None
        # The original code had a duplicate block here, which is now removed as per the instruction's implied change.
        # The instruction provided a snippet that effectively replaces the original error logging with print statements.
        # The original block was:
        # if isinstance(news, Exception):
        #     logger.error(f"News fetch error: {news}")
        #     news = []
        # if isinstance(tech_map, Exception):
        #     logger.error(f"Technical fetch error: {tech_map}")
        #     tech_map = {}
        # if isinstance(nifty, Exception):
        #     nifty = None

        analyzed_news = news

        sector_analysis = await self.analyze_sectors(analyzed_news, tech_map)
        top_predictions = self.get_top_predictions(sector_analysis)
        upcoming_events = get_upcoming_market_events()
        alerts = self.generate_event_alerts(upcoming_events) + self.generate_alerts(analyzed_news, sector_analysis)

        # Record for backtest
        for pred in top_predictions:
            self.backtest_engine.record_prediction(pred.symbol, {
                'prediction': pred.prediction.value,
                'confidence': pred.confidence,
                'sentiment_score': SENTIMENT_SCORE.get(pred.prediction, 0.0),
            })

        market_summary = technical_service.compute_market_summary()

        return DashboardData(
            latest_news=analyzed_news[:20],
            sector_analysis=sector_analysis,
            top_predictions=top_predictions,
            alerts=alerts[:10],
            last_updated=datetime.now(),
            nifty=nifty,
            market_summary=market_summary,
            technical_updated=datetime.now().strftime('%H:%M:%S'),
            upcoming_events=upcoming_events,
        )

    async def analyze_sectors(
        self,
        news: List[NewsArticle],
        tech_map: Dict[str, TechnicalData],
    ) -> List[SectorAnalysis]:
        sectors_data = []

        for sector in config.sectors:
            sector_name = sector['name']
            keywords = sector.get('keywords', [])
            stock_symbols = sector.get('stocks', [])

            sector_news = self._filter_news_by_sector(news, keywords)
            sentiment_score, sentiment_label = advanced_sentiment_service.calculate_sector_sentiment(
                sector_news, keywords
            )
            confidence = self._calculate_confidence(
                sentiment_score, len(sector_news),
                any(n.is_breaking for n in sector_news)
            )

            # Compute avg AC for sector
            sector_ac_vals = [
                tech_map[sym].ac
                for sym in stock_symbols
                if sym in tech_map
            ]
            avg_ac = round(float(np.mean(sector_ac_vals)), 4) if sector_ac_vals else 0.0

            # Dominant tech signal
            signals = [tech_map[sym].signal_strength for sym in stock_symbols if sym in tech_map]
            buy_count = sum(1 for s in signals if 'BUY' in s)
            sell_count = sum(1 for s in signals if 'SELL' in s)
            if buy_count > sell_count:
                tech_signal = 'BUY' if buy_count < len(signals) * 0.7 else 'STRONG_BUY'
            elif sell_count > buy_count:
                tech_signal = 'SELL' if sell_count < len(signals) * 0.7 else 'STRONG_SELL'
            else:
                tech_signal = 'NEUTRAL'

            predictions = []
            for symbol in stock_symbols:
                tech = tech_map.get(symbol)
                pred = await self._create_prediction(
                    symbol, sector_name, sentiment_label, confidence,
                    sector_news[:3], tech
                )
                predictions.append(pred)

            sector_analysis = SectorAnalysis(
                name=sector_name,
                overall_sentiment=sentiment_label,
                confidence=confidence,
                affected_stocks=predictions,
                news_count=len(sector_news),
                avg_ac=avg_ac,
                tech_signal=tech_signal,
                top_url=sector_news[0].url if sector_news else None
            )
            sectors_data.append(sector_analysis)

        sectors_data.sort(key=lambda x: abs(x.confidence), reverse=True)
        return sectors_data

    async def _create_prediction(
        self,
        symbol: str,
        sector: str,
        sentiment: SentimentType,
        confidence: float,
        related_news: List[NewsArticle],
        tech: Optional[TechnicalData],
    ) -> StockPrediction:
        confluence_score, confluence_label = compute_confluence(sentiment, tech)

        return StockPrediction(
            symbol=symbol,
            name=symbol,
            sector=sector,
            prediction=sentiment,
            confidence=confidence,
            impact_level=self._determine_impact_level(confidence, sentiment),
            related_news=[n.title for n in related_news[:3]],
            price_info=None,
            # Technical fields
            ltp=tech.ltp if tech else None,
            change_percent=tech.change_percent if tech else None,
            velocity=tech.velocity if tech else None,
            ac=tech.ac if tech else None,
            psar_af=tech.psar_af if tech else None,
            psar_trend=tech.psar_trend if tech else None,
            signal_strength=tech.signal_strength if tech else None,
            high_52w=tech.high_52w if tech else None,
            distance_52w=tech.distance_52w if tech else None,
            reversal_count=tech.reversal_count if tech else 0,
            af_increase_rate=tech.af_increase_rate if tech else 0.0,
            # Confluence
            confluence_score=confluence_score,
            confluence_label=confluence_label,
        )

    def _filter_news_by_sector(self, news: List[NewsArticle], keywords: List[str]) -> List[NewsArticle]:
        filtered = []
        for article in news:
            text = (article.title + ' ' + article.description).lower()
            if contains_any(text, keywords):
                filtered.append(article)
                if keywords:
                    article.affected_sectors.append(keywords[0])
        return filtered

    def _calculate_confidence(self, sentiment_score: float, news_count: int, is_breaking: bool) -> float:
        base = abs(sentiment_score)
        news_factor = min(news_count / 10, 1.0)
        breaking_factor = 1.2 if is_breaking else 1.0
        return min((base * 0.6 + news_factor * 0.4) * breaking_factor, 1.0)

    def _determine_impact_level(self, confidence: float, sentiment: SentimentType) -> ImpactLevel:
        if confidence >= 0.7 and sentiment in [SentimentType.STRONG_BULLISH, SentimentType.STRONG_BEARISH]:
            return ImpactLevel.HIGH
        elif confidence >= 0.4:
            return ImpactLevel.MEDIUM
        return ImpactLevel.LOW

    def get_top_predictions(self, sector_analysis: List[SectorAnalysis]) -> List[StockPrediction]:
        all_preds = []
        for sector in sector_analysis:
            for pred in sector.affected_stocks:
                if pred.confidence >= self.prediction_config.get('min_confidence', 0.2):
                    all_preds.append(pred)

        # Sort by absolute confluence score (highest conviction first)
        all_preds.sort(
            key=lambda x: (abs(x.confluence_score or 0), x.impact_level == ImpactLevel.HIGH),
            reverse=True
        )
        return all_preds

    def generate_event_alerts(self, upcoming_events: List[Dict]) -> List[Alert]:
        alerts = []

        for event in upcoming_events:
            if event.get("days_until") != 1:
                continue

            alert = Alert(
                id=hashlib.md5(f"market-event:{event['id']}:{event['date']}".encode()).hexdigest()[:8],
                timestamp=datetime.now(),
                title=f"Event tomorrow: {event['title']}",
                message=f"{event['date']} | {event['note']}",
                severity="high" if event.get("impact") == "high" else "medium",
                related_sectors=[event.get("category", "Market event")],
                related_stocks=[],
            )
            alerts.append(alert)

        return alerts

    def generate_alerts(self, news: List[NewsArticle], sector_analysis: List[SectorAnalysis]) -> List[Alert]:
        alerts = []

        for article in news:
            if article.is_breaking:
                alert = Alert(
                    id=hashlib.md5(article.id.encode()).hexdigest()[:8],
                    timestamp=article.published_at,
                    title=f"Breaking: {article.title[:60]}",
                    message=f"Breaking news from {article.source}. Sentiment: {article.sentiment_label.value}",
                    severity="high",
                    related_sectors=article.affected_sectors[:3],
                    related_stocks=[],
                    url=article.url
                )
                alerts.append(alert)

        for sector in sector_analysis:
            # Alert when strong sentiment + supporting tech signal (confluence)
            if sector.confidence >= 0.55 and sector.overall_sentiment in [
                SentimentType.STRONG_BULLISH, SentimentType.STRONG_BEARISH
            ]:
                tech_aligned = (
                    (sector.overall_sentiment in [SentimentType.STRONG_BULLISH, SentimentType.BULLISH]
                     and sector.tech_signal in ['BUY', 'STRONG_BUY'])
                    or
                    (sector.overall_sentiment in [SentimentType.STRONG_BEARISH, SentimentType.BEARISH]
                     and sector.tech_signal in ['SELL', 'STRONG_SELL'])
                )
                prefix = "⚡ Confluence Alert" if tech_aligned else "📰 Sentiment Alert"
                alert = Alert(
                    id=hashlib.md5(f"{sector.name}{datetime.now().date()}".encode()).hexdigest()[:8],
                    timestamp=datetime.now(),
                    title=f"{prefix}: {sector.name}",
                    message=(
                        f"{sector.name} shows {sector.overall_sentiment.value} sentiment "
                        f"({sector.confidence:.0%} confidence) with tech signal: {sector.tech_signal}. "
                        f"Avg AC: {sector.avg_ac:+.4f}. {sector.news_count} news articles."
                    ),
                    severity="high" if tech_aligned else "medium",
                    related_sectors=[sector.name],
                    related_stocks=[p.symbol for p in sector.affected_stocks[:5]],
                    url=sector.top_url
                )
                alerts.append(alert)

        alerts.sort(key=lambda x: (x.severity == 'high', x.timestamp), reverse=True)
        self.alerts = alerts
        return alerts

    async def refresh_data(self) -> DashboardData:
        if self._refresh_task and not self._refresh_task.done():
            return await asyncio.shield(self._refresh_task)
        self._refresh_task = asyncio.create_task(self.generate_dashboard_data())
        try:
            return await asyncio.shield(self._refresh_task)
        finally:
            if self._refresh_task and self._refresh_task.done():
                self._refresh_task = None

    async def refresh_news(self, force: bool = False) -> List[NewsArticle]:
        if (
            not force
            and self._news_cache
            and self._news_updated_at
            and (datetime.now() - self._news_updated_at).total_seconds() < 45
        ):
            return list(self._news_cache)
        if self._news_task and not self._news_task.done():
            return await asyncio.shield(self._news_task)
        self._news_task = asyncio.create_task(self._refresh_news_once())
        try:
            return await asyncio.shield(self._news_task)
        finally:
            if self._news_task and self._news_task.done():
                self._news_task = None

    async def _refresh_news_once(self) -> List[NewsArticle]:
        articles = await self.news_service.fetch_all_news()
        analyzed = await asyncio.to_thread(
            advanced_sentiment_service.analyze_articles,
            articles,
        )
        if analyzed:
            self._news_cache = analyzed
            self._news_updated_at = datetime.now()
        return list(self._news_cache)


prediction_engine_v2 = PredictionEngineV2()
