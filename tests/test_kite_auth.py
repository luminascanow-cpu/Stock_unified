import hashlib
import os
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from src.services.kite_auth_service import KiteAuthError, KiteAuthService


class FakeResponse:
    status_code = 200

    def json(self):
        return {
            "status": "success",
            "data": {
                "access_token": "private-access-token",
                "user_id": "AB1234",
                "user_name": "Test User",
            },
        }


class FakeClient:
    def __init__(self):
        self.form = None
        self.headers = None

    async def post(self, _url, data, headers):
        self.form = data
        self.headers = headers
        return FakeResponse()


class KiteAuthServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.env = patch.dict(
            os.environ,
            {"KITE_API_KEY": "public-key", "KITE_API_SECRET": "private-secret"},
            clear=False,
        )
        self.env.start()
        self.service = KiteAuthService()

    def tearDown(self):
        self.env.stop()

    def test_login_url_contains_one_time_state(self):
        query = parse_qs(urlparse(self.service.create_login_url()).query)
        self.assertEqual(query["api_key"], ["public-key"])
        self.assertEqual(query["v"], ["3"])

        redirect_params = parse_qs(query["redirect_params"][0])
        state = redirect_params["state"][0]
        self.service.validate_state(state)
        with self.assertRaises(KiteAuthError):
            self.service.validate_state(state)

    def test_checksum_matches_kite_specification(self):
        expected = hashlib.sha256(
            b"public-keyrequest-tokenprivate-secret"
        ).hexdigest()
        self.assertEqual(
            self.service.checksum("public-key", "request-token", "private-secret"),
            expected,
        )

    async def test_exchange_stores_token_without_exposing_it_in_status(self):
        client = FakeClient()
        result = await self.service.exchange_request_token("request-token", client=client)

        self.assertTrue(result["authenticated"])
        self.assertEqual(result["user_id"], "AB1234")
        self.assertNotIn("access_token", result)
        self.assertEqual(self.service.access_token, "private-access-token")
        self.assertEqual(client.headers, {"X-Kite-Version": "3"})
        self.assertNotEqual(client.form["checksum"], "private-secret")

    async def test_token_expires_on_the_next_india_calendar_day(self):
        await self.service.exchange_request_token("request-token", client=FakeClient())
        self.service._session_day = "2000-01-01"

        result = self.service.status()

        self.assertFalse(result["authenticated"])
        self.assertIsNone(result["authenticated_at"])
        self.assertIsNone(result["session_day"])
        self.assertIsNone(self.service.access_token)


if __name__ == "__main__":
    unittest.main()
