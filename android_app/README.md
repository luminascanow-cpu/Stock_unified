# Stock Unified Android App

This Android app packages the Confluence Terminal mobile UI as bundled WebView assets.
It opens without a local backend or localhost server.

## Standalone Mode

The debug build opens:

```text
file:///android_asset/index.html
```

The bundled HTML is a self-contained mobile UI based on the Stitch export at
`/Users/dipanudas/Downloads/stitch_web_to_mobile_app_design 2`. It includes
Home, Matrix, Intel, and Alerts tabs. On launch, it immediately syncs Yahoo
Finance market data through the native Android bridge and computes lightweight
technical signals on-device. No broker API key, hosted backend, or localhost
server is required on the phone.

The last successful dashboard, including alerts and news-action cards, is kept
in WebView storage and restored before a new sync starts. A refresh never clears
the visible snapshot; it is replaced only after a successful dashboard response.
Live syncing runs every 30 seconds while the market is open, every 5 minutes
while it is closed, retries after 60 seconds on failure, and refreshes immediately
when the app returns to the foreground.

The multi-day close ledger uses the full active watchlist quote feed, including
stocks added by the app's discovery flow. It lists every qualifying weakness
signal without a display cap; selecting a stock opens its existing Lens detail.
For each active symbol, the native bridge recovers up to 45 adjusted Yahoo daily
closes and persists them in WebView storage. Recovery is cached for six hours and
returns partial coverage safely when individual symbols or the network fail.

Technical scans also report their requested and completed coverage. A partial
scan merges fresh rows into the last valid Matrix instead of removing unfinished
stocks. Saved technical rows, missing indicators, quote age, close-history
coverage, and the age of the last usable update are labeled in the interface.

The Matrix keeps app-added stocks active without leaving the full removable-chip
list open. After a successful manual add, the ticker input clears; both manual
and discovery additions collapse the list to a compact active count. `Manage`
reopens it when a stock needs to be removed.

Home includes `Sectors in Focus`, a watchlist-scoped rotation estimate for the
open trade. It aggregates current price × cumulative session volume by maintained
sector classification, shows inflow/outflow, breadth, coverage, freshness, and
top stock links, and switches to `LAST SESSION` after market close. It is a
directional-turnover estimate, not exchange order-flow or FII/DII flow.
The same eligible rows drive a turnover-sized, price-change-coloured sector map.
The macro strip also includes India VIX with
change, regime, timestamp, and the standard `VIX / √252` one-day move context.

Regenerate the bundled WebView asset before rebuilding:

```bash
node tools/generate_standalone_asset.mjs
./gradlew assembleDebug
```

## Build

```bash
./gradlew assembleDebug
```

The debug APK is generated at:

```text
app/build/outputs/apk/debug/app-debug.apk
```
