"""Sentiment analysis service stub"""
import logging
from models.unified import NewsArticle
from datetime import datetime
logger = logging.getLogger(__name__)

class SentimentService:
    def __init__(self):
        self.healthy = True
    
    async def fetch_news(self):
        """Fetch news articles"""
        logger.info("Fetching news...")
        return []
    
    def is_healthy(self):
        return self.healthy
