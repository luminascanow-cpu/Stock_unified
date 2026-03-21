"""Confluence engine - merges technical + sentiment signals"""
import logging
from typing import List, Dict, Optional
from models.unified import StockSignal, SectorAnalysis, Alert
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfluenceEngine:
    def __init__(self):
        self._signals: List[StockSignal] = []
        self._alerts: List[Alert] = []
        self._sectors: Dict[str, SectorAnalysis] = {}
    
    def generate_signals(self, tech_data: List[Dict], news_data: List = None):
        """Generate confluence signals from technical + sentiment data"""
        logger.info(f"Generating confluence signals from {len(tech_data)} technical records...")
        
        self._signals = []
        
        for tech in tech_data:
            # Calculate confluence score (for now, just technical since sentiment is stub)
            technical_score = self._calculate_technical_score(tech)
            sentiment_score = 0.0  # Placeholder for sentiment
            
            confluence_score = (technical_score * 0.7) + (sentiment_score * 0.3)
            
            signal = StockSignal(
                symbol=tech['symbol'],
                name=tech['symbol'].split('.')[0],  # Remove .NS suffix
                sector="Unknown",  # TODO: Add sector mapping
                signal=tech.get('signal', 'NEUTRAL'),
                confidence=abs(confluence_score),
                technical_score=technical_score,
                sentiment_score=sentiment_score,
                confluence_score=confluence_score,
                price_info={
                    'ltp': tech.get('ltp'),
                    'high_52w': tech.get('high_52w'),
                    'distance_52w': tech.get('distance_52w')
                },
                related_news=[]
            )
            self._signals.append(signal)
        
        logger.info(f"Generated {len(self._signals)} confluence signals")
        return self._signals
    
    def _calculate_technical_score(self, tech: Dict) -> float:
        """Calculate technical score from indicators"""
        score = 0.0
        
        # PSAR trend weight
        if tech.get('psar_trend') == 'bull':
            score += 0.3
        elif tech.get('psar_trend') == 'bear':
            score -= 0.3
        
        # Acceleration Factor weight
        ac = tech.get('ac', 0)
        if ac > 0.002:
            score += 0.3
        elif ac < -0.002:
            score -= 0.3
        
        # Signal strength weight
        signal = tech.get('signal', 'NEUTRAL')
        if signal == 'STRONG_BUY':
            score += 0.4
        elif signal == 'STRONG_SELL':
            score -= 0.4
        elif signal == 'BUY':
            score += 0.2
        elif signal == 'SELL':
            score -= 0.2
        
        return max(-1.0, min(1.0, score))
    
    def get_all_signals(self) -> List[Dict]:
        """Get all signals as dicts"""
        return [self._signal_to_dict(s) for s in self._signals]
    
    def _signal_to_dict(self, signal: StockSignal) -> Dict:
        return {
            'symbol': signal.symbol,
            'name': signal.name,
            'sector': signal.sector,
            'signal': signal.signal,
            'confidence': signal.confidence,
            'technical_score': signal.technical_score,
            'sentiment_score': signal.sentiment_score,
            'confluence_score': signal.confluence_score,
            'price_info': signal.price_info,
            'related_news': signal.related_news
        }
    
    def get_signal(self, symbol: str) -> Optional[Dict]:
        """Get single signal by symbol"""
        for s in self._signals:
            if s.symbol.upper() == symbol.upper():
                return self._signal_to_dict(s)
        return None
    
    def get_sector_analysis(self) -> List[Dict]:
        """Get sector analysis"""
        return list(self._sectors.values())
    
    def get_alerts(self) -> List[Dict]:
        """Get active alerts"""
        return self._alerts
    
    def calculate_confluence(self, symbol: str) -> Dict:
        """Get confluence score for a stock"""
        signal = self.get_signal(symbol)
        if signal:
            return {
                'symbol': symbol,
                'confluence_score': signal['confluence_score'],
                'technical_score': signal['technical_score'],
                'sentiment_score': signal['sentiment_score']
            }
        return {'symbol': symbol, 'score': 0.0}
