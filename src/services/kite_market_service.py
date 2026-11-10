from datetime import datetime, timedelta, timezone
import math
import re
from typing import Any, Dict, Iterable, List, Optional

from .kite_auth_service import KiteAuthService, kite_auth_service


class KiteMarketError(RuntimeError):
    """A safe Kite market-data error with an API-facing HTTP status."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class KiteMarketService:
    quote_endpoint = "https://api.kite.trade/quote"
    india_timezone = timezone(timedelta(hours=5, minutes=30))
    symbol_pattern = re.compile(r"^[A-Z0-9][A-Z0-9&-]{0,29}$")
    max_symbols = 250

    def __init__(self, auth_service: KiteAuthService = kite_auth_service):
        self.auth_service = auth_service

    def normalize_symbols(self, symbols: Iterable[str]) -> List[str]:
        normalized: List[str] = []
        seen = set()
        for raw_symbol in symbols:
            symbol = str(raw_symbol or "").strip().upper()
            if symbol.endswith(".NS"):
                symbol = symbol[:-3]
            if not symbol or symbol in seen:
                continue
            if not self.symbol_pattern.fullmatch(symbol):
                raise KiteMarketError(f"Unsupported NSE symbol: {symbol[:30]}", 400)
            seen.add(symbol)
            normalized.append(symbol)
        if not normalized:
            raise KiteMarketError("At least one NSE symbol is required.", 400)
        if len(normalized) > self.max_symbols:
            raise KiteMarketError(
                f"A maximum of {self.max_symbols} NSE symbols can be requested.",
                400,
            )
        return normalized

    async def get_quotes(self, symbols: Iterable[str], client=None) -> Dict[str, Any]:
        normalized = self.normalize_symbols(symbols)
        access_token = self.auth_service.access_token
        if not access_token:
            raise KiteMarketError("Kite login is required for today's market data.", 401)

        headers = {
            "X-Kite-Version": "3",
            "Authorization": f"token {self.auth_service.api_key}:{access_token}",
        }
        params = [("i", f"NSE:{symbol}") for symbol in normalized]

        try:
            if client is None:
                import httpx

                async with httpx.AsyncClient(timeout=15.0) as owned_client:
                    response = await owned_client.get(
                        self.quote_endpoint,
                        params=params,
                        headers=headers,
                    )
            else:
                response = await client.get(
                    self.quote_endpoint,
                    params=params,
                    headers=headers,
                )
        except Exception as exc:
            raise KiteMarketError("Could not reach Kite for market quotes.") from exc

        if response.status_code in (401, 403):
            self.auth_service.clear_session_if_token(access_token)
            raise KiteMarketError("The Kite session expired. Sign in again.", 401)

        try:
            payload = response.json()
        except Exception as exc:
            raise KiteMarketError("Kite returned an invalid market-data response.") from exc
        payload_status = payload.get("status") if isinstance(payload, dict) else None
        data = payload.get("data") if isinstance(payload, dict) else None
        if response.status_code >= 400 or payload_status != "success" or not isinstance(data, dict):
            raise KiteMarketError(
                f"Kite rejected the market-data request (HTTP {response.status_code})."
            )

        quotes = []
        missing_symbols = []
        for symbol in normalized:
            raw_quote = data.get(f"NSE:{symbol}")
            if not isinstance(raw_quote, dict):
                missing_symbols.append(symbol)
                continue
            normalized_quote = self._normalize_quote(symbol, raw_quote)
            if not normalized_quote.get("available"):
                missing_symbols.append(symbol)
                continue
            quotes.append(normalized_quote)

        return {
            "source": "Zerodha Kite",
            "as_of": datetime.now(timezone.utc).isoformat(),
            "session_day": datetime.now(self.india_timezone).date().isoformat(),
            "requested_count": len(normalized),
            "quote_count": len(quotes),
            "missing_symbols": missing_symbols,
            "quotes": quotes,
        }

    def _normalize_quote(self, symbol: str, raw_quote: Dict[str, Any]) -> Dict[str, Any]:
        last_price = self._number(raw_quote.get("last_price"))
        ohlc = raw_quote.get("ohlc") if isinstance(raw_quote.get("ohlc"), dict) else {}
        previous_close = self._number(ohlc.get("close"))
        change = None
        change_percent = None
        if last_price is not None and previous_close not in (None, 0):
            change = last_price - previous_close
            change_percent = change / previous_close * 100

        raw_timestamp = str(raw_quote.get("timestamp") or "").strip()
        quote_timestamp, quote_epoch, quote_time = self._normalize_india_timestamp(raw_timestamp)
        volume = self._integer(raw_quote.get("volume"))
        tuple_complete = (
            last_price is not None
            and last_price > 0
            and previous_close is not None
            and previous_close > 0
            and quote_epoch is not None
            and quote_epoch > 0
            and volume is not None
            and volume >= 0
            and change is not None
            and math.isfinite(change)
            and change_percent is not None
            and math.isfinite(change_percent)
        )
        normalized = {
            "symbol": symbol,
            "available": tuple_complete,
            "ltp": self._rounded(last_price),
            "change": self._rounded(change),
            "change_percent": self._rounded(change_percent),
            "session_volume": volume,
            "quote_timestamp": quote_timestamp,
            "quote_epoch": quote_epoch,
            "quote_time": quote_time,
            "quote_source": "Zerodha Kite",
            "instrument_token": raw_quote.get("instrument_token"),
            "open": self._rounded(self._number(ohlc.get("open"))),
            "high": self._rounded(self._number(ohlc.get("high"))),
            "low": self._rounded(self._number(ohlc.get("low"))),
            "previous_close": self._rounded(previous_close),
        }
        if last_price is not None and volume is not None:
            normalized["turnover_estimate"] = round(last_price * volume, 2)
        return {key: value for key, value in normalized.items() if value is not None}

    def _normalize_india_timestamp(
        self, value: str
    ) -> tuple[Optional[str], Optional[int], Optional[str]]:
        if not value:
            return None, None, None
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=self.india_timezone
            )
            return parsed.isoformat(), int(parsed.timestamp()), parsed.strftime("%H:%M:%S")
        except ValueError:
            return None, None, None

    @staticmethod
    def _number(value: Any) -> Optional[float]:
        try:
            number = float(value)
            return number if math.isfinite(number) else None
        except (TypeError, ValueError, OverflowError):
            return None

    @staticmethod
    def _integer(value: Any) -> Optional[int]:
        try:
            number = int(value)
            return number if number >= 0 else None
        except (TypeError, ValueError, OverflowError):
            return None

    @staticmethod
    def _rounded(value: Optional[float]) -> Optional[float]:
        return round(value, 4) if value is not None else None


kite_market_service = KiteMarketService()
