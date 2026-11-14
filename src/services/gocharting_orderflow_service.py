import json
import math
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional


class GoChartingOrderflowError(RuntimeError):
    """Safe, user-facing GoCharting webhook or signal error."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class GoChartingOrderflowService:
    """Keeps short-lived GoCharting alert confirmations in server memory.

    GoCharting sends webhook messages as text/plain. The message itself is JSON
    so the receiver can validate every field before making it visible to the
    Android client. Signals are deliberately short-lived and disappear after a
    server restart; an order-flow alert must never be carried into a later
    trading context.
    """

    india_timezone = timezone(timedelta(hours=5, minutes=30))
    symbol_pattern = re.compile(r"^[A-Z0-9][A-Z0-9&.-]{0,29}$")
    allowed_intervals = {"1m", "2m", "3m", "5m", "10m", "15m", "30m", "1h"}
    max_body_bytes = 8192
    max_symbols_per_request = 250
    signal_ttl_seconds = 420

    def __init__(self):
        self._signals: Dict[str, Dict[str, Any]] = {}
        self._last_received_at: Optional[str] = None

    @property
    def webhook_token(self) -> str:
        return os.getenv("GOCHARTING_WEBHOOK_TOKEN", "").strip()

    @property
    def ttl_seconds(self) -> int:
        return self.signal_ttl_seconds

    def is_configured(self) -> bool:
        return bool(self.webhook_token)

    def normalize_symbol(self, value: Any) -> str:
        symbol = str(value or "").strip().upper()
        if ":" in symbol:
            exchange, _, symbol = symbol.rpartition(":")
            if exchange != "NSE":
                raise GoChartingOrderflowError("Only NSE order-flow symbols are accepted.")
        if symbol.endswith(".NS"):
            symbol = symbol[:-3]
        if not self.symbol_pattern.fullmatch(symbol):
            raise GoChartingOrderflowError("Invalid order-flow symbol.")
        return symbol

    def normalize_symbols(self, values: Iterable[Any]) -> List[str]:
        normalized: List[str] = []
        seen = set()
        for value in values:
            symbol = self.normalize_symbol(value)
            if symbol not in seen:
                normalized.append(symbol)
                seen.add(symbol)
        if len(normalized) > self.max_symbols_per_request:
            raise GoChartingOrderflowError("At most 250 order-flow symbols may be requested.")
        return normalized

    @staticmethod
    def _optional_number(
        payload: Dict[str, Any],
        key: str,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
    ) -> Optional[float]:
        value = payload.get(key)
        if value is None or value == "":
            return None
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise GoChartingOrderflowError(f"{key} must be a finite number.") from exc
        if not math.isfinite(number):
            raise GoChartingOrderflowError(f"{key} must be a finite number.")
        if minimum is not None and number < minimum:
            raise GoChartingOrderflowError(f"{key} must be at least {minimum:g}.")
        if maximum is not None and number > maximum:
            raise GoChartingOrderflowError(f"{key} must be at most {maximum:g}.")
        return number

    @staticmethod
    def _now(now: Optional[datetime] = None) -> datetime:
        value = now or datetime.now(timezone.utc)
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _purge_expired(self, now: Optional[datetime] = None) -> None:
        current = self._now(now)
        expired = [
            symbol
            for symbol, signal in self._signals.items()
            if datetime.fromisoformat(signal["expires_at"]) <= current
        ]
        for symbol in expired:
            self._signals.pop(symbol, None)

    def ingest(self, raw_body: bytes, now: Optional[datetime] = None) -> Dict[str, Any]:
        if not self.is_configured():
            raise GoChartingOrderflowError(
                "GoCharting webhooks are not configured on the server.",
                status_code=503,
            )
        if not raw_body or len(raw_body) > self.max_body_bytes:
            raise GoChartingOrderflowError("Webhook body is empty or too large.")
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GoChartingOrderflowError(
                "Webhook message must be a JSON object sent as plain text."
            ) from exc
        if not isinstance(payload, dict):
            raise GoChartingOrderflowError("Webhook message must be a JSON object.")

        candidate_token = str(payload.get("token") or "")
        if not candidate_token or not secrets.compare_digest(candidate_token, self.webhook_token):
            raise GoChartingOrderflowError("Invalid GoCharting webhook token.", status_code=401)

        symbol = self.normalize_symbol(payload.get("symbol") or payload.get("ticker"))
        raw_side = str(payload.get("signal") or payload.get("side") or "").strip().upper()
        side_aliases = {"BUY": "BUY", "LONG": "BUY", "SELL": "SELL", "SHORT": "SELL"}
        side = side_aliases.get(raw_side)
        if side is None:
            raise GoChartingOrderflowError("signal must be BUY or SELL.")

        interval = str(payload.get("interval") or "5m").strip().lower()
        if interval not in self.allowed_intervals:
            raise GoChartingOrderflowError("Unsupported order-flow interval.")

        received = self._now(now)
        expires = received + timedelta(seconds=self.ttl_seconds)
        signal = {
            "symbol": symbol,
            "signal": side,
            "interval": interval,
            "delta": self._optional_number(payload, "delta"),
            "delta_percent": self._optional_number(
                payload, "delta_percent", minimum=-100, maximum=100
            ),
            "buy_volume": self._optional_number(payload, "buy_volume", minimum=0),
            "sell_volume": self._optional_number(payload, "sell_volume", minimum=0),
            "source": "GoCharting Premium",
            "received_at": received.isoformat(),
            "expires_at": expires.isoformat(),
        }
        self._signals[symbol] = signal
        self._last_received_at = signal["received_at"]
        self._purge_expired(received)
        return dict(signal)

    def get_signals(
        self,
        symbols: Iterable[Any],
        now: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        normalized = self.normalize_symbols(symbols)
        self._purge_expired(now)
        return [dict(self._signals[symbol]) for symbol in normalized if symbol in self._signals]

    def status(self, now: Optional[datetime] = None) -> Dict[str, Any]:
        self._purge_expired(now)
        return {
            "configured": self.is_configured(),
            "source": "GoCharting Premium",
            "signal_ttl_seconds": self.ttl_seconds,
            "active_signal_count": len(self._signals),
            "last_received_at": self._last_received_at,
        }


gocharting_orderflow_service = GoChartingOrderflowService()
