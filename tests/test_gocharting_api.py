import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.main import app
from src.services.gocharting_orderflow_service import gocharting_orderflow_service


class GoChartingOrderflowApiTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(
            os.environ,
            {
                "GOCHARTING_WEBHOOK_TOKEN": "api-test-token",
            },
            clear=False,
        )
        self.env.start()
        gocharting_orderflow_service._signals.clear()
        gocharting_orderflow_service._last_received_at = None
        self.client = TestClient(app)

    def tearDown(self):
        gocharting_orderflow_service._signals.clear()
        gocharting_orderflow_service._last_received_at = None
        self.env.stop()

    def test_plain_text_webhook_reaches_public_fresh_signal_feed(self):
        webhook = self.client.post(
            "/api/orderflow/gocharting/webhook",
            content='{"token":"api-test-token","symbol":"NSE:RELIANCE","signal":"BUY","interval":"5m"}',
            headers={"Content-Type": "text/plain"},
        )
        self.assertEqual(webhook.status_code, 200)
        self.assertNotIn("token", webhook.json()["signal"])

        feed = self.client.get("/api/orderflow/signals?symbols=RELIANCE,TCS")
        self.assertEqual(feed.status_code, 200)
        self.assertTrue(feed.json()["configured"])
        self.assertEqual(feed.json()["requested_count"], 2)
        self.assertEqual(feed.json()["signals"][0]["symbol"], "RELIANCE")

    def test_invalid_webhook_secret_returns_401_without_signal(self):
        webhook = self.client.post(
            "/api/orderflow/gocharting/webhook",
            content='{"token":"wrong","symbol":"NSE:RELIANCE","signal":"BUY"}',
            headers={"Content-Type": "text/plain"},
        )
        self.assertEqual(webhook.status_code, 401)

        feed = self.client.get("/api/orderflow/signals?symbols=RELIANCE")
        self.assertEqual(feed.json()["signals"], [])

    def test_oversized_webhook_is_rejected_before_json_parsing(self):
        webhook = self.client.post(
            "/api/orderflow/gocharting/webhook",
            content=b"x" * (gocharting_orderflow_service.max_body_bytes + 1),
            headers={"Content-Type": "text/plain"},
        )
        self.assertEqual(webhook.status_code, 413)


if __name__ == "__main__":
    unittest.main()
