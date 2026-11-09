# Confluence Terminal UX Contract

## Product context

- Audience: Indian-market traders using an Android phone for repeated market checks.
- Primary jobs: scan the watchlist, inspect live/technical signals, review alerts, and open one stock in Lens for detail.
- Locale and time: English (`en-IN`) with Asia/Kolkata market time.
- Accessibility target: WCAG 2.2 AA.

## Sources and visual ownership

- Market-data and watchlist contract: `app/src/main/java/com/stockunified/app/MainActivity.java`.
- UI behavior and generated asset source: `tools/generate_standalone_asset.mjs`.
- Visual contract: `DESIGN.md`; its values mirror the canonical generator CSS variables.
- Generated `app/src/main/assets/index.html` is an output and is not edited directly.

## Canonical navigation and list behavior

- Matrix rows and multi-day close-weakness rows share `openStockDetail(symbol)` as the canonical stock-to-Lens transition.
- The close ledger scans the complete active watchlist universe returned by the native bridge, merges app-added custom symbols, and excludes stocks explicitly removed/hidden by the user.
- The weakness card renders every qualifying stock; it does not silently cap the list.
- A close-weakness entry is a native button with a visible `OPEN LENS` affordance, accessible name, hover, focus-visible, and pressed states.
- Native Back returns from Lens to Matrix, matching the established Android detail flow.
- Custom stocks remain active after addition, but their removable chip list is collapsed by default and after every successful manual or discovery add. A semantic `Manage` disclosure exposes the full list, reports `aria-expanded`, and keeps the active count visible while collapsed.

## Async and stale-data behavior

- Background refresh preserves the last successful dashboard and alerts until a newer successful response arrives.
- Failed quote or news work must not replace usable content with an empty payload.
- A partially completed technical scan merges its returned rows into the last usable Matrix. Unfinished symbols retain saved indicators with an explicit label; symbols with only a quote remain visible with `NO TECH`.
- The native dashboard supplies both `watchlist_symbols` and `watchlist_quotes`; technical Matrix completion does not define close-ledger membership.
- The native bridge recovers up to 45 adjusted daily closes for every active watchlist symbol. Yahoo's returned daily sequence defines exchange-session continuity, including holidays; locally captured closes remain conservative across unknown gaps.
- Coverage and freshness are textual: the Matrix reports available versus total technical rows, saved rows, technical update age, quote age, and close-history coverage. Empty breadth is `INSUFFICIENT DATA`, never a bearish percentage.
- Home `Sectors in Focus` covers the active classified watchlist, including available app-added symbols only when a maintained sector classification exists. It estimates directional turnover from current price × cumulative session volume, assigned by price direction; it must be labeled as an estimate and never as exchange order-flow, FII/DII flow, or guaranteed buying/selling.
- During market hours the panel is labeled `OPEN TRADE` only when at least one complete current-session price/change/volume/timestamp tuple contributes; otherwise it is `AWAITING LIVE`. Outside market hours it is `LAST SESSION`, and restored snapshots are `SAVED`. A fresh price-only quote atomically clears inherited flow fields, and older-session tuples are excluded while the market is open. Failed or partial quote refreshes preserve usable rows and expose flow coverage plus contributing-quote freshness. Missing volume produces an explicit unavailable state rather than fabricated flow.
- Sector Map visualizes that eligible flow dataset. Tile area is proportional to estimated turnover and colour represents turnover-weighted percentage change; it retains textual coverage, freshness, and empty states.
- India VIX is supplied by the macro quote batch as `^INDIAVIX`, displays value, percentage change, quote time, and a threshold-based volatility regime. The approximate one-day move is `VIX / √252`; it is contextual volatility, not a forecasted market direction.

## Verification

- Static regression: `node tools/verify_regressions.mjs`.
- Asset generation: `node tools/generate_standalone_asset.mjs`.
- Android compile/build: `./gradlew testDebugUnitTest` and `./gradlew assembleDebug`.
- Browser matrix: Alerts → Close at a narrow mobile viewport; activate a weakness row by touch/click and keyboard, then verify the matching Lens symbol opens.
