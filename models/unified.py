from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum

class SentimentType(Enum):
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"

class ImpactLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class NewsArticle:
    id: str
    title: str
    description: str
    source: str
    url: str
    published_at: datetime
    raw_content: str = ""
    sentiment_score: float = 0.0
    sentiment_label: SentimentType = SentimentType.NEUTRAL
    affected_sectors: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    is_breaking: bool = False

@dataclass
class StockSignal:
    symbol: str
    name: str
    sector: str
    signal: str  # BUY, SELL, STRONG_BUY, STRONG_SELL, NEUTRAL
    confidence: float
    technical_score: float
    sentiment_score: float
    confluence_score: float
    price_info: Optional[Dict] = None
    related_news: List[str] = field(default_factory=list)

@dataclass
class SectorAnalysis:
    name: str
    overall_sentiment: SentimentType
    confidence: float
    affected_stocks: List[StockSignal]
    news_count: int

@dataclass
class Alert:
    id: str
    timestamp: datetime
    title: str
    message: str
    severity: str
    related_sectors: List[str] = field(default_factory=list)
    related_stocks: List[str] = field(default_factory=list)
    is_read: bool = False

@dataclass
class DashboardData:
    latest_news: List[NewsArticle] = field(default_factory=list)
    sector_analysis: List[SectorAnalysis] = field(default_factory=list)
    top_predictions: List[StockSignal] = field(default_factory=list)
    alerts: List[Alert] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
