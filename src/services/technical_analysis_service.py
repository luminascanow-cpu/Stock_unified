"""
Technical Analysis Service
Provides PSAR (Parabolic SAR), Acceleration Factor (AC), and Velocity
calculations for NSE stocks, ported from the standalone app.py tracker.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import yfinance as yf
from pytz import timezone

logger = logging.getLogger(__name__)

# ---- PSAR Configuration ----
INITIAL_AF = 0.02
MAX_AF = 0.2
AF_STEP = 0.02

IST = timezone('Asia/Kolkata')
NIFTY_TICKER = '^NSEI'

# Full NSE ticker universe (140+ stocks from app.py)
ALL_TICKERS = sorted(list(set([
    'BEL.NS','MAZDOCK.NS','HAL.NS','EICHERMOT.NS','TVSMOTOR.NS','HEROMOTOCO.NS',
    'TMPV.NS','TITAN.NS','INDUSINDBK.NS','SAMMAANCAP.NS','IREDA.NS','LXCHEM.NS',
    'PIDILITIND.NS','YASHO.NS','BALAMINES.NS','CLEAN.NS','DEEPAKNTR.NS','DRREDDY.NS',
    'GODREJCP.NS','HINDALCO.NS','HINDPETRO.NS','HINDUNILVR.NS','HINDZINC.NS','ITC.NS',
    'KOTAKBANK.NS','LUPIN.NS','MARUTI.NS','NTPC.NS','POWERGRID.NS','RELIANCE.NS',
    'SBILIFE.NS','SBIN.NS','SUNPHARMA.NS','TATACONSUM.NS','TCS.NS','TATASTEEL.NS',
    'TECHM.NS','ULTRACEMCO.NS','VEDL.NS','WIPRO.NS','YESBANK.NS','TATACHEM.NS',
    'UPL.NS','SRF.NS','TATVA.NS','RALLIS.NS','COALINDIA.NS','TEJASNET.NS','NELCO.NS',
    'LT.NS','ACC.NS','GRASIM.NS','NYKAA.NS','TATAPOWER.NS','SJVN.NS','DMART.NS',
    'BALRAMCHIN.NS','INDHOTEL.NS','STOVEKRAFT.NS','LICI.NS','ANGELONE.NS','IEX.NS',
    'HEG.NS','POLYCAB.NS','HAVELLS.NS','TITAGARH.NS','AFFLE.NS','ZEEL.NS','NMDC.NS',
    'JSWSTEEL.NS','SAIL.NS','INDIGO.NS','CIPLA.NS','GLENMARK.NS','DIVISLAB.NS',
    'INFY.NS','INDIAMART.NS','HAPPSTMNDS.NS','IDEA.NS','TATACOMM.NS','BHARTIARTL.NS',
    'TRIDENT.NS','WAAREEENER.NS','GRANULES.NS','MCX.NS','OLAELEC.NS','INDUSTOWER.NS',
    'GRSE.NS','CDSL.NS','HDFCBANK.NS','FACT.NS','MANAPPURAM.NS','PAYTM.NS','NCC.NS',
    'TRENT.NS','PNB.NS','GMRAIRPORT.NS','BDL.NS','KAYNES.NS','BSE.NS','NBCC.NS',
    'IRCTC.NS','RVNL.NS','CAMS.NS','GRAPHITE.NS','IDEAFORGE.NS','BAJAJHFL.NS',
    'ICICIBANK.NS','AXISBANK.NS','BAJFINANCE.NS','BAJAJFINSV.NS','ONGC.NS','BPCL.NS',
    'GAIL.NS','ADANIPORTS.NS','ADANIENT.NS','ADANIGREEN.NS','ADANIPOWER.NS',
    'AMBUJACEM.NS','DABUR.NS','BRITANNIA.NS','NESTLEIND.NS','COLPAL.NS','MARICO.NS',
    'SIEMENS.NS','ABB.NS','BHEL.NS','VOLTAS.NS','CUMMINSIND.NS','M&M.NS',
    'ASHOKLEY.NS','TATAMOTORS.NS','BAJAJ-AUTO.NS','APOLLOTYRE.NS','MRF.NS',
    'BANKBARODA.NS','CANBK.NS','UNIONBANK.NS','IOB.NS','INDIANB.NS',
    'FEDERALBNK.NS','RBLBANK.NS','AUBANK.NS','BANDHANBNK.NS','IDFCFIRSTB.NS',
    'SOUTHBANK.NS','KARURVYSYA.NS','DCBBANK.NS','IOC.NS','HINDCOPPER.NS'
])))


@dataclass
class TechnicalData:
    """Technical indicators for a single stock."""
    symbol: str          # without .NS
    ltp: float = 0.0
    change_percent: float = 0.0
    velocity: float = 0.0
    ac: float = 0.0
    psar_af: float = INITIAL_AF
    psar_trend: str = 'neutral'   # 'bull' | 'bear' | 'neutral'
    signal_strength: str = 'NEUTRAL'  # STRONG_BUY | BUY | NEUTRAL | SELL | STRONG_SELL
    high_52w: float = 0.0
    distance_52w: Optional[float] = None
    volume: str = '-'
    reversal_count: int = 0
    af_increase_rate: float = 0.0


# ---- Pure calculation helpers (same logic as app.py) ----

def _safe_float(value, default=0.0) -> float:
    try:
        return float(value) if pd.notna(value) else default
    except (ValueError, TypeError):
        return default


def _format_volume(num) -> str:
    if num is None or (isinstance(num, float) and np.isnan(num)):
        return '-'
    try:
        num = float(num)
        if num >= 1e9:
            return f"{num/1e9:.1f}B"
        elif num >= 1e6:
            return f"{num/1e6:.1f}M"
        elif num >= 1e3:
            return f"{num/1e3:.1f}K"
        return str(int(num))
    except Exception:
        return '-'


def calculate_psar_full(
    df: pd.DataFrame,
    af: float = INITIAL_AF,
    max_af: float = MAX_AF,
    step: float = AF_STEP
) -> Tuple[List, List, List, List]:
    length = len(df)
    if length < 2:
        return [None] * length, [af] * length, ['neutral'] * length, []

    high = df['High'].values
    low = df['Low'].values
    close = df['Close'].values

    psar = [0.0] * length
    af_values = [0.0] * length
    trend = [''] * length
    reversals = []

    bull = True
    af_val = af
    ep = high[0]
    psar[0] = low[0]
    af_values[0] = af
    trend[0] = 'bull' if (len(close) > 1 and close[0] > close[1]) else 'bear'

    for i in range(1, length):
        psar[i] = psar[i - 1] + af_val * (ep - psar[i - 1])

        if bull:
            if i > 1:
                psar[i] = min(psar[i], low[i - 1], low[i - 2])
        else:
            if i > 1:
                psar[i] = max(psar[i], high[i - 1], high[i - 2])

        if bull:
            if low[i] < psar[i]:
                bull = False
                psar[i] = ep
                ep = low[i]
                af_val = af
                trend[i] = 'bear'
                reversals.append({'index': i, 'type': 'BULL_TO_BEAR', 'price': low[i]})
            else:
                if high[i] > ep:
                    ep = high[i]
                    af_val = min(af_val + step, max_af)
                trend[i] = 'bull'
        else:
            if high[i] > psar[i]:
                bull = True
                psar[i] = ep
                ep = high[i]
                af_val = af
                trend[i] = 'bull'
                reversals.append({'index': i, 'type': 'BEAR_TO_BULL', 'price': high[i]})
            else:
                if low[i] < ep:
                    ep = low[i]
                    af_val = min(af_val + step, max_af)
                trend[i] = 'bear'

        af_values[i] = af_val

    return psar, af_values, trend, reversals


def calculate_ac(df: pd.DataFrame) -> Tuple[pd.DataFrame, List]:
    """Compute AC Oscillator + Velocity + PSAR on a price dataframe."""
    d = df.copy()
    d['Midpoint'] = (d['High'] + d['Low']) / 2
    d['SMA_5'] = d['Midpoint'].rolling(window=5).mean()
    d['Velocity'] = d['SMA_5'].diff()
    d['SMA_34'] = d['Midpoint'].rolling(window=34).mean()
    d['AO'] = d['SMA_5'] - d['SMA_34']
    d['Standard_AC'] = d['AO'] - d['AO'].rolling(window=5).mean()

    psar_values, af_values, trend, reversals = calculate_psar_full(d)
    d['PSAR'] = psar_values
    d['PSAR_AF'] = af_values
    d['PSAR_Trend'] = trend

    return d, reversals


def _analyze_single(ticker: str, ticker_data: pd.DataFrame, high_52w: float = 0.0) -> Optional[TechnicalData]:
    """Analyze a single ticker dataframe → TechnicalData."""
    try:
        if len(ticker_data) < 10:
            return None

        current_price = _safe_float(ticker_data['Close'].iloc[-1])
        previous_index = max(0, len(ticker_data) - 13)
        previous_price = _safe_float(ticker_data['Close'].iloc[previous_index])
        change_percent = ((current_price - previous_price) / previous_price) * 100 if previous_price > 0 else 0.0
        analyzed, reversals = calculate_ac(ticker_data)

        velocity_val = _safe_float(analyzed['Velocity'].iloc[-1])
        ac_val = _safe_float(analyzed['Standard_AC'].iloc[-1])
        psar_af = _safe_float(analyzed['PSAR_AF'].iloc[-1])
        current_trend = str(analyzed['PSAR_Trend'].iloc[-1])

        af_vals = analyzed['PSAR_AF'].dropna().values
        af_increase_count = sum(1 for i in range(1, len(af_vals)) if af_vals[i] > af_vals[i - 1])
        af_increase_rate = (af_increase_count / len(af_vals)) * 100 if len(af_vals) > 1 else 0

        dist_52w = ((current_price - high_52w) / high_52w) * 100 if high_52w > 0 else None
        volume = _safe_float(ticker_data['Volume'].iloc[-1]) if 'Volume' in ticker_data.columns else 0.0

        signal = 'NEUTRAL'
        if ac_val > 0.002 and velocity_val > 0 and current_trend == 'bull':
            signal = 'STRONG_BUY'
        elif ac_val < -0.002 and velocity_val < 0 and current_trend == 'bear':
            signal = 'STRONG_SELL'
        elif ac_val > 0 and current_trend == 'bull':
            signal = 'BUY'
        elif ac_val < 0 and current_trend == 'bear':
            signal = 'SELL'

        clean_symbol = ticker.replace('.NS', '')
        return TechnicalData(
            symbol=clean_symbol,
            ltp=round(current_price, 2),
            change_percent=round(change_percent, 2),
            velocity=round(velocity_val, 4),
            ac=round(ac_val, 4),
            psar_af=round(psar_af, 2),
            psar_trend=current_trend,
            signal_strength=signal,
            high_52w=round(high_52w, 2) if high_52w else 0.0,
            distance_52w=round(dist_52w, 2) if dist_52w is not None else None,
            volume=_format_volume(volume),
            reversal_count=len(reversals),
            af_increase_rate=round(af_increase_rate, 2),
        )
    except Exception as e:
        logger.debug(f"Error analyzing {ticker}: {e}")
        return None


def _extract_ticker_df(data: pd.DataFrame, ticker: str) -> Optional[pd.DataFrame]:
    """Extract one ticker frame from yfinance single or multi-ticker downloads."""
    try:
        if data is None or data.empty:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            level_0 = data.columns.get_level_values(0)
            level_1 = data.columns.get_level_values(1)
            if ticker in level_0:
                return data.xs(ticker, axis=1, level=0).dropna(how='all')
            if ticker in level_1:
                return data.xs(ticker, axis=1, level=1).dropna(how='all')
            return None
        return data.dropna(how='all')
    except Exception:
        return None


def _chunks(items: List[str], size: int) -> List[List[str]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


# ---- Async Service ----

class TechnicalAnalysisService:
    """Async service for fetching and computing PSAR/AC technical data."""

    def __init__(self):
        self._cache: Dict[str, TechnicalData] = {}
        self._highs_52w: Dict[str, float] = {}
        self._last_fetch: Optional[float] = None
        self._fetching = False
        self._macro_cache: Dict[str, Dict] = {}
        self._macro_cache_ts: Dict[str, float] = {}

        logger.info("Technical Analysis Service configured with Yahoo Finance")

    @property
    def is_broker_configured(self) -> bool:
        return True

    def get_cached(self) -> Dict[str, TechnicalData]:
        return dict(self._cache)

    async def fetch_52w_highs(self) -> Dict[str, float]:
        """Fetch 52-week highs for all tickers through Yahoo Finance."""
        logger.info("Fetching 52-week highs for all tickers through Yahoo Finance...")
        loop = asyncio.get_event_loop()

        def _download_yahoo():
            highs: Dict[str, float] = {}
            for batch in _chunks(ALL_TICKERS, 40):
                try:
                    data = yf.download(
                        batch,
                        period="1y",
                        interval="1d",
                        progress=False,
                        group_by='ticker',
                        threads=True,
                        timeout=60,
                    )
                except Exception as e:
                    logger.error(f"Yahoo 52w batch fetch failed: {e}")
                    data = pd.DataFrame()

                for ticker in batch:
                    t_df = _extract_ticker_df(data, ticker)
                    if t_df is not None and not t_df.empty and 'High' in t_df.columns:
                        highs[ticker] = _safe_float(t_df['High'].max())
                    else:
                        highs[ticker] = 0.0
            return highs

        self._highs_52w = await loop.run_in_executor(None, _download_yahoo)
        logger.info(f"52W highs fetched for {len(self._highs_52w)} tickers via Yahoo Finance.")
        return self._highs_52w

    async def fetch_all(self) -> Dict[str, TechnicalData]:
        """Fetch fresh intraday data and compute technical indicators through Yahoo Finance."""
        if self._fetching:
            return self._cache

        self._fetching = True
        start = time.time()
        loop = asyncio.get_event_loop()

        def _download_yahoo():
            results: Dict[str, TechnicalData] = {}
            for batch in _chunks(ALL_TICKERS, 40):
                try:
                    data = yf.download(
                        batch,
                        period="5d",
                        interval="5m",
                        prepost=False,
                        progress=False,
                        group_by='ticker',
                        threads=True,
                        timeout=60,
                    )
                except Exception as e:
                    logger.error(f"Yahoo intraday batch fetch failed: {e}")
                    data = pd.DataFrame()

                for ticker in batch:
                    t_df = _extract_ticker_df(data, ticker)
                    if t_df is None or t_df.empty:
                        continue
                    tdata = _analyze_single(ticker, t_df, self._highs_52w.get(ticker, 0.0))
                    if tdata:
                        results[tdata.symbol] = tdata
            return results

        try:
            if not self._highs_52w:
                await self.fetch_52w_highs()
            results = await loop.run_in_executor(None, _download_yahoo)
            self._cache = results
            self._last_fetch = time.time()
            logger.info(f"Technical analysis via Yahoo Finance complete: {len(results)} stocks in {time.time()-start:.1f}s")
            return results
        except Exception as e:
            logger.error(f"Technical fetch_all error: {e}")
            return self._cache
        finally:
            self._fetching = False

    async def get_nifty(self) -> Optional[Dict]:
        """Fetch NIFTY 50 technical data through Yahoo Finance."""
        loop = asyncio.get_event_loop()

        def _nifty():
            try:
                data = yf.download(
                    NIFTY_TICKER,
                    period='5d',
                    interval='5m',
                    progress=False,
                    timeout=30,
                )
                df = _extract_ticker_df(data, NIFTY_TICKER)
                if df is None or df.empty or len(df) < 10:
                    return None

                analyzed, reversals = calculate_ac(df)
                analyzed['Close'] = analyzed['Close'].ffill()

                return {
                    'ltp': round(_safe_float(analyzed['Close'].iloc[-1]), 2),
                    'velocity': round(_safe_float(analyzed['Velocity'].iloc[-1]), 4),
                    'ac': round(_safe_float(analyzed['Standard_AC'].iloc[-1]), 4),
                    'psar_af': round(_safe_float(analyzed['PSAR_AF'].iloc[-1]), 2),
                    'trend': str(analyzed['PSAR_Trend'].iloc[-1]).upper(),
                    'reversal_count': len(reversals),
                }
            except Exception as e:
                logger.error(f"Nifty tech error: {e}")
                return None

        return await loop.run_in_executor(None, _nifty)

    async def get_crude_ltp(self) -> Dict:
        cached = self._macro_cache.get('crude')
        cached_at = self._macro_cache_ts.get('crude', 0)
        if cached and time.time() - cached_at < 60:
            return cached

        quote = {
            'symbol': 'CL=F',
            'label': 'WTI Crude',
            'value': None,
            'change': None,
            'change_percent': None,
            'currency': 'USD',
            'source': 'Yahoo Finance',
            'timestamp': datetime.now().isoformat()
        }

        loop = asyncio.get_event_loop()

        def _fetch():
            try:
                data = yf.download(
                    'CL=F',
                    period='2d',
                    interval='5m',
                    progress=False,
                    timeout=20,
                )
                df = _extract_ticker_df(data, 'CL=F')
                if df is None or df.empty or 'Close' not in df.columns:
                    return quote
                close = df['Close'].dropna()
                if close.empty:
                    return quote
                latest = _safe_float(close.iloc[-1])
                previous = _safe_float(close.iloc[-2]) if len(close) > 1 else None
                change = latest - previous if previous else None
                change_percent = (change / previous) * 100 if previous else None
                return {
                    'symbol': 'CL=F',
                    'label': 'WTI Crude',
                    'value': round(latest, 2),
                    'change': round(change, 2) if change is not None else None,
                    'change_percent': round(change_percent, 3) if change_percent is not None else None,
                    'currency': 'USD',
                    'source': 'Yahoo Finance',
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Yahoo crude fetch failed: {e}")
                return quote

        result = await loop.run_in_executor(None, _fetch)
        self._macro_cache['crude'] = result
        self._macro_cache_ts['crude'] = time.time()
        return result

    def compute_market_summary(self) -> Dict:
        """Compute summary stats over current cached technical data."""
        data = list(self._cache.values())
        if not data:
            return {}
        bullish = sum(1 for d in data if d.psar_trend == 'bull')
        bearish = sum(1 for d in data if d.psar_trend == 'bear')
        avg_af = sum(d.psar_af for d in data) / len(data)
        return {
            'total_stocks': len(data),
            'bullish': bullish,
            'bearish': bearish,
            'neutral': len(data) - bullish - bearish,
            'avg_af': round(avg_af, 2),
            'strong_buy': sum(1 for d in data if d.signal_strength == 'STRONG_BUY'),
            'strong_sell': sum(1 for d in data if d.signal_strength == 'STRONG_SELL'),
        }


# Singleton
technical_service = TechnicalAnalysisService()
