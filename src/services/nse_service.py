import asyncio
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from functools import lru_cache
import logging

try:
    from nsepython import nsefetch
    NSEPY_AVAILABLE = True
except ImportError:
    NSEPY_AVAILABLE = False
    logging.warning("nsepython not installed")

import aiohttp

from ..models.models import StockPrediction, SentimentType, ImpactLevel
from ..utils.config import config

logger = logging.getLogger(__name__)

class StockCache:
    def __init__(self, ttl: int = 300):
        self._cache: Dict[str, tuple] = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[dict]:
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return data
            del self._cache[key]
        return None
    
    def set(self, key: str, data: dict):
        self._cache[key] = (data, time.time())
    
    def clear(self):
        self._cache.clear()

class NSEService:
    def __init__(self):
        self.sectors = config.sectors
        self.nse_config = config.get('nse', {})
        self.cache = StockCache(ttl=self.nse_config.get('cache_duration', 300))
        self.enabled = self.nse_config.get('enabled', True) and NSEPY_AVAILABLE
    
    def _get_cache_key(self, symbol: str) -> str:
        return f"nse_{symbol}"
    
    async def get_quote(self, symbol: str) -> Optional[Dict]:
        if not self.enabled:
            return None
        
        cache_key = self._get_cache_key(symbol)
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            quote = await self._fetch_nse_quote(symbol)
            if quote:
                self.cache.set(cache_key, quote)
            return quote
        except Exception as e:
            logger.warning(f"NSE fetch failed for {symbol}: {e}")
            return None
    
    async def _fetch_nse_quote(self, symbol: str) -> Optional[Dict]:
        try:
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/json',
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_nse_quote(data, symbol)
        except Exception as e:
            logger.error(f"NSE API error for {symbol}: {e}")
        return None
    
    def _parse_nse_quote(self, data: dict, symbol: str) -> Dict:
        metadata = data.get('info', {})
        price_info = data.get('priceInfo', {})
        
        return {
            'symbol': symbol,
            'name': metadata.get('companyName', symbol),
            'current_price': price_info.get('lastPrice', 0),
            'change': price_info.get('change', 0),
            'change_percent': price_info.get('pChange', 0),
            'open': price_info.get('open', 0),
            'high': price_info.get('high', 0),
            'low': price_info.get('low', 0),
            'previous_close': price_info.get('previousClose', 0),
            'volume': price_info.get('totalTradedVolume', 0),
            'value': price_info.get('totalTradedValue', 0),
            'day_high': price_info.get('dayHigh', 0),
            'day_low': price_info.get('dayLow', 0),
            'year_high': price_info.get('yearHigh', 0),
            'year_low': price_info.get('yearLow', 0),
            'market_cap': price_info.get('marketCap', 0),
            'timestamp': datetime.now().isoformat()
        }
    
    async def _get_yahoo_quote(self, symbol: str) -> Optional[Dict]:
        return None
    
    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        results = {}
        
        tasks = [self.get_quote(s) for s in symbols]
        quotes = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, quote in zip(symbols, quotes):
            if isinstance(quote, dict):
                results[symbol] = quote
            else:
                results[symbol] = {'symbol': symbol, 'error': str(quote)[:50] if quote else 'Unknown error'}
        
        return results
    
    async def get_sector_quotes(self, sector_name: str) -> Dict[str, Dict]:
        stocks = self.get_sector_stocks(sector_name)
        return await self.get_multiple_quotes(stocks[:10])
    
    def get_sector_stocks(self, sector_name: str) -> List[str]:
        for sector in self.sectors:
            if sector['name'].lower() == sector_name.lower():
                return sector.get('stocks', [])
        return []
    
    def get_all_sectors(self) -> List[str]:
        return [s['name'] for s in self.sectors]
    
    def get_sector_keywords(self, sector_name: str) -> List[str]:
        for sector in self.sectors:
            if sector['name'].lower() == sector_name.lower():
                return sector.get('keywords', [])
        return []
    
    def clear_cache(self):
        self.cache.clear()


class MarketHoursService:
    def __init__(self):
        self.market_config = config.get('market_hours', {})
        self.enabled = self.market_config.get('enabled', True)
    
    def is_market_open(self) -> bool:
        if not self.enabled:
            return True
        
        now = datetime.now()
        
        if now.weekday() >= 5:
            return False
        
        start_time = self.market_config.get('start_time', '09:15')
        end_time = self.market_config.get('end_time', '15:30')
        
        start_h, start_m = map(int, start_time.split(':'))
        end_h, end_m = map(int, end_time.split(':'))
        
        now_time = now.time()
        start = start_h * 60 + start_m
        end = end_h * 60 + end_m
        current = now.hour * 60 + now.minute
        
        return start <= current <= end
    
    def get_next_open_time(self) -> Optional[datetime]:
        now = datetime.now()
        
        if self.is_market_open():
            return now
        
        for i in range(1, 8):
            check_date = now + timedelta(days=i)
            if check_date.weekday() < 5:
                start_h, start_m = map(int, self.market_config.get('start_time', '09:15').split(':'))
                return check_date.replace(hour=start_h, minute=start_m, second=0)
        
        return None
    
    def get_time_until_open(self) -> Optional[timedelta]:
        if self.is_market_open():
            return None
        
        next_open = self.get_next_open_time()
        if next_open:
            return next_open - datetime.now()
        return None
    
    def should_run_scheduler(self) -> bool:
        return self.is_market_open()


nse_service = NSEService()
market_hours_service = MarketHoursService()