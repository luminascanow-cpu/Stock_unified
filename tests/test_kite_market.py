import os
import unittest
from unittest.mock import patch

from src.services.kite_auth_service import KiteAuthService
from src.services.kite_market_service import KiteMarketError, KiteMarketService


class FakeQuoteResponse:
    status_code = 200

    def json(self):
        return {
            "status": "success",
            "data": {
                "NSE:INFY": {
                    "instrument_token": 408065,
                    "timestamp": "2026-11-10 15:30:00",
                    "last_price": 1412.95,
                    "volume": 7360198,
                    "ohlc": {
                        "open": 1396,
                        "high": 1421.75,
                        "low": 1395.55,
                        "close": 1389.65,
                    },
                }
            },
        }


class FakeQuoteClient:
    def __init__(self):
        self.params = None
        self.headers = None

    async def get(self, _url, params, headers):
        self.params = params
        self.headers = headers
        return FakeQuoteResponse()


class UnauthorizedResponse:
    status_code = 401

    def json(self):
        raise AssertionError("401 responses must be handled before JSON parsing")


class UnauthorizedClient:
    async def get(self, _url, params, headers):
        return UnauthorizedResponse()


class ReloginDuringRequestClient:
    def __init__(self, auth):
        self.auth = auth

    async def get(self, _url, params, headers):
        self.auth._access_token = "new-token"
        self.auth._session_day = self.auth._today_in_india()
        return UnauthorizedResponse()


class PartialQuoteResponse:
    status_code = 200

    def json(self):
        payload = FakeQuoteResponse().json()
        payload["data"]["NSE:INFY"].pop("volume")
        return payload


class PartialQuoteClient:
    async def get(self, _url, params, headers):
        return PartialQuoteResponse()


class InvalidQuoteClient:
    def __init__(self, field, value):
        self.field = field
        self.value = value

    async def get(self, _url, params, headers):
        payload = FakeQuoteResponse().json()
        quote = payload["data"]["NSE:INFY"]
        if self.field == "previous_close":
            quote["ohlc"]["close"] = self.value
        else:
            quote[self.field] = self.value

        class Response:
            status_code = 200

            def json(self_inner):
                return payload

        return Response()


class KiteMarketServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.env = patch.dict(
            os.environ,
            {"KITE_API_KEY": "public-key", "KITE_API_SECRET": "private-secret"},
            clear=False,
        )
        self.env.start()
        self.auth = KiteAuthService()
        self.market = KiteMarketService(self.auth)

    def tearDown(self):
        self.env.stop()

    async def test_quotes_require_daily_login(self):
        with self.assertRaises(KiteMarketError) as context:
            await self.market.get_quotes(["INFY"])
        self.assertEqual(context.exception.status_code, 401)

    async def test_full_quote_is_normalized_for_sector_flow(self):
        self.auth._access_token = "daily-token"
        self.auth._session_day = self.auth._today_in_india()
        client = FakeQuoteClient()

        result = await self.market.get_quotes([" infy.ns ", "INFY"], client=client)

        self.assertEqual(result["requested_count"], 1)
        self.assertEqual(result["quote_count"], 1)
        quote = result["quotes"][0]
        self.assertEqual(quote["symbol"], "INFY")
        self.assertEqual(quote["session_volume"], 7360198)
        self.assertEqual(quote["quote_source"], "Zerodha Kite")
        self.assertEqual(quote["quote_timestamp"], "2026-11-10T15:30:00+05:30")
        self.assertEqual(quote["quote_time"], "15:30:00")
        self.assertAlmostEqual(quote["change"], 23.3)
        self.assertAlmostEqual(quote["change_percent"], 1.6767)
        self.assertGreater(quote["turnover_estimate"], 0)
        self.assertEqual(client.params, [("i", "NSE:INFY")])
        self.assertEqual(
            client.headers["Authorization"],
            "token public-key:daily-token",
        )

    def test_symbol_validation_blocks_exchange_injection(self):
        with self.assertRaises(KiteMarketError) as context:
            self.market.normalize_symbols(["NSE:INFY"])
        self.assertEqual(context.exception.status_code, 400)

    def test_symbol_limit_accepts_250_and_rejects_251(self):
        symbols = [f"S{index}" for index in range(251)]
        self.assertEqual(len(self.market.normalize_symbols(symbols[:250])), 250)
        with self.assertRaises(KiteMarketError) as context:
            self.market.normalize_symbols(symbols)
        self.assertEqual(context.exception.status_code, 400)

    async def test_partial_quote_tuple_is_reported_missing(self):
        self.auth._access_token = "daily-token"
        self.auth._session_day = self.auth._today_in_india()

        result = await self.market.get_quotes(["INFY"], client=PartialQuoteClient())

        self.assertEqual(result["quote_count"], 0)
        self.assertEqual(result["missing_symbols"], ["INFY"])

    async def test_zero_or_non_finite_prices_are_reported_missing(self):
        self.auth._access_token = "daily-token"
        self.auth._session_day = self.auth._today_in_india()

        for client in (
            InvalidQuoteClient("previous_close", 0),
            InvalidQuoteClient("last_price", float("inf")),
        ):
            with self.subTest(client=client.field):
                result = await self.market.get_quotes(["INFY"], client=client)
                self.assertEqual(result["quote_count"], 0)
                self.assertEqual(result["missing_symbols"], ["INFY"])

    async def test_non_json_unauthorized_response_clears_matching_session(self):
        self.auth._access_token = "daily-token"
        self.auth._session_day = self.auth._today_in_india()

        with self.assertRaises(KiteMarketError) as context:
            await self.market.get_quotes(["INFY"], client=UnauthorizedClient())

        self.assertEqual(context.exception.status_code, 401)
        self.assertIsNone(self.auth.access_token)

    async def test_late_unauthorized_response_preserves_new_login(self):
        self.auth._access_token = "old-token"
        self.auth._session_day = self.auth._today_in_india()

        with self.assertRaises(KiteMarketError):
            await self.market.get_quotes(
                ["INFY"],
                client=ReloginDuringRequestClient(self.auth),
            )

        self.assertEqual(self.auth.access_token, "new-token")


if __name__ == "__main__":
    unittest.main()
