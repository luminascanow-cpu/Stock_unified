import hashlib
import feedparser
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import asyncio
import aiohttp

from ..models.models import NewsArticle
from ..utils.config import config, get_env
from .news_matching import canonical_story_key

logger = logging.getLogger(__name__)

class NewsService:
    def __init__(self):
        self.rss_feeds = config.news_sources.get('rss_feeds', [])
        self.news_api_key = get_env('NEWS_API_KEY', '')
        self._feed_cache: Dict[str, List[NewsArticle]] = {}
        self._feed_validators: Dict[str, Dict[str, str]] = {}
        self._last_successful: List[NewsArticle] = []
        self._fetch_task: Optional[asyncio.Task] = None
        self.last_fetch_status = {
            'status': 'not_started',
            'fresh_sources': 0,
            'cached_sources': 0,
            'failed_sources': 0,
            'updated_at': None,
        }

    async def fetch_all_news(self) -> List[NewsArticle]:
        """Fetch and deduplicate news with a single in-flight provider request."""
        if self._fetch_task and not self._fetch_task.done():
            return await asyncio.shield(self._fetch_task)
        self._fetch_task = asyncio.create_task(self._fetch_all_news_once())
        try:
            return await asyncio.shield(self._fetch_task)
        finally:
            if self._fetch_task and self._fetch_task.done():
                self._fetch_task = None

    async def _fetch_all_news_once(self) -> List[NewsArticle]:
        timeout = aiohttp.ClientTimeout(total=12, connect=4, sock_read=8)
        connector = aiohttp.TCPConnector(limit=max(4, min(12, len(self.rss_feeds) * 2)))
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            results = await asyncio.gather(
                *(self.fetch_rss_feed(feed, session) for feed in self.rss_feeds),
                return_exceptions=True,
            )

        all_articles: List[NewsArticle] = []
        fresh_sources = 0
        cached_sources = 0
        failed_sources = 0
        for result in results:
            if isinstance(result, Exception):
                failed_sources += 1
                continue
            articles, state = result
            all_articles.extend(articles)
            if state == 'fresh':
                fresh_sources += 1
            elif state == 'cached':
                cached_sources += 1
            elif state == 'stale':
                cached_sources += 1
                failed_sources += 1
            else:
                failed_sources += 1

        deduplicated: Dict[str, NewsArticle] = {}
        for article in all_articles:
            key = canonical_story_key(article.title, article.url)
            current = deduplicated.get(key)
            if current is None or article.published_at > current.published_at:
                deduplicated[key] = article

        articles = sorted(deduplicated.values(), key=lambda item: item.published_at, reverse=True)[:50]
        if articles:
            self._last_successful = articles
        elif self._last_successful:
            articles = list(self._last_successful)

        status = 'fresh' if fresh_sources else ('cached' if articles else 'unavailable')
        if failed_sources and articles:
            status = 'partial'
        self.last_fetch_status = {
            'status': status,
            'fresh_sources': fresh_sources,
            'cached_sources': cached_sources,
            'failed_sources': failed_sources,
            'updated_at': datetime.utcnow().isoformat() + 'Z',
        }
        return articles
    
    async def fetch_rss_feed(
        self,
        feed_info: dict,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Tuple[List[NewsArticle], str]:
        """Fetch and parse RSS feed"""
        articles: List[NewsArticle] = []
        feed_url = feed_info['url']
        own_session = session is None
        if own_session:
            session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=12))
        try:
            validators = self._feed_validators.get(feed_url, {})
            headers = {'Accept': 'application/rss+xml, application/xml, text/xml'}
            if validators.get('etag'):
                headers['If-None-Match'] = validators['etag']
            if validators.get('last_modified'):
                headers['If-Modified-Since'] = validators['last_modified']

            async with session.get(feed_url, headers=headers) as response:
                if response.status == 304:
                    return list(self._feed_cache.get(feed_url, [])), 'cached'
                response.raise_for_status()
                content = await response.text()
                feed = feedparser.parse(content)
                for entry in feed.entries[:15]:
                    article = self._parse_entry(entry, feed_info['name'])
                    if article:
                        articles.append(article)
                self._feed_cache[feed_url] = articles
                self._feed_validators[feed_url] = {
                    'etag': response.headers.get('ETag', ''),
                    'last_modified': response.headers.get('Last-Modified', ''),
                }
                return articles, 'fresh'
        except Exception as e:
            logger.warning("News feed unavailable (%s): %s", feed_info.get('name', feed_url), e)
            cached = self._feed_cache.get(feed_url, [])
            return list(cached), 'stale' if cached else 'failed'
        finally:
            if own_session and session is not None:
                await session.close()
    
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
                published_at = datetime.utcnow()
            
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
