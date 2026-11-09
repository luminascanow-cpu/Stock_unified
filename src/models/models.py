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
class StockPrediction:
    symbol: str
    name: str
    sector: str
    prediction: SentimentType
    confidence: float
    impact_level: ImpactLevel
    related_news: List[str] = field(default_factory=list)
    price_info: Optional[Dict] = None

    # --- Technical fields (from PSAR/AC tracker) ---
    ltp: Optional[float] = None
    change_percent: Optional[float] = None
    velocity: Optional[float] = None
    ac: Optional[float] = None
    psar_af: Optional[float] = None
    psar_trend: Optional[str] = None          # "bull" | "bear" | "neutral"
    signal_strength: Optional[str] = None     # STRONG_BUY | BUY | NEUTRAL | SELL | STRONG_SELL
    high_52w: Optional[float] = None
    distance_52w: Optional[float] = None
    reversal_count: int = 0
    af_increase_rate: float = 0.0

    # --- Confluence (technical + sentiment fusion) ---
    confluence_score: Optional[float] = None  # -1.0 → +1.0
    confluence_label: Optional[str] = None    # "Strong Confluence" | "Aligned" | "Divergence" | "Conflicting"


@dataclass
class SectorAnalysis:
    name: str
    overall_sentiment: SentimentType
    confidence: float
    affected_stocks: List[StockPrediction]
    news_count: int
    avg_ac: float = 0.0          # average Bill Williams AC across sector stocks
    tech_signal: str = "NEUTRAL" # dominant technical signal for sector
    top_url: Optional[str] = None


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
    url: Optional[str] = None


@dataclass
class DashboardData:
    latest_news: List[NewsArticle] = field(default_factory=list)
    sector_analysis: List[SectorAnalysis] = field(default_factory=list)
    top_predictions: List[StockPrediction] = field(default_factory=list)
    alerts: List[Alert] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    nifty: Optional[Dict] = None
    market_summary: Optional[Dict] = None
    technical_updated: Optional[str] = None
    upcoming_events: List[Dict] = field(default_factory=list)
