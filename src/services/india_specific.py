import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

from ..utils.config import config

try:
    pass
except ImportError:
    pass


@dataclass
class ElectionData:
    source: str
    headline: str
    date: datetime
    impact: str
    sentiment: str


@dataclass
class MonsoonData:
    region: str
    rainfall: float
    normal_rainfall: float
    status: str
    date: datetime


@dataclass
class FIIData:
    date: str
    fii_buy: float
    fii_sell: float
    fii_net: float
    dii_buy: float
    dii_sell: float
    dii_net: float


@dataclass
class CurrencyData:
    pair: str
    rate: float
    change: float
    change_percent: float
    timestamp: datetime


class ElectionMonitor:
    def __init__(self):
        self.config = config.get('india_specific', {}).get('election_monitoring', {})
        self.enabled = self.config.get('enabled', True)
        self.eci_url = self.config.get('eci_rss', '')
    
    async def fetch_latest_news(self) -> List[ElectionData]:
        return []
    
    def analyze_impact(self, headline: str) -> Dict:
        headline_lower = headline.lower()
        
        impact_keywords = {
            'market_positive': ['growth', 'development', 'reform', 'infrastructure boost', 'fdi'],
            'market_negative': ['instability', 'policy uncertainty', 'delay', 'controversy'],
            'sector_specific': {
                'defense': ['defense', 'security', 'military'],
                'infrastructure': ['roads', 'highways', 'construction', 'real estate'],
                'agriculture': ['farmer', 'msp', 'procurement', 'mandi'],
                'energy': ['oil', 'gas', 'power', 'renewable'],
                'finance': ['tax', 'fiscal', 'budget', 'gst']
            }
        }
        
        impact = 'neutral'
        sentiment = 'neutral'
        
        for keyword in impact_keywords['market_positive']:
            if keyword in headline_lower:
                impact = 'positive'
                sentiment = 'bullish'
                break
        
        for keyword in impact_keywords['market_negative']:
            if keyword in headline_lower:
                impact = 'negative'
                sentiment = 'bearish'
                break
        
        return {'impact': impact, 'sentiment': sentiment}


class MonsoonTracker:
    def __init__(self):
        self.config = config.get('india_specific', {}).get('monsoon_tracking', {})
        self.enabled = self.config.get('enabled', True)
        self.imd_url = self.config.get('imd_url', '')
    
    async def get_current_status(self) -> Optional[MonsoonData]:
        return MonsoonData(
            region='India',
            rainfall=0,
            normal_rainfall=0,
            status='Data not available',
            date=datetime.now()
        )
    
    def analyze_impact(self, rainfall_status: str) -> Dict:
        status_lower = rainfall_status.lower()
        
        if 'excess' in status_lower or 'above normal' in status_lower:
            return {
                'impact': 'positive',
                'sentiment': 'bullish',
                'sectors': ['agriculture', 'fertilizer', ' FMCG', 'rural consumption'],
                'description': 'Good monsoon boosts rural income and agricultural output'
            }
        elif 'deficit' in status_lower or 'below normal' in status_lower:
            return {
                'impact': 'negative',
                'sentiment': 'bearish',
                'sectors': ['agriculture', 'fertilizer', 'FMCG', 'rural consumption'],
                'description': 'Poor monsoon could impact rural demand and agricultural GDP'
            }
        
        return {
            'impact': 'neutral',
            'sentiment': 'neutral',
            'sectors': [],
            'description': 'Normal monsoon expected'
        }


class BudgetAnalyzer:
    def __init__(self):
        self.config = config.get('india_specific', {}).get('budget_analyzer', {})
        self.enabled = self.config.get('enabled', True)
        self.cache = {}
    
    async def analyze_budget_speech(self, text: str) -> Dict:
        text_lower = text.lower()
        
        sector_impacts = {
            'infrastructure': [],
            'defense': [],
            'agriculture': [],
            'healthcare': [],
            'education': [],
            'energy': [],
            'technology': [],
            'finance': []
        }
        
        if 'infrastructure' in text_lower or 'roads' in text_lower or 'highway' in text_lower:
            sector_impacts['infrastructure'].append('positive')
        
        if 'defense' in text_lower or 'military' in text_lower:
            sector_impacts['defense'].append('positive')
        
        if 'msp' in text_lower or 'farmer' in text_lower or 'agriculture' in text_lower:
            sector_impacts['agriculture'].append('positive')
        
        if 'health' in text_lower or 'hospital' in text_lower:
            sector_impacts['healthcare'].append('positive')
        
        if 'tax' in text_lower or 'direct tax' in text_lower:
            if 'cut' in text_lower or 'reduce' in text_lower or 'rationalize' in text_lower:
                sector_impacts['finance'].append('positive')
            else:
                sector_impacts['finance'].append('negative')
        
        if 'digital' in text_lower or 'technology' in text_lower or 'startup' in text_lower:
            sector_impacts['technology'].append('positive')
        
        overall_sentiment = 'neutral'
        positive_sectors = sum(1 for v in sector_impacts.values() if v)
        if positive_sectors >= 3:
            overall_sentiment = 'bullish'
        elif positive_sectors <= 1:
            overall_sentiment = 'bearish'
        
        return {
            'sector_impacts': sector_impacts,
            'overall_sentiment': overall_sentiment,
            'summary': f"Budget shows positive impact on {positive_sectors} sectors"
        }


class FIIDIIFlowTracker:
    def __init__(self):
        self.config = config.get('india_specific', {}).get('fii_dii_flow', {})
        self.enabled = self.config.get('enabled', True)
        self.cache = {}
        self.cache_duration = 300
    
    async def get_latest_flow(self) -> Optional[FIIData]:
        try:
            # Removed yfinance dependency for NIFTY. Returning defaults.
            return FIIData(
                date=datetime.now().strftime('%Y-%m-%d'),
                fii_buy=0,
                fii_sell=0,
                fii_net=0,
                dii_buy=0,
                dii_sell=0,
                dii_net=0
            )
        except Exception as e:
            logger.error(f"FII/DII flow error: {e}")
        
        return FIIData(
            date=datetime.now().strftime('%Y-%m-%d'),
            fii_buy=0,
            fii_sell=0,
            fii_net=0,
            dii_buy=0,
            dii_sell=0,
            dii_net=0
        )
    
    def analyze_impact(self, fii_net: float, dii_net: float) -> Dict:
        total_net = fii_net + dii_net
        
        if total_net > 0:
            return {
                'sentiment': 'bullish',
                'impact': 'positive',
                'description': 'Net buying from FIIs and DIIs indicates positive sentiment'
            }
        elif total_net < 0:
            return {
                'sentiment': 'bearish',
                'impact': 'negative',
                'description': 'Net selling from FIIs and DIIs indicates negative sentiment'
            }
        
        return {
            'sentiment': 'neutral',
            'impact': 'neutral',
            'description': 'No significant FII/DII activity'
        }


class CurrencyImpactAnalyzer:
    def __init__(self):
        self.config = config.get('india_specific', {}).get('currency_impact', {})
        self.enabled = self.config.get('enabled', True)
        self.pairs = self.config.get('pairs', ['USD/INR'])
        self._quote_cache: Optional[Dict] = None
        self._quote_cache_ts: Optional[datetime] = None
        self.cache_duration = self.config.get('cache_duration', 60)

    async def get_usd_inr_quote(self) -> Dict:
        now = datetime.now()
        if (
            self._quote_cache
            and self._quote_cache_ts
            and (now - self._quote_cache_ts).total_seconds() < self.cache_duration
        ):
            return self._quote_cache

        quote = {
            'symbol': 'USDINR',
            'label': 'USD/INR',
            'value': None,
            'change': None,
            'change_percent': None,
            'source': 'Yahoo Finance',
            'timestamp': now.isoformat()
        }

        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/USDINR=X?range=1d&interval=1m"
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=8) as response:
                    if response.status == 200:
                        payload = await response.json()
                        result = payload.get('chart', {}).get('result', [])
                        meta = result[0].get('meta', {}) if result else {}
                        current = meta.get('regularMarketPrice')
                        previous = meta.get('chartPreviousClose') or meta.get('previousClose')

                        if current is not None:
                            change = (float(current) - float(previous)) if previous else None
                            quote.update({
                                'value': round(float(current), 4),
                                'change': round(change, 4) if change is not None else None,
                                'change_percent': round((change / float(previous)) * 100, 3) if change is not None and previous else None,
                                'timestamp': datetime.fromtimestamp(meta.get('regularMarketTime', now.timestamp())).isoformat()
                            })
        except Exception as e:
            logger.warning(f"USD/INR live quote failed: {e}")

        if quote['value'] is None:
            try:
                url = "https://open.er-api.com/v6/latest/USD"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers={"Accept": "application/json"}, timeout=8) as response:
                        if response.status == 200:
                            payload = await response.json()
                            rate = payload.get('rates', {}).get('INR')
                            if rate is not None:
                                quote.update({
                                    'value': round(float(rate), 4),
                                    'change': 0.0,
                                    'change_percent': 0.0,
                                    'source': 'ExchangeRate API',
                                    'timestamp': datetime.fromtimestamp(payload.get('time_last_update_unix', now.timestamp())).isoformat()
                                })
            except Exception as e:
                logger.warning(f"USD/INR fallback quote failed: {e}")

        if quote['value'] is None:
            quote.update({
                'value': 83.5,
                'change': 0.0,
                'change_percent': 0.0,
                'source': 'Fallback',
                'timestamp': now.isoformat()
            })

        self._quote_cache = quote
        self._quote_cache_ts = now
        return quote
    
    async def get_rates(self) -> List[CurrencyData]:
        results = []
        
        for pair in self.pairs:
            try:
                base, quote = pair.split('/')
                if base == 'USD':
                    usd_inr = await self.get_usd_inr_quote()
                    current = usd_inr['value'] or 83.5
                    change = usd_inr['change'] or 0.0
                    change_pct = usd_inr['change_percent'] or 0.0
                    
                    results.append(CurrencyData(
                        pair=pair,
                        rate=round(current, 2),
                        change=round(change, 2),
                        change_percent=round(change_pct, 2),
                        timestamp=datetime.now()
                    ))
            except Exception as e:
                logger.error(f"Currency rate error for {pair}: {e}")
        
        return results
    
    def analyze_it_impact(self, inr_change_percent: float) -> Dict:
        if inr_change_percent < -2:
            return {
                'sector': 'IT',
                'impact': 'positive',
                'sentiment': 'bullish',
                'description': 'INR depreciation boosts IT revenue in USD terms'
            }
        elif inr_change_percent > 2:
            return {
                'sector': 'IT',
                'impact': 'negative',
                'sentiment': 'bearish',
                'description': 'INR appreciation compresses IT margins'
            }
        
        return {
            'sector': 'IT',
            'impact': 'neutral',
            'sentiment': 'neutral',
            'description': 'Minimal currency impact on IT sector'
        }
    
    def analyze_pharma_impact(self, inr_change_percent: float) -> Dict:
        if inr_change_percent > 2:
            return {
                'sector': 'Pharma',
                'impact': 'positive',
                'sentiment': 'bullish',
                'description': 'INR appreciation reduces raw material costs'
            }
        elif inr_change_percent < -2:
            return {
                'sector': 'Pharma',
                'impact': 'negative',
                'sentiment': 'bearish',
                'description': 'INR depreciation increases input costs'
            }
        
        return {
            'sector': 'Pharma',
            'impact': 'neutral',
            'sentiment': 'neutral',
            'description': 'Minimal currency impact on pharma sector'
        }


class IndiaSpecificService:
    def __init__(self):
        self.election = ElectionMonitor()
        self.monsoon = MonsoonTracker()
        self.budget = BudgetAnalyzer()
        self.fii_dii = FIIDIIFlowTracker()
        self.currency = CurrencyImpactAnalyzer()
    
    async def get_all_data(self) -> Dict:
        fii_data = await self.fii_dii.get_latest_flow()
        currency_data = await self.currency.get_rates()
        
        currency_impact = {}
        if currency_data:
            inr_change = currency_data[0].change_percent
            currency_impact = {
                'it': self.currency.analyze_it_impact(inr_change),
                'pharma': self.currency.analyze_pharma_impact(inr_change)
            }
        
        return {
            'election': {
                'enabled': self.election.enabled,
                'data': []
            },
            'monsoon': {
                'enabled': self.monsoon.enabled,
                'status': 'Data unavailable'
            },
            'budget': {
                'enabled': self.budget.enabled
            },
            'fii_dii': {
                'enabled': self.fii_dii.enabled,
                'data': fii_data
            },
            'currency': {
                'enabled': self.currency.enabled,
                'rates': currency_data,
                'impact': currency_impact
            }
        }


india_service = IndiaSpecificService()
