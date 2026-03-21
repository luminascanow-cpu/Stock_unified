import hashlib
from datetime import datetime
from typing import List, Dict
import asyncio

from ..models.models import (
    NewsArticle, StockPrediction, SectorAnalysis, 
    SentimentType, ImpactLevel, Alert, DashboardData
)
from ..services.news_service import NewsService
from ..services.sentiment_service import SentimentService
from ..services.stock_service import StockService
from ..utils.config import config

class PredictionEngine:
    def __init__(self):
        self.news_service = NewsService()
        self.sentiment_service = SentimentService()
        self.stock_service = StockService()
        self.alerts: List[Alert] = []
        
    async def generate_dashboard_data(self) -> DashboardData:
        """Generate complete dashboard data"""
        news = await self.news_service.fetch_all_news()
        
        analyzed_news = []
        for article in news:
            analyzed = self.sentiment_service.analyze_article(article)
            analyzed_news.append(analyzed)
        
        sector_analysis = await self.analyze_sectors(analyzed_news)
        
        top_predictions = self.get_top_predictions(sector_analysis)
        
        alerts = self.generate_alerts(analyzed_news, sector_analysis)
        
        return DashboardData(
            latest_news=analyzed_news[:20],
            sector_analysis=sector_analysis,
            top_predictions=top_predictions[:10],
            alerts=alerts[:10],
            last_updated=datetime.now()
        )
    
    async def analyze_sectors(self, news: List[NewsArticle]) -> List[SectorAnalysis]:
        """Analyze sentiment for each sector"""
        sectors_data = []
        sectors = config.sectors
        
        for sector in sectors:
            sector_name = sector['name']
            keywords = sector.get('keywords', [])
            stock_symbols = sector.get('stocks', [])
            
            sector_news = self._filter_news_by_sector(news, keywords)
            
            sentiment_score, sentiment_label = self.sentiment_service.calculate_sector_sentiment(
                sector_news, keywords
            )
            
            confidence = self.stock_service.calculate_confidence(
                sentiment_score,
                len(sector_news),
                any(n.is_breaking for n in sector_news)
            )
            
            price_info = None
            if stock_symbols:
                try:
                    stock_data = await self.stock_service.get_stock_info(stock_symbols[:3])
                    price_info = stock_data
                except:
                    pass
            
            predictions = []
            for symbol in stock_symbols[:5]:
                pred = StockPrediction(
                    symbol=symbol,
                    name=symbol,
                    sector=sector_name,
                    prediction=sentiment_label,
                    confidence=confidence,
                    impact_level=self.stock_service.determine_impact_level(confidence, sentiment_label),
                    related_news=[n.title for n in sector_news[:3]],
                    price_info=price_info.get(symbol) if price_info else None
                )
                predictions.append(pred)
            
            sector_analysis = SectorAnalysis(
                name=sector_name,
                overall_sentiment=sentiment_label,
                confidence=confidence,
                affected_stocks=predictions,
                news_count=len(sector_news)
            )
            sectors_data.append(sector_analysis)
        
        sectors_data.sort(key=lambda x: x.confidence, reverse=True)
        return sectors_data
    
    def _filter_news_by_sector(self, news: List[NewsArticle], keywords: List[str]) -> List[NewsArticle]:
        """Filter news articles relevant to a sector"""
        filtered = []
        for article in news:
            text = (article.title + ' ' + article.description).lower()
            if any(kw.lower() in text for kw in keywords):
                filtered.append(article)
                article.affected_sectors.append(keywords[0] if keywords else '')
        return filtered
    
    def get_top_predictions(self, sector_analysis: List[SectorAnalysis]) -> List[StockPrediction]:
        """Get top stock predictions across all sectors"""
        all_predictions = []
        
        for sector in sector_analysis:
            for pred in sector.affected_stocks:
                if pred.confidence >= config.prediction.get('min_confidence', 0.3):
                    all_predictions.append(pred)
        
        all_predictions.sort(key=lambda x: (x.confidence, x.impact_level == ImpactLevel.HIGH), reverse=True)
        return all_predictions
    
    def generate_alerts(self, news: List[NewsArticle], sector_analysis: List[SectorAnalysis]) -> List[Alert]:
        """Generate alerts based on news and predictions"""
        alerts = []
        
        for article in news:
            if article.is_breaking:
                alert = Alert(
                    id=hashlib.md5(article.id.encode()).hexdigest()[:8],
                    timestamp=article.published_at,
                    title=f"Breaking: {article.title[:50]}...",
                    message=f"Breaking news from {article.source}. Sentiment: {article.sentiment_label.value}",
                    severity="high",
                    related_sectors=article.affected_sectors[:3],
                    related_stocks=[]
                )
                alerts.append(alert)
        
        for sector in sector_analysis:
            if sector.confidence >= 0.6 and sector.overall_sentiment in [
                SentimentType.STRONG_BULLISH, SentimentType.STRONG_BEARISH
            ]:
                alert = Alert(
                    id=hashlib.md5(f"{sector.name}{datetime.now()}".encode()).hexdigest()[:8],
                    timestamp=datetime.now(),
                    title=f"High Impact: {sector.name} Sector",
                    message=f"{sector.name} sector showing {sector.overall_sentiment.value} sentiment with {sector.confidence:.0%} confidence ({sector.news_count} news articles)",
                    severity="medium",
                    related_sectors=[sector.name],
                    related_stocks=[p.symbol for p in sector.affected_stocks[:3]]
                )
                alerts.append(alert)
        
        alerts.sort(key=lambda x: (x.severity == 'high', x.timestamp), reverse=True)
        self.alerts = alerts
        return alerts
    
    async def refresh_data(self) -> DashboardData:
        """Refresh all data"""
        return await self.generate_dashboard_data()
