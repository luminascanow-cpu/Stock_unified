import re
import logging
from typing import List, Tuple, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

from ..models.models import NewsArticle, SentimentType
from ..utils.config import config
from .news_matching import contains_any, contains_phrase

try:
    from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not installed, using fallback sentiment analysis")

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    from textblob import TextBlob
    FALLBACK_AVAILABLE = True
except ImportError:
    FALLBACK_AVAILABLE = False


class FinBERTService:
    def __init__(self):
        self.sentiment_config = config.sentiment
        self.model_name = self.sentiment_config.get('finbert_model', 'ProsusAI/finbert')
        self.context_aware = self.sentiment_config.get('context_aware', True)
        self.india_context = self.sentiment_config.get('india_context', {})
        self._model = None
        self._tokenizer = None
        self._fallback = None
        
        if TRANSFORMERS_AVAILABLE:
            try:
                self._load_model()
            except Exception as e:
                logger.error(f"Failed to load FinBERT: {e}")
                self._model = None
        else:
            self._init_fallback()
    
    def _load_model(self):
        logger.info(f"Loading FinBERT model: {self.model_name}")
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self._model.eval()
        logger.info("FinBERT model loaded successfully")
    
    def _init_fallback(self):
        if FALLBACK_AVAILABLE:
            self._fallback = FallbackSentiment()
    
    def analyze(self, text: str) -> Tuple[float, str]:
        if self._model is None:
            if self._fallback:
                return self._fallback.analyze(text)
            return 0.0, "neutral"
        
        try:
            inputs = self._tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            with torch.no_grad():
                outputs = self._model(**inputs)
            
            probs = torch.softmax(outputs.logits, dim=1)
            pred_idx = torch.argmax(probs, dim=1).item()
            
            label = self._label_for_index(pred_idx)
            confidence = probs[0][pred_idx].item()
            
            score_map = {'positive': 0.5, 'neutral': 0.0, 'negative': -0.5}
            score = score_map.get(label, 0.0) * confidence
            
            return score, label
        except Exception as e:
            logger.error(f"FinBERT analysis error: {e}")
            if self._fallback:
                return self._fallback.analyze(text)
            return 0.0, "neutral"
    
    def analyze_batch(self, texts: List[str]) -> List[Tuple[float, str]]:
        if not texts:
            return []
        if self._model is None:
            return [self.analyze(text) for text in texts]

        try:
            inputs = self._tokenizer(
                texts,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512,
            )
            with torch.no_grad():
                outputs = self._model(**inputs)
            probabilities = torch.softmax(outputs.logits, dim=1)
            indices = torch.argmax(probabilities, dim=1).tolist()
            score_map = {'positive': 0.5, 'neutral': 0.0, 'negative': -0.5}
            return [
                (
                    score_map.get(self._label_for_index(index), 0.0)
                    * probabilities[row][index].item(),
                    self._label_for_index(index),
                )
                for row, index in enumerate(indices)
            ]
        except Exception as e:
            logger.error(f"FinBERT batch analysis error: {e}")
            return [self.analyze(text) for text in texts]

    def _label_for_index(self, index: int) -> str:
        configured = getattr(getattr(self._model, "config", None), "id2label", {}) or {}
        raw = str(configured.get(index, configured.get(str(index), ""))).lower()
        for label in ("positive", "negative", "neutral"):
            if label in raw:
                return label
        # ProsusAI/finbert's documented class order.
        fallback = ['positive', 'negative', 'neutral']
        return fallback[index] if 0 <= index < len(fallback) else "neutral"


class FallbackSentiment:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer() if FALLBACK_AVAILABLE else None
        self.thresholds = config.sentiment.get('thresholds', {})
    
    def analyze(self, text: str) -> Tuple[float, str]:
        if not self.vader:
            return 0.0, "neutral"
        
        vader_score = self.vader.polarity_scores(text)
        compound = vader_score['compound']
        
        if compound >= self.thresholds.get('strong_bullish', 0.5):
            return compound, "positive"
        elif compound >= self.thresholds.get('weak_bullish', 0.1):
            return compound * 0.6, "positive"
        elif compound <= self.thresholds.get('strong_bearish', -0.5):
            return compound, "negative"
        elif compound <= self.thresholds.get('weak_bearish', -0.1):
            return compound * 0.6, "negative"
        return compound, "neutral"


class IndiaContextAnalyzer:
    def __init__(self):
        self.india_config = config.sentiment.get('india_context', {})
    
    def adjust_sentiment(self, score: float, text: str) -> float:
        text_lower = text.lower()
        
        if self.india_config.get('oil_price_impact', True):
            if 'oil' in text_lower or 'crude' in text_lower:
                if 'price' in text_lower and ('↑' in text or 'up' in text_lower or 'surge' in text_lower or 'high' in text_lower):
                    score = min(score, -0.2)
        
        if self.india_config.get('currency_impact', True):
            if 'rupee' in text_lower or 'inr' in text_lower or 'usd/inr' in text_lower:
                if 'falls' in text_lower or 'weaker' in text_lower or 'record low' in text_lower:
                    score = min(score, -0.3)
                elif 'rises' in text_lower or 'stronger' in text_lower or 'appreciates' in text_lower:
                    score = max(score, 0.3)
        
        return max(-1.0, min(1.0, score))
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        entities = {
            'companies': [],
            'ministers': [],
            'policies': [],
            'sectors': []
        }
        
        company_patterns = ['TCS', 'INFY', 'RELIANCE', 'HDFC', 'SBIN', 'TCS', 'WIPRO', 'TATA', 'ADANI']
        for company in company_patterns:
            if company.lower() in text.lower():
                entities['companies'].append(company)
        
        minister_patterns = ['FM', 'Finance Minister', 'RBI Governor', 'PM', 'Narendra Modi', 'Nirmala', 'Sitharaman']
        for minister in minister_patterns:
            if minister.lower() in text.lower():
                entities['ministers'].append(minister)
        
        policy_patterns = ['budget', 'fiscal', 'monetary policy', 'repo rate', 'GST', 'tax', 'customs duty']
        for policy in policy_patterns:
            if policy.lower() in text.lower():
                entities['policies'].append(policy)
        
        return entities


class AdvancedSentimentService:
    def __init__(self):
        self.sentiment_config = config.sentiment
        self.thresholds = self.sentiment_config.get('thresholds', {})
        self.alert_keywords = config.alerts.get('keywords', [])
        
        self.finbert = FinBERTService() if self.sentiment_config.get('model') == 'finbert' else None
        if not self.finbert:
            self.finbert = FinBERTService()
        
        self.context_analyzer = IndiaContextAnalyzer()
        self.sectors = config.sectors
    
    def analyze_article(self, article: NewsArticle) -> NewsArticle:
        text = article.title + ' ' + article.description
        base_score, label = self.finbert.analyze(text)
        return self._apply_analysis(article, text, base_score)

    def analyze_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        texts = [article.title + ' ' + article.description for article in articles]
        results = []
        for start in range(0, len(texts), 16):
            results.extend(self.finbert.analyze_batch(texts[start:start + 16]))
        return [
            self._apply_analysis(article, text, score)
            for article, text, (score, _label) in zip(articles, texts, results)
        ]

    def _apply_analysis(self, article: NewsArticle, text: str, base_score: float) -> NewsArticle:
        if self.sentiment_config.get('context_aware', True):
            base_score = self.context_analyzer.adjust_sentiment(base_score, text)

        article.sentiment_score = base_score
        article.sentiment_label = self._score_to_sentiment(base_score)
        article.keywords = self._extract_keywords(text)
        article.is_breaking = self._is_breaking(text)
        
        return article
    
    def _score_to_sentiment(self, score: float) -> SentimentType:
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
        text_lower = text.lower()
        keywords = []
        
        sector_keywords = []
        for sector in self.sectors:
            sector_keywords.extend(sector.get('keywords', []))
        
        for keyword in sector_keywords:
            if contains_phrase(text_lower, keyword):
                keywords.append(keyword)
        
        return list(set(keywords))[:5]
    
    def _is_breaking(self, text: str) -> bool:
        return contains_any(text, self.alert_keywords)
    
    def calculate_sector_sentiment(self, articles: List[NewsArticle], sector_keywords: List[str]) -> Tuple[float, SentimentType]:
        if not articles:
            return 0.0, SentimentType.NEUTRAL
        
        total_score = 0
        count = 0
        
        for article in articles:
            text = (article.title + ' ' + article.description).lower()
            if contains_any(text, sector_keywords):
                total_score += article.sentiment_score
                count += 1
        
        if count == 0:
            return 0.0, SentimentType.NEUTRAL
        
        avg_score = total_score / count
        return avg_score, self._score_to_sentiment(avg_score)


advanced_sentiment_service = AdvancedSentimentService()
