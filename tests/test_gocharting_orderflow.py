import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from src.services.gocharting_orderflow_service import (
    GoChartingOrderflowError,
    GoChartingOrderflowService,
)


class GoChartingOrderflowServiceTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(
            os.environ,
            {"GOCHARTING_WEBHOOK_TOKEN": "test-webhook-token"},
            clear=False,
        )
        self.env.start()
        self.service = GoChartingOrderflowService()
        self.now = datetime(2026, 11, 14, 4, 30, tzinfo=timezone.utc)

    def tearDown(self):
        self.env.stop()

    def body(self, **overrides):
        payload = {
            "token": "test-webhook-token",
            "symbol": "NSE:INFY",
            "signal": "BUY",
            "interval": "5m",
            "delta": 42000,
            "delta_percent": 24.5,
            "buy_volume": 120000,
            "sell_volume": 78000,
        }
        payload.update(overrides)
        return json.dumps(payload).encode("utf-8")

    def test_plain_text_json_is_normalized_and_secret_is_not_returned(self):
        signal = self.service.ingest(self.body(), now=self.now)

        self.assertEqual(signal["symbol"], "INFY")
        self.assertEqual(signal["signal"], "BUY")
        self.assertEqual(signal["source"], "GoCharting Premium")
        self.assertNotIn("token", signal)
        self.assertEqual(self.service.get_signals(["INFY"], now=self.now), [signal])

    def test_invalid_token_is_rejected_without_mutating_signals(self):
        with self.assertRaises(GoChartingOrderflowError) as context:
            self.service.ingest(self.body(token="wrong"), now=self.now)

        self.assertEqual(context.exception.status_code, 401)
        self.assertEqual(self.service.get_signals(["INFY"], now=self.now), [])

    def test_signal_expires_at_exact_seven_minute_boundary(self):
        signal = self.service.ingest(self.body(), now=self.now)

        self.assertEqual(
            self.service.get_signals(
                ["INFY"],
                now=self.now + timedelta(seconds=419, milliseconds=999),
            ),
            [signal],
        )
        self.assertEqual(
            self.service.get_signals(
                ["INFY"],
                now=self.now + timedelta(seconds=420),
            ),
            [],
        )
        self.assertEqual(
            self.service.status(now=self.now + timedelta(seconds=420))["active_signal_count"],
            0,
        )

    def test_latest_signal_replaces_previous_symbol_direction(self):
        self.service.ingest(self.body(signal="BUY"), now=self.now)
        replacement = self.service.ingest(
            self.body(signal="SHORT", delta=-36000),
            now=self.now + timedelta(seconds=30),
        )

        self.assertEqual(replacement["signal"], "SELL")
        self.assertEqual(
            self.service.get_signals(["NSE:INFY"], now=self.now + timedelta(seconds=30))[0]["signal"],
            "SELL",
        )

    def test_exchange_and_numeric_validation_rejects_untrusted_payloads(self):
        for overrides in (
            {"symbol": "BSE:INFY"},
            {"symbol": "NASDAQ:AAPL"},
            {"symbol": "NSE:INFY/../../"},
            {"signal": "HOLD"},
            {"delta": float("inf")},
            {"delta_percent": 100.1},
            {"buy_volume": -1},
            {"sell_volume": -1},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(GoChartingOrderflowError):
                    self.service.ingest(self.body(**overrides), now=self.now)

    def test_missing_server_configuration_fails_closed(self):
        with patch.dict(os.environ, {"GOCHARTING_WEBHOOK_TOKEN": ""}, clear=False):
            service = GoChartingOrderflowService()
            with self.assertRaises(GoChartingOrderflowError) as context:
                service.ingest(self.body(), now=self.now)
        self.assertEqual(context.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
