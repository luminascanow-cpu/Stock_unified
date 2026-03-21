"""
Technical Analysis Service
Provides PSAR (Parabolic SAR), Acceleration Factor (AC), and Velocity
calculations for NSE stocks, ported from the standalone app.py tracker.
"""

import asyncio
import logging
import time
from datetime import datetime
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
    'BEL.NS', 'MAZDOCK.NS', 'HAL.NS', 'EICHERMOT.NS', 'TVSMOTOR.NS', 'HEROMOTOCO.NS',
    'TITAN.NS', 'INDUSINDBK.NS', 'IREDA.NS', 'PIDILITIND.NS', 'BALAMINES.NS',
    'DEEPAKNTR.NS', 'DRREDDY.NS', 'GODREJCP.NS', 'HINDALCO.NS', 'HINDPETRO.NS',
    'HINDUNILVR.NS', 'HINDZINC.NS', 'ITC.NS', 'KOTAKBANK.NS', 'LUPIN.NS',
    'MARUTI.NS', 'NTPC.NS', 'POWERGRID.NS', 'RELIANCE.NS', 'SBILIFE.NS', 'SBIN.NS',
    'SUNPHARMA.NS', 'TATACONSUM.NS', 'TCS.NS', 'TATASTEEL.NS', 'TECHM.NS',
    'ULTRACEMCO.NS', 'VEDL.NS', 'WIPRO.NS', 'YESBANK.NS', 'TATACHEM.NS',
    'UPL.NS', 'SRF.NS', 'RALLIS.NS', 'COALINDIA.NS', 'TEJASNET.NS', 'NELCO.NS',
    'LT.NS', 'ACC.NS', 'GRASIM.NS', 'TATAPOWER.NS', 'SJVN.NS', 'DMART.NS',
    'BALRAMCHIN.NS', 'INDHOTEL.NS', 'LICI.NS', 'ANGELONE.NS', 'IEX.NS',
    'HEG.NS', 'POLYCAB.NS', 'HAVELLS.NS', 'TITAGARH.NS', 'AFFLE.NS', 'NMDC.NS',
    'JSWSTEEL.NS', 'SAIL.NS', 'INDIGO.NS', 'CIPLA.NS', 'GLENMARK.NS', 'DIVISLAB.NS',
    'INFY.NS', 'INDIAMART.NS', 'TATACOMM.NS', 'BHARTIARTL.NS',
    'TRIDENT.NS', 'WAAREEENER.NS', 'GRANULES.NS', 'MCX.NS', 'INDUSTOWER.NS',
    'GRSE.NS', 'CDSL.NS', 'HDFCBANK.NS', 'MANAPPURAM.NS', 'NCC.NS',
    'TRENT.NS', 'PNB.NS', 'GMRAIRPORT.NS', 'BDL.NS', 'KAYNES.NS', 'BSE.NS',
    'IRCTC.NS', 'RVNL.NS', 'CAMS.NS', 'ICICIBANK.NS', 'AXISBANK.NS',
    'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'ONGC.NS', 'BPCL.NS', 'GAIL.NS',
    'ADANIPORTS.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPOWER.NS',
    'AMBUJACEM.NS', 'DABUR.NS', 'BRITANNIA.NS', 'NESTLEIND.NS', 'COLPAL.NS',
    'MARICO.NS', 'SIEMENS.NS', 'ABB.NS', 'BHEL.NS', 'VOLTAS.NS', 'CUMMINSIND.NS',
    'M&M.NS', 'ASHOKLEY.NS', 'BAJAJ-AUTO.NS', 'APOLLOTYRE.NS', 'MRF.NS',
    'BANKBARODA.NS', 'CANBK.NS', 'UNIONBANK.NS', 'INDIANB.NS',
    'FEDERALBNK.NS', 'RBLBANK.NS', 'AUBANK.NS', 'BANDHANBNK.NS', 'IDFCFIRSTB.NS',
    'KARURVYSYA.NS', 'IOC.NS', 'HINDCOPPER.NS', 'MIDHANI.NS', 'PARAS.NS',
])))


@dataclass
class TechnicalData:
    """Technical indicators for a single stock."""
    symbol: str          # without .NS
    ltp: float = 0.0
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
    """Extract single ticker dataframe from a multi-ticker yfinance bulk download."""
    try:
        if isinstance(data.columns, pd.MultiIndex):
            lvl0 = data.columns.get_level_values(0)
            lvl1 = data.columns.get_level_values(1)
            if ticker in lvl0:
                return data.xs(ticker, axis=1, level=0).dropna(how='all')
            elif ticker in lvl1:
                return data.xs(ticker, axis=1, level=1).dropna(how='all')
            return None
        return data.dropna(how='all')
    except Exception:
        return None


# ---- Async Service ----

class TechnicalAnalysisService:
    """Async service for fetching and computing PSAR/AC technical data."""

    def __init__(self):
        self._cache: Dict[str, TechnicalData] = {}
        self._highs_52w: Dict[str, float] = {}
        self._last_fetch: Optional[float] = None
        self._fetching = False

    def get_cached(self) -> Dict[str, TechnicalData]:
        return dict(self._cache)

    async def fetch_52w_highs(self) -> Dict[str, float]:
        """Fetch 52-week highs for all tickers (runs once at startup)."""
        logger.info("Fetching 52-week highs for all tickers…")
        loop = asyncio.get_event_loop()

        def _download():
            try:
                data = yf.download(
                    ALL_TICKERS, period="1y", interval="1d",
                    progress=False, group_by='ticker', threads=True, timeout=60
                )
                highs: Dict[str, float] = {}
                for ticker in ALL_TICKERS:
                    t_df = _extract_ticker_df(data, ticker)
                    if t_df is not None and not t_df.empty and 'High' in t_df.columns:
                        highs[ticker] = _safe_float(t_df['High'].max())
                    else:
                        highs[ticker] = 0.0
                return highs
            except Exception as e:
                logger.error(f"52W high fetch failed: {e}")
                return {}

        result = await loop.run_in_executor(None, _download)
        self._highs_52w = result
        logger.info(f"52W highs fetched for {len(result)} tickers")
        return result

    async def fetch_all(self) -> Dict[str, TechnicalData]:
        """Fetch fresh intraday data and compute technical indicators for all tickers."""
        if self._fetching:
            return self._cache

        self._fetching = True
        start = time.time()
        loop = asyncio.get_event_loop()

        def _download():
            return yf.download(
                ALL_TICKERS,
                period="2d",
                interval="5m",
                prepost=False,
                progress=False,
                group_by='ticker',
                threads=True,
                timeout=60
            )

        try:
            data = await loop.run_in_executor(None, _download)

            if data is None or (hasattr(data, 'empty') and data.empty):
                logger.warning("Technical data fetch returned empty dataframe")
                return self._cache

            results: Dict[str, TechnicalData] = {}
            for ticker in ALL_TICKERS:
                t_df = _extract_ticker_df(data, ticker)
                if t_df is None or t_df.empty:
                    continue
                h52 = self._highs_52w.get(ticker, 0.0)
                td = _analyze_single(ticker, t_df, h52)
                if td:
                    results[td.symbol] = td

            self._cache = results
            self._last_fetch = time.time()
            logger.info(f"Technical analysis complete: {len(results)} stocks in {time.time()-start:.1f}s")
            return results

        except Exception as e:
            logger.error(f"Technical fetch_all error: {e}")
            return self._cache
        finally:
            self._fetching = False

    async def get_nifty(self) -> Optional[Dict]:
        """Fetch NIFTY 50 technical data."""
        loop = asyncio.get_event_loop()

        def _nifty():
            try:
                data = yf.download(NIFTY_TICKER, period='2d', interval='5m',
                                   progress=False, timeout=20)
                if data is None or data.empty:
                    return None

                if isinstance(data.columns, pd.MultiIndex):
                    lvl = data.columns.get_level_values(0)
                    if NIFTY_TICKER in lvl:
                        data = data.xs(NIFTY_TICKER, axis=1, level=0).dropna(how='all')

                if data.empty or len(data) < 10:
                    return None

                analyzed, reversals = calculate_ac(data)
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
