import hashlib
import feedparser
import requests
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup
import asyncio
import aiohttp

from ..models.models import NewsArticle, SentimentType
from ..utils.config import config, get_env

class NewsService:
    def __init__(self):
        self.rss_feeds = config.news_sources.get('rss_feeds', [])
        self.news_api_key = get_env('NEWS_API_KEY', '')
        
    async def fetch_all_news(self) -> List[NewsArticle]:
        """Fetch news from all configured sources"""
        all_articles = []
        
        rss_tasks = [self.fetch_rss_feed(feed) for feed in self.rss_feeds]
        rss_results = await asyncio.gather(*rss_tasks, return_exceptions=True)
        
        for result in rss_results:
            if isinstance(result, list):
                all_articles.extend(result)
        
        if not all_articles:
            all_articles = self._get_sample_news()
        
        all_articles.sort(key=lambda x: x.published_at, reverse=True)
        return all_articles[:50]
    
    def _get_sample_news(self) -> List[NewsArticle]:
        """Return sample news when APIs are unavailable"""
        sample_news = [
            NewsArticle(
                id="1",
                title="India announces new defense procurement policy amid border tensions",
                description="The Indian government has unveiled a new defense procurement policy aimed at boosting domestic manufacturing and reducing reliance on foreign arms.",
                source="Reuters India",
                url="https://finance.yahoo.com",
                published_at=datetime.now(),
                raw_content="India announces new defense procurement policy amid border tensions",
                sentiment_score=0.3,
                sentiment_label=SentimentType.BULLISH,
                affected_sectors=["Defense"]
            ),
            NewsArticle(
                id="2",
                title="Oil prices surge as OPEC+ extends production cuts",
                description="Crude oil prices jumped 3% after OPEC+ announced an extension of voluntary production cuts into the next quarter.",
                source="Business Standard",
                url="https://finance.yahoo.com",
                published_at=datetime.now(),
                raw_content="Oil prices surge as OPEC+ extends production cuts",
                sentiment_score=-0.2,
                sentiment_label=SentimentType.BEARISH,
                affected_sectors=["Energy"]
            ),
            NewsArticle(
                id="3",
                title="IT sector faces headwinds as US visa policies tighten",
                description="Indian IT companies may face challenges as the US considers new visa regulations affecting tech workers.",
                source="Economic Times",
                url="https://finance.yahoo.com",
                published_at=datetime.now(),
                raw_content="IT sector faces headwinds as US visa policies tighten",
                sentiment_score=-0.4,
                sentiment_label=SentimentType.BEARISH,
                affected_sectors=["IT"]
            ),
            NewsArticle(
                id="4",
                title="RBI keeps repo rate unchanged, markets react positively",
                description="The Reserve Bank of India maintained the repo rate at current levels, boosting banking and financial services stocks.",
                source="MoneyControl",
                url="https://finance.yahoo.com",
                published_at=datetime.now(),
                raw_content="RBI keeps repo rate unchanged, markets react positively",
                sentiment_score=0.5,
                sentiment_label=SentimentType.STRONG_BULLISH,
                affected_sectors=["Banking"]
            ),
            NewsArticle(
                id="5",
                title="Pharma companies gain on expectations of strong Q4 earnings",
                description="Indian pharmaceutical stocks rallied on expectations of strong quarterly results driven by US generic drug sales.",
                source="Business Standard",
                url="https://finance.yahoo.com",
                published_at=datetime.now(),
                raw_content="Pharma companies gain on expectations of strong Q4 earnings",
                sentiment_score=0.4,
                sentiment_label=SentimentType.BULLISH,
                affected_sectors=["Pharma"]
            ),
            NewsArticle(
                id="6",
                title="Auto manufacturers report strong sales in February",
                description="Major automobile companies reported robust sales numbers for February, driven by festive season demand and new model launches.",
                source="The Hindu",
                url="https://finance.yahoo.com",
                published_at=datetime.now(),
                raw_content="Auto manufacturers report strong sales in February",
                sentiment_score=0.6,
                sentiment_label=SentimentType.STRONG_BULLISH,
                affected_sectors=["Auto"]
            ),
        ]
        return sample_news
    
    async def fetch_rss_feed(self, feed_info: dict) -> List[NewsArticle]:
        """Fetch and parse RSS feed"""
        articles = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(feed_info['url'], timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        for entry in feed.entries[:10]:
                            article = self._parse_entry(entry, feed_info['name'])
                            if article:
                                articles.append(article)
        except Exception as e:
            pass
        
        return articles
    
    def _parse_entry(self, entry, source: str) -> Optional[NewsArticle]:
        """Parse RSS entry into NewsArticle"""
        try:
            title = entry.get('title', '')
            if not title:
                return None
            
            article_id = hashlib.md5(title.encode()).hexdigest()
            
            published_str = entry.get('published', '')
            try:
                published_at = datetime(*entry.published_parsed[:6])
            except:
                published_at = datetime.now()
            
            description = entry.get('summary', '')
            url = entry.get('link', '')
            
            return NewsArticle(
                id=article_id,
                title=title,
                description=description[:200] if description else '',
                source=source,
                url=url,
                published_at=published_at,
                raw_content=title + ' ' + description
            )
        except Exception as e:
            print(f"Error parsing entry: {e}")
            return None
    
    async def fetch_with_newsapi(self, query: str = "India") -> List[NewsArticle]:
        """Fetch news from NewsAPI"""
        if not self.news_api_key or self.news_api_key == 'your_newsapi_key_here':
            return []
        
        articles = []
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'language': 'en',
                'sortBy': 'publishedAt',
                'apiKey': self.news_api_key,
                'pageSize': 20
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        for item in data.get('articles', []):
                            article = NewsArticle(
                                id=hashlib.md5(item['url'].encode()).hexdigest(),
                                title=item.get('title', ''),
                                description=item.get('description', '')[:200] if item.get('description') else '',
                                source=item.get('source', {}).get('name', ''),
                                url=item.get('url', ''),
                                published_at=datetime.fromisoformat(item['publishedAt'].replace('Z', '+00:00')),
                                raw_content=item.get('title', '') + ' ' + (item.get('description') or '')
                            )
                            articles.append(article)
        except Exception as e:
            print(f"NewsAPI error: {e}")
        
        return articles
