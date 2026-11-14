# GoCharting Premium order-flow setup

The Android app consumes short-lived buy/sell confirmations from GoCharting
Premium. It does not estimate a footprint from candles or Zerodha quote
snapshots.

## Server configuration

Create a random webhook token and store it only in Render as:

```text
GOCHARTING_WEBHOOK_TOKEN=<random secret>
```

The production webhook URL is:

```text
https://stock-monitor-pro.onrender.com/api/orderflow/gocharting/webhook
```

GoCharting sends webhook messages as `text/plain`. Put a JSON object in the
alert's custom Message field. Configure separate BUY and SELL conditions for
each tracked symbol.

BUY example:

```json
{"token":"YOUR_GOCHARTING_WEBHOOK_TOKEN","symbol":"NSE:RELIANCE","signal":"BUY","interval":"5m"}
```

SELL example:

```json
{"token":"YOUR_GOCHARTING_WEBHOOK_TOKEN","symbol":"NSE:RELIANCE","signal":"SELL","interval":"5m"}
```

If GoCharting exposes dynamic values in the custom message, the receiver also
accepts finite `delta`, `delta_percent`, `buy_volume`, and `sell_volume` fields.
They are optional because the current GoCharting webhook documentation does not
promise placeholder expansion in custom messages.

## Recommended GoCharting alert configuration

1. Open the NSE symbol in a saved 5-minute Volume Footprint workspace.
2. Prefer an alert that fires once when the completed bar's aggressive-buy
   delta crosses the chosen positive threshold for BUY.
3. Create the matching negative-delta alert for SELL.
4. Select Webhook delivery, paste the production URL, and paste the appropriate
   JSON message with the exact NSE symbol.
5. Repeat only for stocks being monitored. GoCharting's Premium alert allowance
   determines the maximum simultaneous coverage.

GoCharting's public documentation currently conflicts about whether custom Lipi
indicators can combine `orderflow.*` variables with webhooks. Use the built-in
Delta/Orderflow alert controls when they are present in the Premium account. Do
not enable an undocumented Lipi workaround without verifying it in the account.

## App confirmation rules

- Bullish Matrix + fresh GoCharting BUY alert: `CONFIRMED BUY`
- Bearish Matrix + fresh GoCharting SELL alert: `CONFIRMED SELL`
- Matrix and GoCharting disagree: `FLOW CONFLICT`
- No alert within the server TTL: `AWAITING DATA`

Signals are informational. They never place an order, and a signal is removed
after its TTL or a backend restart.
