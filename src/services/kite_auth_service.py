import hashlib
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from urllib.parse import urlencode


class KiteAuthError(RuntimeError):
    """Safe, user-facing Kite authentication error."""


class KiteAuthService:
    login_endpoint = "https://kite.zerodha.com/connect/login"
    token_endpoint = "https://api.kite.trade/session/token"

    def __init__(self, state_ttl_seconds: int = 600):
        self.state_ttl_seconds = state_ttl_seconds
        self._pending_states: Dict[str, float] = {}
        self._access_token: Optional[str] = None
        self._session: Dict[str, Any] = {}

    @property
    def api_key(self) -> str:
        return os.getenv("KITE_API_KEY", "").strip()

    @property
    def api_secret(self) -> str:
        return os.getenv("KITE_API_SECRET", "").strip()

    @property
    def access_token(self) -> Optional[str]:
        return self._access_token

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def create_login_url(self) -> str:
        if not self.is_configured():
            raise KiteAuthError(
                "Kite is not configured. Set KITE_API_KEY and KITE_API_SECRET on the server."
            )

        self._discard_expired_states()
        state = secrets.token_urlsafe(32)
        self._pending_states[state] = time.time() + self.state_ttl_seconds
        redirect_params = urlencode({"state": state})
        return f"{self.login_endpoint}?{urlencode({'v': '3', 'api_key': self.api_key, 'redirect_params': redirect_params})}"

    def validate_state(self, state: Optional[str]) -> None:
        self._discard_expired_states()
        if not state:
            raise KiteAuthError("Missing Kite login state. Start again from /auth/kite/login.")

        expiry = self._pending_states.pop(state, None)
        if expiry is None or expiry < time.time():
            raise KiteAuthError("Invalid or expired Kite login state. Start the login again.")

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
        self._access_token = access_token
        self._session = {
            "authenticated": True,
            "authenticated_at": authenticated_at,
            "user_id": data.get("user_id"),
            "user_name": data.get("user_name"),
        }
        return self.status()

    def status(self) -> Dict[str, Any]:
        return {
            "configured": self.is_configured(),
            "authenticated": bool(self._access_token),
            "authenticated_at": self._session.get("authenticated_at"),
            "user_id": self._session.get("user_id"),
            "requires_daily_login": True,
        }

    def _discard_expired_states(self) -> None:
        now = time.time()
        self._pending_states = {
            state: expiry
            for state, expiry in self._pending_states.items()
            if expiry >= now
        }


kite_auth_service = KiteAuthService()
