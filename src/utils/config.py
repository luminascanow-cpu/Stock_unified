import os
import yaml
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

class Config:
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f)
    
    @property
    def app(self) -> Dict[str, Any]:
        return self._config.get('app', {})
    
    @property
    def news_sources(self) -> Dict[str, Any]:
        return self._config.get('news_sources', {})
    
    @property
    def sentiment(self) -> Dict[str, Any]:
        return self._config.get('sentiment', {})
    
    @property
    def sectors(self) -> List[Dict[str, Any]]:
        return self._config.get('sectors', [])
    
    @property
    def prediction(self) -> Dict[str, Any]:
        return self._config.get('prediction', {})
    
    @property
    def alerts(self) -> Dict[str, Any]:
        return self._config.get('alerts', {})
    
    def get(self, key: str, default=None):
        return self._config.get(key, default)

config = Config()

def get_env(key: str, default=None):
    return os.getenv(key, default)

def get_news_api_key():
    return get_env('NEWS_API_KEY', '')
