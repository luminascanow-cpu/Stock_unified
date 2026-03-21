
import threading
import time
import logging
import gc
import os
from datetime import datetime, timedelta
from collections import deque
import json

import pandas as pd
import numpy as np
import yfinance as yf
from flask import Flask, jsonify, render_template, request
from flask.json.provider import DefaultJSONProvider
from pytz import timezone
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# ----------------------------------
# Configuration
# ----------------------------------
TICKERS = sorted(list(set([
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

REFRESH_MINUTES = int(os.getenv('REFRESH_MINUTES', 3))
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 20))  # Download in chunks to avoid rate limits
NIFTY_TICKER = '^NSEI'
ist = timezone('Asia/Kolkata')

# PSAR Configuration
INITIAL_AF = 0.02
MAX_AF = 0.2
AF_STEP = 0.02

# ----------------------------------
# Logging Configuration
# ----------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('market_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ----------------------------------
# Circuit Breaker Pattern
# ----------------------------------
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=300):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self._lock = threading.Lock()
        
    def call(self, func, *args, **kwargs):
        with self._lock:
            if self.state == 'OPEN':
                if time.time() - self.last_failure_time > self.timeout:
                    logger.info("Circuit breaker entering HALF_OPEN state")
                    self.state = 'HALF_OPEN'
                else:
                    raise Exception(f"Circuit breaker is OPEN. Retry after {self.timeout}s")
        
        try:
            result = func(*args, **kwargs)
            with self._lock:
                if self.state == 'HALF_OPEN':
                    self.state = 'CLOSED'
                    self.failure_count = 0
                    logger.info("Circuit breaker CLOSED")
                else:
                    self.failure_count = max(0, self.failure_count - 1)
            return result
        except Exception as e:
            with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self.state = 'OPEN'
                    logger.error(f"Circuit breaker OPENED after {self.failure_count} failures")
            raise e

yf_circuit = CircuitBreaker(failure_threshold=3, timeout=600)

# ----------------------------------
# Shared State (Thread-safe)
# ----------------------------------
state_lock = threading.RLock()
shared_state = {
    "results": [],
    "last_updated": None,
    "status": "Initializing...",
    "loading": True,
    "nifty": None,
    "market_summary": {
        "total_stocks": 0,
        "bullish": 0,
        "bearish": 0,
        "neutral": 0,
        "avg_af": 0,
        "high_af_stocks": 0,
        "near_52w_high": 0
    },
    "error_log": []
}

# Performance tracking
performance_stats = {
    "fetch_times": deque(maxlen=10),
    "process_times": deque(maxlen=10),
    "total_requests": 0,
    "failed_requests": 0
}

# ----------------------------------
# Flask App & JSON Provider
# ----------------------------------
class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy/pandas types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        return super().default(obj)

class UpdatedJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        kwargs.setdefault('default', CustomJSONEncoder().default)
        return super().dumps(obj, **kwargs)

app = Flask(__name__)
app.json = UpdatedJSONProvider(app)

# ----------------------------------
# Utility Functions
# ----------------------------------
def safe_float_conversion(value, default=0.0):
    """Safely convert to float"""
    try:
        if pd.isna(value) or value is None:
            return default
        return float(value)
    except (ValueError, TypeError, OverflowError):
        return default

def format_large_number(num):
    """Format large numbers with K/M/B suffix"""
    if num is None or pd.isna(num):
        return '-'
    try:
        num = float(num)
        if num >= 1e9:
            return f"{num/1e9:.1f}B"
        elif num >= 1e6:
            return f"{num/1e6:.1f}M"
        elif num >= 1e3:
            return f"{num/1e3:.1f}K"
        else:
            return str(int(num))
    except:
        return '-'

def is_market_open():
    """Check if Indian market is likely open (simplified check)"""
    now = datetime.now(ist)
    if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    market_start = now.replace(hour=9, minute=15, second=0)
    market_end = now.replace(hour=15, minute=30, second=0)
    return market_start <= now <= market_end

# ----------------------------------
# PSAR Calculation Functions (Fixed)
# ----------------------------------
def calculate_psar_fixed(df, af=INITIAL_AF, max_af=MAX_AF, step=AF_STEP):
    """
    Fixed PSAR calculation with proper edge case handling
    """
    length = len(df)
    if length == 0:
        return [], [], [], []
    if length == 1:
        return [df['Low'].iloc[0]], [af], ['neutral'], []
    
    high = df['High'].values
    low = df['Low'].values
    close = df['Close'].values
    index = df.index
    
    psar = np.zeros(length)
    af_values = np.zeros(length)
    trend = [''] * length
    reversals = []
    
    # Initialize - determine initial trend properly
    bull = close[0] > close[1] if length > 1 else True
    af_val = af
    
    if bull:
        ep = high[0]
        psar[0] = low[0]
    else:
        ep = low[0]
        psar[0] = high[0]
        
    af_values[0] = af
    trend[0] = 'bull' if bull else 'bear'
    
    for i in range(1, length):
        # Calculate PSAR
        psar[i] = psar[i-1] + af_val * (ep - psar[i-1])
        
        # Apply SAR constraints (only if we have enough history)
        if bull:
            if i >= 2:
                psar[i] = min(psar[i], low[i-1], low[i-2])
            elif i == 1:
                psar[i] = min(psar[i], low[i-1])
        else:
            if i >= 2:
                psar[i] = max(psar[i], high[i-1], high[i-2])
            elif i == 1:
                psar[i] = max(psar[i], high[i-1])
        
        # Check for trend reversal
        if bull:
            if low[i] < psar[i]:
                # Bull to bear reversal
                bull = False
                reversals.append({
                    'index': i,
                    'type': 'BULL_TO_BEAR',
                    'price': float(low[i]),
                    'sar': float(psar[i]),
                    'timestamp': str(index[i])
                })
                psar[i] = ep
                ep = low[i]
                af_val = af
                trend[i] = 'bear'
            else:
                trend[i] = 'bull'
                if high[i] > ep:
                    ep = high[i]
                    af_val = min(af_val + step, max_af)
        else:
            if high[i] > psar[i]:
                # Bear to bull reversal
                bull = True
                reversals.append({
                    'index': i,
                    'type': 'BEAR_TO_BULL',
                    'price': float(high[i]),
                    'sar': float(psar[i]),
                    'timestamp': str(index[i])
                })
                psar[i] = ep
                ep = high[i]
                af_val = af
                trend[i] = 'bull'
            else:
                trend[i] = 'bear'
                if low[i] < ep:
                    ep = low[i]
                    af_val = min(af_val + step, max_af)
        
        af_values[i] = af_val
    
    return psar.tolist(), af_values.tolist(), trend, reversals

def detect_psar_signals(df, psar_values, trend):
    """
    Detect PSAR trading signals - Fixed logic
    """
    length = len(df)
    if length < 2:
        return []
    
    signals = []
    close = df['Close'].values
    index = df.index
    
    for i in range(1, length):
        # Bullish crossover: Price crosses above PSAR
        if close[i-1] <= psar_values[i-1] and close[i] > psar_values[i]:
            signals.append({
                'timestamp': str(index[i]),
                'type': 'BULLISH_CROSSOVER',
                'price': float(close[i]),
                'psar': float(psar_values[i]),
                'strength': 'STRONG' if close[i] > psar_values[i] * 1.02 else 'NORMAL'
            })
        # Bearish crossover: Price crosses below PSAR
        elif close[i-1] >= psar_values[i-1] and close[i] < psar_values[i]:
            signals.append({
                'timestamp': str(index[i]),
                'type': 'BEARISH_CROSSOVER',
                'price': float(close[i]),
                'psar': float(psar_values[i]),
                'strength': 'STRONG' if close[i] < psar_values[i] * 0.98 else 'NORMAL'
            })
    
    return signals

def calculate_acceleration_factor(data):
    """Computes technical indicators - Memory optimized"""
    if len(data) < 10:
        return None, None, None
        
    df = data.copy()
    df['Midpoint'] = (df['High'] + df['Low']) / 2
    
    # Velocity (5-period SMA diff)
    df['SMA_5'] = df['Midpoint'].rolling(window=5, min_periods=1).mean()
    df['Velocity'] = df['SMA_5'].diff()
    
    # Bill Williams AC
    df['SMA_34'] = df['Midpoint'].rolling(window=34, min_periods=1).mean()
    df['AO'] = df['SMA_5'] - df['SMA_34']
    df['Standard_AC'] = df['AO'] - df['AO'].rolling(window=5, min_periods=1).mean()
    
    # PSAR calculation
    psar_values, af_values, trend, reversals = calculate_psar_fixed(df)
    df['PSAR'] = psar_values
    df['PSAR_AF'] = af_values
    df['PSAR_Trend'] = trend
    
    # Signal detection (don't store all signals in DataFrame - memory hog)
    all_signals = detect_psar_signals(df, psar_values, trend)
    
    # Only keep last 3 signals to prevent memory bloat
    recent_signals = all_signals[-3:] if len(all_signals) > 3 else all_signals
    
    return df, reversals, recent_signals

# ----------------------------------
# Data Fetching Functions (Optimized)
# ----------------------------------
@retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((Exception))
)
def download_with_circuit_breaker(tickers, period, interval, group_by='ticker'):
    """Wrapper with circuit breaker"""
    return yf.download(
        tickers,
        period=period,
        interval=interval,
        prepost=False,
        progress=False,
        group_by=group_by,
        threads=True,
        timeout=30
    )

def get_fresh_data_chunked(tickers, chunk_size=CHUNK_SIZE):
    """Fetch data in chunks to avoid rate limiting"""
    start_time = time.time()
    all_data = {}
    
    # Split tickers into chunks
    chunks = [tickers[i:i+chunk_size] for i in range(0, len(tickers), chunk_size)]
    logger.info(f"Downloading data in {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        try:
            data = yf_circuit.call(
                download_with_circuit_breaker,
                chunk,
                period="2d",
                interval="5m"
            )
            
            if isinstance(data.columns, pd.MultiIndex):
                for ticker in chunk:
                    try:
                        if ticker in data.columns.get_level_values(0):
                            ticker_data = data.xs(ticker, axis=1, level=0).dropna(how='all')
                            if not ticker_data.empty:
                                all_data[ticker] = ticker_data
                    except Exception as e:
                        logger.warning(f"Error extracting {ticker}: {e}")
            else:
                # Single ticker case
                if len(chunk) == 1 and not data.empty:
                    all_data[chunk[0]] = data.dropna(how='all')
            
            # Rate limiting - be nice to Yahoo
            if i < len(chunks) - 1:
                time.sleep(2)
                
        except Exception as e:
            logger.error(f"Failed to download chunk {i+1}: {e}")
            performance_stats["failed_requests"] += 1
            continue
    
    fetch_time = time.time() - start_time
    performance_stats["fetch_times"].append(fetch_time)
    performance_stats["total_requests"] += 1
    
    logger.info(f"Fetched data for {len(all_data)} tickers in {fetch_time:.2f}s")
    return all_data

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
def get_52w_highs(tickers):
    """Fetch 52-week highs"""
    try:
        data = yf.download(
            tickers, 
            period="1y", 
            interval="1d", 
            progress=False, 
            group_by='ticker', 
            threads=True,
            timeout=30
        )
        
        highs = {}
        for ticker in tickers:
            try:
                if isinstance(data.columns, pd.MultiIndex):
                    if ticker in data.columns.get_level_values(0):
                        ticker_data = data.xs(ticker, axis=1, level=0).dropna(how='all')
                    else:
                        highs[ticker] = 0.0
                        continue
                else:
                    ticker_data = data.dropna(how='all')
                
                if not ticker_data.empty and 'High' in ticker_data.columns:
                    highs[ticker] = safe_float_conversion(ticker_data['High'].max())
                else:
                    highs[ticker] = 0.0
            except Exception:
                highs[ticker] = 0.0
        return highs
    except Exception as e:
        logger.error(f"52-week highs fetch failed: {e}")
        return {}

def get_nifty_trend():
    """Fetch Nifty 50 data"""
    try:
        data = yf.download(NIFTY_TICKER, period='2d', interval='5m', progress=False, timeout=15)
        if data.empty: 
            return None
        
        if isinstance(data.columns, pd.MultiIndex):
            if NIFTY_TICKER in data.columns.get_level_values(0):
                data = data.xs(NIFTY_TICKER, axis=1, level=0).dropna(how='all')
            elif NIFTY_TICKER in data.columns.get_level_values(1):
                data = data.xs(NIFTY_TICKER, axis=1, level=1).dropna(how='all')
        
        if data.empty or len(data) < 10: 
            return None
            
        data, reversals, signals = calculate_acceleration_factor(data)
        if data is None:
            return None
            
        ltp = safe_float_conversion(data['Close'].iloc[-1])
        velocity = safe_float_conversion(data['Velocity'].iloc[-1])
        ac = safe_float_conversion(data['Standard_AC'].iloc[-1])
        psar_af = safe_float_conversion(data['PSAR_AF'].iloc[-1])
        trend = data['PSAR_Trend'].iloc[-1]
        
        return {
            'ltp': round(float(ltp), 2),
            'velocity': round(float(velocity), 4),
            'ac': round(float(ac), 4),
            'psar_af': round(float(psar_af), 2),
            'trend': str(trend).upper(),
            'reversal_count': len(reversals),
            'last_signal': signals[-1] if signals else None
        }
    except Exception as e:
        logger.error(f'Nifty trend error: {e}')
        return None

def analyze_stock(ticker_data, ticker, highs_52w=None):
    """Analyze single stock with validation"""
    try:
        # Validation checks
        if ticker_data is None or len(ticker_data) < 20:
            return None
            
        required_cols = ['Open', 'High', 'Low', 'Close']
        if not all(col in ticker_data.columns for col in required_cols):
            logger.warning(f"Missing required columns for {ticker}")
            return None
            
        # Check data quality
        if ticker_data['Close'].isna().sum() > len(ticker_data) * 0.2:  # >20% NaN
            logger.warning(f"Too many NaN values for {ticker}")
            return None
            
        current_price = safe_float_conversion(ticker_data['Close'].iloc[-1])
        if current_price <= 0:
            return None
            
        analyzed_data, reversals, signals = calculate_acceleration_factor(ticker_data)
        if analyzed_data is None:
            return None
        
        velocity_val = safe_float_conversion(analyzed_data['Velocity'].iloc[-1])
        ac_val = safe_float_conversion(analyzed_data['Standard_AC'].iloc[-1])
        psar_af = safe_float_conversion(analyzed_data['PSAR_AF'].iloc[-1])
        current_trend = analyzed_data['PSAR_Trend'].iloc[-1]
        
        # AF increase rate calculation
        af_values = analyzed_data['PSAR_AF'].dropna().values
        af_increase_count = sum(1 for i in range(1, len(af_values)) if af_values[i] > af_values[i-1])
        af_increase_rate = (af_increase_count / len(af_values)) * 100 if len(af_values) > 1 else 0
        
        # 52-week high calculations
        h52 = highs_52w.get(ticker, 0.0) if highs_52w else 0.0
        dist_52w = ((current_price - h52) / h52) * 100 if h52 > 0 else None
        
        current_volume = safe_float_conversion(ticker_data['Volume'].iloc[-1]) if 'Volume' in ticker_data.columns else 0.0

        # Signal logic
        signal = 'NEUTRAL'
        if ac_val > 0.002 and velocity_val > 0 and current_trend == 'bull': 
            signal = 'STRONG_BUY'
        elif ac_val < -0.002 and velocity_val < 0 and current_trend == 'bear': 
            signal = 'STRONG_SELL'
        elif ac_val > 0 and current_trend == 'bull': 
            signal = 'BUY'
        elif ac_val < 0 and current_trend == 'bear': 
            signal = 'SELL'
        
        return {
            'ticker': ticker,
            'ltp': round(float(current_price), 2),
            'high_52w': round(float(h52), 2) if h52 else None,
            'distance_52w': round(float(dist_52w), 2) if dist_52w is not None else None,
            'velocity': round(float(velocity_val), 4),
            'ac': round(float(ac_val), 4),
            'psar_af': round(float(psar_af), 2),
            'psar_trend': str(current_trend),
            'af_increase_rate': round(float(af_increase_rate), 2),
            'volume': format_large_number(current_volume),
            'signal_strength': signal,
            'reversal_count': len(reversals),
            'recent_signals': signals
        }
    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {e}", exc_info=False)
        return None

def calculate_market_summary(results):
    """Calculate market summary statistics"""
    if not results: 
        return {}
    
    bullish = sum(1 for r in results if r.get('psar_trend') == 'bull')
    bearish = sum(1 for r in results if r.get('psar_trend') == 'bear')
    avg_af = np.mean([r.get('psar_af', 0) for r in results])
    
    # Count near 52w high (within 5%)
    near_high = sum(1 for r in results if r.get('distance_52w') and r.get('distance_52w') > -5)
    
    return {
        "total_stocks": len(results),
        "bullish": bullish,
        "bearish": bearish,
        "neutral": len(results) - bullish - bearish,
        "avg_af": round(float(avg_af), 2),
        "strong_buy": sum(1 for r in results if r.get('signal_strength') == 'STRONG_BUY'),
        "strong_sell": sum(1 for r in results if r.get('signal_strength') == 'STRONG_SELL'),
        "near_52w_high": near_high
    }

# ----------------------------------
# Background Worker (Fixed)
# ----------------------------------
def refresh_data_loop(highs_52w=None):
    """Main data refresh loop"""
    try:
        with state_lock:
            shared_state["status"] = "Fetching..."
            shared_state["loading"] = True

        start_time = time.time()
        
        # Get data using chunked download
        data_dict = get_fresh_data_chunked(TICKERS)
        
        if not data_dict:
            with state_lock: 
                shared_state["status"] = "Data fetch failed"
                shared_state["loading"] = False
            return

        results = []
        for ticker in TICKERS:
            try:
                if ticker in data_dict:
                    t_data = data_dict[ticker]
                    analysis = analyze_stock(t_data, ticker, highs_52w)
                    if analysis: 
                        results.append(analysis)
            except Exception as e:
                logger.debug(f"Skipping {ticker}: {e}")
                continue

        # Sort by AC (momentum)
        results.sort(key=lambda x: x.get('ac', 0), reverse=True)
        
        # Calculate summary
        market_summary = calculate_market_summary(results)
        
        # Get Nifty data
        nifty = get_nifty_trend()
        
        process_time = time.time() - start_time
        performance_stats["process_times"].append(process_time)

        with state_lock:
            shared_state["results"] = results
            shared_state["last_updated"] = datetime.now(ist).strftime('%H:%M:%S %d-%m-%Y')
            shared_state["status"] = "OK"
            shared_state["loading"] = False
            shared_state["nifty"] = nifty
            shared_state["market_summary"] = market_summary
            
        logger.info(f"Processed {len(results)} stocks in {process_time:.2f}s")
        
        # Force garbage collection to prevent memory bloat
        gc.collect()
        
    except Exception as e:
        logger.error(f"Loop error: {e}", exc_info=True)
        with state_lock: 
            shared_state["status"] = f"Error: {str(e)[:50]}"
            shared_state["loading"] = False
            shared_state["error_log"].append({
                'time': datetime.now(ist).isoformat(),
                'error': str(e)
            })
            # Keep only last 10 errors
            shared_state["error_log"] = shared_state["error_log"][-10:]

def background_worker():
    """Background worker with 52w high refresh"""
    highs_52w = {}
    last_52w_update = 0
    
    logger.info("Background worker started")
    
    # Initial fetch
    try:
        highs_52w = get_52w_highs(TICKERS[:50])  # Fetch first 50 initially
        last_52w_update = time.time()
    except Exception as e:
        logger.error(f"Failed to fetch initial 52W highs: {e}")
    
    while True:
        try:
            # Refresh 52w highs daily (86400 seconds)
            if time.time() - last_52w_update > 86400:
                try:
                    logger.info("Refreshing 52-week highs...")
                    new_highs = get_52w_highs(TICKERS)
                    if new_highs:
                        highs_52w = new_highs
                        last_52w_update = time.time()
                        logger.info("52-week highs refreshed")
                except Exception as e:
                    logger.error(f"Failed to refresh 52w highs: {e}")
            
            # Market hours check (optional - can remove if you want 24/7)
            if not is_market_open():
                logger.info("Market closed, sleeping...")
                time.sleep(300)  # Check every 5 minutes when closed
                continue
            
            start = time.time()
            refresh_data_loop(highs_52w)
            duration = time.time() - start
            
            # Calculate sleep time
            sleep_time = max(10, (REFRESH_MINUTES * 60) - duration)
            logger.info(f"Loop completed in {duration:.2f}s. Sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
            
        except Exception as e:
            logger.error(f"Critical error in background worker: {e}")
            time.sleep(60)

def start_background_worker():
    worker = threading.Thread(target=background_worker, daemon=True)
    worker.start()
    return worker

# ----------------------------------
# Routes
# ----------------------------------
@app.route('/')
def index():
    return render_template('index.html', refresh_minutes=REFRESH_MINUTES)

@app.route('/api/stocks')
def api_stocks():
    with state_lock:
        response_data = {
            "results": shared_state["results"],
            "last_updated": shared_state["last_updated"],
            "status": shared_state["status"],
            "loading": shared_state["loading"],
            "nifty": shared_state["nifty"],
            "market_summary": shared_state["market_summary"],
            "market_open": is_market_open(),
            "performance": {
                "avg_fetch_time": round(float(np.mean(performance_stats["fetch_times"])), 2) if performance_stats["fetch_times"] else 0,
                "avg_process_time": round(float(np.mean(performance_stats["process_times"])), 2) if performance_stats["process_times"] else 0,
                "success_rate": round(float((1 - performance_stats["failed_requests"] / max(performance_stats["total_requests"], 1)) * 100), 2),
                "total_requests": performance_stats["total_requests"]
            }
        }
        return jsonify(response_data)

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    with state_lock:
        last_update = shared_state["last_updated"]
        status = shared_state["status"]
    
    if not last_update:
        return jsonify({
            "status": "INITIALIZING",
            "timestamp": datetime.now(ist).isoformat()
        }), 503
    
    # Parse last update time
    try:
        last_dt = datetime.strptime(last_update, '%H:%M:%S %d-%m-%Y')
        last_dt = last_dt.replace(year=datetime.now().year)  # Add current year
        diff = (datetime.now() - last_dt).total_seconds()
        
        if diff > REFRESH_MINUTES * 60 * 3:  # 3x refresh interval = stale
            return jsonify({
                "status": "STALE",
                "last_update": last_update,
                "seconds_behind": int(diff),
                "circuit_breaker": yf_circuit.state
            }), 503
    except Exception:
        pass
    
    return jsonify({
        "status": "HEALTHY",
        "last_update": last_update,
        "stocks_tracked": len(shared_state["results"]),
        "circuit_breaker": yf_circuit.state,
        "timestamp": datetime.now(ist).isoformat()
    })

@app.route('/api/ticker/<ticker>')
def get_ticker_detail(ticker):
    """Get detailed data for specific ticker"""
    ticker = ticker.upper()
    with state_lock:
        for stock in shared_state["results"]:
            if stock['ticker'] == ticker:
                return jsonify(stock)
    return jsonify({"error": "Ticker not found"}), 404

# ----------------------------------
# Main
# ----------------------------------
if __name__ == '__main__':
    start_background_worker()
    # Use threaded=True for production, debug=False
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
