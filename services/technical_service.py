"""Technical analysis service - PSAR + Bill Williams AC"""
import logging
import asyncio
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# PSAR Configuration
INITIAL_AF = 0.02
MAX_AF = 0.2
AF_STEP = 0.02

class TechnicalService:
    def __init__(self):
        self.healthy = True
        self._cache = {}
    
    def calculate_psar_fixed(self, df, af=INITIAL_AF, max_af=MAX_AF, step=AF_STEP):
        """Fixed PSAR calculation"""
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
            psar[i] = psar[i-1] + af_val * (ep - psar[i-1])
            
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
            
            if bull:
                if low[i] < psar[i]:
                    bull = False
                    reversals.append({'index': i, 'type': 'BULL_TO_BEAR', 'price': float(low[i])})
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
                    bull = True
                    reversals.append({'index': i, 'type': 'BEAR_TO_BULL', 'price': float(high[i])})
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
    
    def calculate_acceleration_factor(self, data):
        """Compute technical indicators"""
        if len(data) < 10:
            return None, None, None
        
        df = data.copy()
        df['Midpoint'] = (df['High'] + df['Low']) / 2
        df['SMA_5'] = df['Midpoint'].rolling(window=5, min_periods=1).mean()
        df['Velocity'] = df['SMA_5'].diff()
        df['SMA_34'] = df['Midpoint'].rolling(window=34, min_periods=1).mean()
        df['AO'] = df['SMA_5'] - df['SMA_34']
        df['Standard_AC'] = df['AO'] - df['AO'].rolling(window=5, min_periods=1).mean()
        
        psar_values, af_values, trend, reversals = self.calculate_psar_fixed(df)
        df['PSAR'] = psar_values
        df['PSAR_AF'] = af_values
        df['PSAR_Trend'] = trend
        
        return df, reversals, []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_ticker(self, symbol: str):
        """Fetch single ticker data"""
        try:
            data = yf.download(symbol, period="2d", interval="5m", progress=False, timeout=30)
            if data.empty:
                logger.debug(f"No data for {symbol}")
                return None
            
            # Handle MultiIndex columns (yfinance returns MultiIndex: [Price, Ticker])
            if isinstance(data.columns, pd.MultiIndex):
                # Symbol is in level 1 (Ticker), Price types in level 0
                if symbol in data.columns.get_level_values(1):
                    data = data.xs(symbol, axis=1, level=1).dropna(how='all')
                elif symbol in data.columns.get_level_values(0):
                    data = data.xs(symbol, axis=1, level=0).dropna(how='all')
                else:
                    # Fallback: flatten columns
                    data.columns = data.columns.droplevel(1)
                    data = data.dropna(how='all')
            
            if data.empty or len(data) < 20:
                logger.debug(f"Insufficient data for {symbol}: {len(data)} rows")
                return None
            
            return data
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return None
    
    def analyze_stock(self, ticker_data, symbol: str, highs_52w: float = 0.0):
        """Analyze single stock"""
        try:
            if ticker_data is None or len(ticker_data) < 20:
                return None
            
            required_cols = ['Open', 'High', 'Low', 'Close']
            if not all(col in ticker_data.columns for col in required_cols):
                logger.debug(f"Missing columns for {symbol}: {ticker_data.columns}")
                return None
            
            current_price = float(ticker_data['Close'].iloc[-1])
            if current_price <= 0:
                return None
            
            analyzed_data, reversals, signals = self.calculate_acceleration_factor(ticker_data)
            if analyzed_data is None:
                return None
            
            velocity_val = float(analyzed_data['Velocity'].iloc[-1]) if not pd.isna(analyzed_data['Velocity'].iloc[-1]) else 0.0
            ac_val = float(analyzed_data['Standard_AC'].iloc[-1]) if not pd.isna(analyzed_data['Standard_AC'].iloc[-1]) else 0.0
            psar_af = float(analyzed_data['PSAR_AF'].iloc[-1]) if not pd.isna(analyzed_data['PSAR_AF'].iloc[-1]) else 0.0
            current_trend = str(analyzed_data['PSAR_Trend'].iloc[-1])
            
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
            
            # 52-week high distance
            dist_52w = ((current_price - highs_52w) / highs_52w) * 100 if highs_52w > 0 else None
            
            result = {
                'symbol': symbol,
                'ltp': round(current_price, 2),
                'high_52w': round(highs_52w, 2) if highs_52w else None,
                'distance_52w': round(dist_52w, 2) if dist_52w is not None else None,
                'velocity': round(velocity_val, 4),
                'ac': round(ac_val, 4),
                'psar_af': round(psar_af, 2),
                'psar_trend': current_trend,
                'signal': signal,
                'reversal_count': len(reversals)
            }
            logger.debug(f"Analyzed {symbol}: {signal}, AC={ac_val}, PSAR={current_trend}")
            return result
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}", exc_info=False)
            return None
    
    async def fetch_all_tickers(self, symbols: List[str] = None):
        """Fetch technical data for all tickers"""
        if symbols is None:
            symbols = [
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
            ]
        
        logger.info(f"Fetching data for {len(symbols)} tickers...")
        results = []
        
        # Fetch in chunks to avoid rate limiting
        chunk_size = 20
        for i in range(0, len(symbols), chunk_size):
            chunk = symbols[i:i+chunk_size]
            logger.info(f"Processing chunk {i//chunk_size + 1}/{(len(symbols)+chunk_size-1)//chunk_size}")
            
            for symbol in chunk:
                try:
                    data = self.fetch_ticker(symbol)
                    if data:
                        analysis = self.analyze_stock(data, symbol)
                        if analysis:
                            results.append(analysis)
                except Exception as e:
                    logger.debug(f"Skipping {symbol}: {e}")
            
            # Rate limiting
            if i + chunk_size < len(symbols):
                await asyncio.sleep(2)
        
        logger.info(f"Analyzed {len(results)} stocks")
        return results
    
    def is_healthy(self):
        return self.healthy
