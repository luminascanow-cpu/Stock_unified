import re
from typing import List, Tuple
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

from ..models.models import NewsArticle, SentimentType
from ..utils.config import config

class SentimentService:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        self.thresholds = config.sentiment.get('thresholds', {})
        self.alert_keywords = config.alerts.get('keywords', [])
        
    def analyze_article(self, article: NewsArticle) -> NewsArticle:
        """Analyze sentiment of a news article"""
        text = article.title + ' ' + article.description
        
        vader_score = self.vader.polarity_scores(text)
        compound_score = vader_score['compound']
        
        blob = TextBlob(text)
        blob_polarity = blob.sentiment.polarity
        
        avg_score = (compound_score + blob_polarity) / 2
        
        article.sentiment_score = avg_score
        article.sentiment_label = self._score_to_sentiment(avg_score)
        article.keywords = self._extract_keywords(text)
        article.is_breaking = self._is_breaking(text)
        
        return article
    
    def _score_to_sentiment(self, score: float) -> SentimentType:
        """Convert numerical score to sentiment type"""
        if score >= self.thresholds.get('strong_bullish', 0.5):
            return SentimentType.STRONG_BULLISH
        elif score >= self.thresholds.get('weak_bullish', 0.1):
            return SentimentType.BULLISH
        elif score <= self.thresholds.get('strong_bearish', -0.5):
            return SentimentType.STRONG_BEARISH
        elif score <= self.thresholds.get('weak_bearish', -0.1):
            return SentimentType.BEARISH
        return SentimentType.NEUTRAL
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        text_lower = text.lower()
        keywords = []
        
        sector_keywords = []
        for sector in config.sectors:
            sector_keywords.extend(sector.get('keywords', []))
        
        for keyword in sector_keywords:
            if keyword.lower() in text_lower:
                keywords.append(keyword)
        
        return list(set(keywords))[:5]
    
    def _is_breaking(self, text: str) -> bool:
        """Check if news is breaking/urgent"""
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in self.alert_keywords)
    
    def calculate_sector_sentiment(self, articles: List[NewsArticle], sector_keywords: List[str]) -> Tuple[float, SentimentType]:
        """Calculate aggregate sentiment for a sector based on related articles"""
        if not articles:
            return 0.0, SentimentType.NEUTRAL
        
        total_score = 0
        count = 0
        
        for article in articles:
            text = (article.title + ' ' + article.description).lower()
            if any(kw.lower() in text for kw in sector_keywords):
                total_score += article.sentiment_score
                count += 1
        
        if count == 0:
            return 0.0, SentimentType.NEUTRAL
        
        avg_score = total_score / count
        return avg_score, self._score_to_sentiment(avg_score)
