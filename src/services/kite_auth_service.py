import hashlib
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from urllib.parse import urlencode


class KiteAuthError(RuntimeError):
    """Safe, user-facing Kite authentication error."""


class KiteAuthService:
    login_endpoint = "https://kite.zerodha.com/connect/login"
    token_endpoint = "https://api.kite.trade/session/token"
    india_timezone = timezone(timedelta(hours=5, minutes=30))

    def __init__(self, state_ttl_seconds: int = 600):
        self.state_ttl_seconds = state_ttl_seconds
        self.max_pending_states = 256
        self._pending_states: Dict[str, Dict[str, Any]] = {}
        self._access_token: Optional[str] = None
        self._session: Dict[str, Any] = {}
        self._session_day: Optional[str] = None
        self._client_sessions: Dict[str, str] = {}
        self._client_request_at: Dict[str, float] = {}

    @property
    def api_key(self) -> str:
        return os.getenv("KITE_API_KEY", "").strip()

    @property
    def api_secret(self) -> str:
        return os.getenv("KITE_API_SECRET", "").strip()

    @property
    def access_token(self) -> Optional[str]:
        self._expire_stale_session()
        return self._access_token

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def create_login_url(self) -> str:
        return self._create_login_url()

    def create_app_login(self) -> Dict[str, str]:
        client_session_token = secrets.token_urlsafe(48)
        return {
            "login_url": self._create_login_url(client_session_token),
            "client_session_token": client_session_token,
        }

    def _create_login_url(self, client_session_token: Optional[str] = None) -> str:
        if not self.is_configured():
            raise KiteAuthError(
                "Kite is not configured. Set KITE_API_KEY and KITE_API_SECRET on the server."
            )

        self._discard_expired_states()
        while len(self._pending_states) >= self.max_pending_states:
            self._pending_states.pop(next(iter(self._pending_states)))
        state = secrets.token_urlsafe(32)
        self._pending_states[state] = {
            "expires_at": time.time() + self.state_ttl_seconds,
            "client_session_token": client_session_token,
        }
        redirect_params = urlencode({"state": state})
        return f"{self.login_endpoint}?{urlencode({'v': '3', 'api_key': self.api_key, 'redirect_params': redirect_params})}"

    def validate_state(self, state: Optional[str]) -> Optional[str]:
        self._discard_expired_states()
        if not state:
            raise KiteAuthError("Missing Kite login state. Start again from /auth/kite/login.")

        pending = self._pending_states.pop(state, None)
        if pending is None or float(pending.get("expires_at", 0)) < time.time():
            raise KiteAuthError("Invalid or expired Kite login state. Start the login again.")
        return pending.get("client_session_token")

    @staticmethod
    def checksum(api_key: str, request_token: str, api_secret: str) -> str:
        raw = f"{api_key}{request_token}{api_secret}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    async def exchange_request_token(self, request_token: str, client=None) -> Dict[str, Any]:
        if not self.is_configured():
            raise KiteAuthError(
                "Kite is not configured. Set KITE_API_KEY and KITE_API_SECRET on the server."
            )
        if not request_token:
            raise KiteAuthError("Kite did not return a request token.")

        form = {
            "api_key": self.api_key,
            "request_token": request_token,
            "checksum": self.checksum(self.api_key, request_token, self.api_secret),
        }
        headers = {"X-Kite-Version": "3"}

        try:
            if client is None:
                import httpx

                async with httpx.AsyncClient(timeout=15.0) as owned_client:
                    response = await owned_client.post(
                        self.token_endpoint,
                        data=form,
                        headers=headers,
                    )
            else:
                response = await client.post(
                    self.token_endpoint,
                    data=form,
                    headers=headers,
                )
        except Exception as exc:
            raise KiteAuthError("Could not reach Kite to complete authentication.") from exc

        try:
            payload = response.json()
        except Exception as exc:
            raise KiteAuthError("Kite returned an invalid authentication response.") from exc

        data = payload.get("data") if isinstance(payload, dict) else None
        access_token = data.get("access_token") if isinstance(data, dict) else None
        if response.status_code >= 400 or payload.get("status") != "success" or not access_token:
            raise KiteAuthError(
                f"Kite rejected the authentication request (HTTP {response.status_code})."
            )

        authenticated_at = datetime.now(timezone.utc).isoformat()
        # A new broker login supersedes every older app authorization. The
        # callback activates only the app session tied to this exact login.
        self._client_sessions = {}
        self._client_request_at = {}
        self._access_token = access_token
        self._session_day = self._today_in_india()
        self._session = {
            "authenticated": True,
            "authenticated_at": authenticated_at,
            "user_id": data.get("user_id"),
            "user_name": data.get("user_name"),
        }
        return self.status()

    def status(self) -> Dict[str, Any]:
        self._expire_stale_session()
        return {
            "configured": self.is_configured(),
            "authenticated": bool(self._access_token),
            "authenticated_at": self._session.get("authenticated_at"),
            "user_id": self._session.get("user_id"),
            "session_day": self._session_day,
            "requires_daily_login": True,
        }

    def clear_session(self) -> None:
        self._access_token = None
        self._session = {}
        self._session_day = None
        self._client_sessions = {}
        self._client_request_at = {}

    def clear_session_if_token(self, access_token: str) -> bool:
        current = self._access_token or ""
        candidate = access_token or ""
        if not current or not secrets.compare_digest(current, candidate):
            return False
        self.clear_session()
        return True

    def activate_client_session(self, client_session_token: Optional[str]) -> None:
        if not client_session_token or not self.access_token:
            return
        self._client_sessions[client_session_token] = self._today_in_india()

    def is_client_session_authorized(self, client_session_token: Optional[str]) -> bool:
        self._expire_stale_session()
        if not self._access_token or not client_session_token:
            return False
        session_day = self._client_sessions.get(client_session_token)
        return session_day == self._today_in_india()

    def allow_client_quote_request(
        self, client_session_token: Optional[str], minimum_interval_seconds: float = 1.0
    ) -> bool:
        if not self.is_client_session_authorized(client_session_token):
            return False
        now = time.monotonic()
        previous = self._client_request_at.get(client_session_token or "", 0.0)
        if now - previous < minimum_interval_seconds:
            return False
        self._client_request_at[client_session_token or ""] = now
        return True

    def _today_in_india(self) -> str:
        return datetime.now(self.india_timezone).date().isoformat()

    def _expire_stale_session(self) -> None:
        if self._access_token and self._session_day != self._today_in_india():
            self.clear_session()

    def _discard_expired_states(self) -> None:
        now = time.time()
        self._pending_states = {
            state: pending
            for state, pending in self._pending_states.items()
            if float(pending.get("expires_at", 0)) >= now
        }


kite_auth_service = KiteAuthService()
