import yfinance as yf
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import asyncio
import aiohttp

from ..models.models import StockPrediction, SentimentType, ImpactLevel
from ..utils.config import config

class StockService:
    def __init__(self):
        self.sectors = config.sectors
        self.prediction_config = config.prediction
        
    async def get_stock_info(self, symbols: List[str]) -> Dict[str, Dict]:
        """Fetch stock information for given symbols"""
        stock_info = {}
        
        async def fetch_single(symbol):
            try:
                ticker = yf.Ticker(f"{symbol}.NS")
                info = ticker.info
                
                await asyncio.sleep(0.5)
                
                return symbol, {
                    'name': info.get('shortName', symbol),
                    'current_price': info.get('currentPrice', info.get('previousClose', 0)),
                    'change': info.get('regularMarketChange', 0),
                    'change_percent': info.get('regularMarketChangePercent', 0),
                    'volume': info.get('volume', 0),
                    'market_cap': info.get('marketCap', 0),
                    'day_high': info.get('dayHigh', 0),
                    'day_low': info.get('dayLow', 0),
                }
            except Exception as e:
                return symbol, {'name': symbol, 'error': str(e)[:50]}
        
        tasks = [fetch_single(s) for s in symbols[:3]]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, tuple):
                stock_info[result[0]] = result[1]
        
        return stock_info
    
    def get_sector_stocks(self, sector_name: str) -> List[str]:
        """Get list of stock symbols for a sector"""
        for sector in self.sectors:
            if sector['name'].lower() == sector_name.lower():
                return sector.get('stocks', [])
        return []
    
    def get_all_sectors(self) -> List[str]:
        """Get all sector names"""
        return [s['name'] for s in self.sectors]
    
    def get_sector_keywords(self, sector_name: str) -> List[str]:
        """Get keywords for a sector"""
        for sector in self.sectors:
            if sector['name'].lower() == sector_name.lower():
                return sector.get('keywords', [])
        return []
    
    def calculate_confidence(self, sentiment_score: float, news_count: int, is_breaking: bool) -> float:
        """Calculate prediction confidence"""
        base_confidence = abs(sentiment_score)
        
        news_factor = min(news_count / 10, 1.0)
        
        breaking_factor = 1.2 if is_breaking else 1.0
        
        confidence = (base_confidence * 0.6 + news_factor * 0.4) * breaking_factor
        return min(confidence, 1.0)
    
    def determine_impact_level(self, confidence: float, sentiment: SentimentType) -> ImpactLevel:
        """Determine impact level based on confidence and sentiment"""
        if confidence >= 0.7 and sentiment in [SentimentType.STRONG_BULLISH, SentimentType.STRONG_BEARISH]:
            return ImpactLevel.HIGH
        elif confidence >= 0.4:
            return ImpactLevel.MEDIUM
        return ImpactLevel.LOW
    
    def create_prediction(
        self,
        symbol: str,
        sector: str,
        sentiment: SentimentType,
        confidence: float,
        related_news: List[str],
        price_info: Optional[Dict] = None
    ) -> StockPrediction:
        """Create a stock prediction object"""
        stock_list = self.get_sector_stocks(sector)
        stock_names = {
            'HAL': 'Hindustan Aeronautics Ltd',
            'BEL': 'Bharat Electronics Ltd',
            'L&T': 'Larsen & Toubro Ltd',
            'ONGC': 'Oil & Natural Gas Corp',
            'IOC': 'Indian Oil Corp',
            'TCS': 'Tata Consultancy Services',
            'INFY': 'Infosys Ltd',
            'SBIN': 'State Bank of India',
            'HDFCBANK': 'HDFC Bank Ltd',
            'RELIANCE': 'Reliance Industries Ltd',
            'TATAMOTORS': 'Tata Motors Ltd',
            'SUNPHARMA': 'Sun Pharmaceutical',
            'TATASTEEL': 'Tata Steel Ltd',
        }
        
        return StockPrediction(
            symbol=sector,
            name=stock_names.get(symbol, symbol),
            sector=sector,
            prediction=sentiment,
            confidence=confidence,
            impact_level=self.determine_impact_level(confidence, sentiment),
            related_news=related_news,
            price_info=price_info
        )
