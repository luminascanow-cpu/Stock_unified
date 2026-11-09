import fs from "node:fs";

const source = fs.readFileSync(new URL("./generate_standalone_asset.mjs", import.meta.url), "utf8");
const generatedSource = fs.readFileSync(
  new URL("../app/src/main/assets/index.html", import.meta.url),
  "utf8"
);
const nativeSource = fs.readFileSync(
  new URL("../app/src/main/java/com/stockunified/app/MainActivity.java", import.meta.url),
  "utf8"
);
const durableUiDocs = ["DESIGN.md", "UX-CONTRACT.md", "README.md"].map((name) => ({
  name,
  content: fs.readFileSync(new URL(`../${name}`, import.meta.url), "utf8")
}));

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function functionSource(name, nextName) {
  const start = source.indexOf(`    function ${name}(`);
  const end = source.indexOf(`    function ${nextName}(`, start + 1);
  assert(start >= 0 && end > start, `Unable to extract ${name}`);
  return source.slice(start, end).trim();
}

const baseTickerBlock = nativeSource.slice(
  nativeSource.indexOf("private static final String[][] STOCK_TICKERS"),
  nativeSource.indexOf("private static final String[][] MARKET_EVENTS")
);
const baseTickerSymbols = [...baseTickerBlock.matchAll(/\{\"[^\"]+\.NS\", \"([^\"]+)\"\}/g)].map((match) => match[1]);
const sectorGroupBlock = source.slice(
  source.indexOf("const SECTOR_SYMBOL_GROUPS"),
  source.indexOf("const SECTOR_BY_SYMBOL")
);
const mappedSectorSymbols = new Set(
  [...sectorGroupBlock.matchAll(/:\s*\"([^\"]+)\"/g)].flatMap((match) => match[1].split(","))
);
assert(baseTickerSymbols.length > 0, "the base watchlist must remain discoverable by regression checks");
assert(baseTickerSymbols.every((symbol) => mappedSectorSymbols.has(symbol)), "every base-watchlist stock must have a sector classification");

const normalizeCustomSymbol = new Function(
  `${functionSource("normalizeCustomSymbol", "customStockListViewModel")}; return normalizeCustomSymbol;`
)();

assert(normalizeCustomSymbol("ABB.NS") === "ABB", ".NS suffix must normalize to the Matrix symbol");
assert(normalizeCustomSymbol(" policybzr.ns ") === "POLICYBZR", "symbol normalization must trim and uppercase");

const sectorForSymbol = new Function(
  "SECTOR_BY_SYMBOL",
  "normalizeCustomSymbol",
  `${functionSource("sectorForSymbol", "buildSectorFlow")}; return sectorForSymbol;`
)(new Map([["HDFCBANK", "BANKS"]]), normalizeCustomSymbol);
assert(sectorForSymbol("hdfcbank.ns") === "BANKS", "sector lookup must normalize NSE symbols");

const buildSectorFlow = new Function(
  `
    ${functionSource("normalizeCustomSymbol", "customStockListViewModel")}
    ${functionSource("numberOrNull", "roundClose")}
    const sectorForSymbol = () => "";
    ${functionSource("buildSectorFlow", "formatSectorFlowCrores")}
    return buildSectorFlow;
  `
)();
const sectorFlow = buildSectorFlow([
  {symbol: "HDFCBANK", sector: "BANKS", ltp: 100, change_percent: 1.2, session_volume: 1000000, quote_epoch: 100},
  {symbol: "SBIN", sector: "BANKS", ltp: 200, change_percent: 0.8, session_volume: 500000, quote_epoch: 110},
  {symbol: "TCS", sector: "IT & TELECOM", ltp: 100, change_percent: -1.1, session_volume: 400000, quote_epoch: 105},
  {symbol: "UNKNOWN", ltp: 50, change_percent: 3, session_volume: 200000}
]);
assert(sectorFlow.flowCount === 3 && sectorFlow.totalCount === 4, "sector flow must expose classified volume coverage");
assert(sectorFlow.advancers === 2 && sectorFlow.decliners === 1, "sector flow must report classified watchlist breadth");
assert(sectorFlow.inflow === 200000000 && sectorFlow.outflow === 40000000, "sector flow must aggregate directional traded value");
assert(sectorFlow.inflowSectors[0].sector === "BANKS", "sector flow must rank the strongest estimated inflow first");
assert(sectorFlow.outflowSectors[0].sector === "IT & TELECOM", "sector flow must rank the strongest estimated outflow first");
assert(sectorFlow.allSectors[0].grossTurnover === 200000000, "sector map sizing must use gross estimated turnover");
assert(sectorFlow.allSectors[0].weightedChange === 1, "sector map colour must use turnover-weighted percentage change");
assert(buildSectorFlow([{symbol: "HDFCBANK", sector: "BANKS", ltp: 100, change_percent: 1}]).flowCount === 0, "missing session volume must not fabricate sector flow");
const currentSessionNow = Date.parse("2026-11-07T10:00:00+05:30");
const staleOpenFlow = buildSectorFlow([{
  symbol: "HDFCBANK",
  sector: "BANKS",
  ltp: 100,
  change_percent: 1,
  session_volume: 1000,
  quote_epoch: Date.parse("2026-11-06T15:30:00+05:30") / 1000
}], {marketOpen: true, now: currentSessionNow});
assert(staleOpenFlow.flowCount === 0 && staleOpenFlow.staleFlowCount === 1, "open-trade flow must exclude previous-session turnover");
const directionalLeaderFlow = buildSectorFlow([
  {symbol: "HDFCBANK", sector: "BANKS", ltp: 100, change_percent: 1, session_volume: 100, quote_epoch: 100},
  {symbol: "SBIN", sector: "BANKS", ltp: 100, change_percent: -1, session_volume: 1000, quote_epoch: 100}
]);
assert(directionalLeaderFlow.sectors[0].leader.symbol === "SBIN", "sector leaders must match the sector net-flow direction");

const buildSectorTreemap = new Function(
  `${functionSource("buildSectorTreemap", "renderSectorMap")}; return buildSectorTreemap;`
)();
const sectorTreemap = buildSectorTreemap([
  {sector: "BANKS", grossTurnover: 75},
  {sector: "IT & TELECOM", grossTurnover: 25}
]);
const treemapArea = sectorTreemap.reduce((sum, rect) => sum + rect.width * rect.height, 0);
assert(Math.abs(treemapArea - 10000) < 0.001, "sector treemap must fill its complete plotting area");
assert(Math.abs(sectorTreemap[0].width * sectorTreemap[0].height - 7500) < 0.001, "sector treemap tile area must be proportional to turnover");

const indiaVixRegime = new Function(
  `${functionSource("numberOrNull", "roundClose")}; ${functionSource("indiaVixRegime", "renderMacro")}; return indiaVixRegime;`
)();
assert(indiaVixRegime(11.9).label === "CALM", "sub-12 India VIX must be labelled calm");
assert(indiaVixRegime(17.66).label === "NORMAL", "India VIX below 18 must be labelled normal");
assert(indiaVixRegime(22).label === "ELEVATED" && indiaVixRegime(28).label === "HIGH", "higher India VIX regimes must be explicit");

const customStockListViewModel = new Function(
  `${functionSource("customStockListViewModel", "knownMatrixSymbols")}; return customStockListViewModel;`
)();
const collapsedCustomStocks = customStockListViewModel(["ABB", "TCS"], false);
assert(collapsedCustomStocks.count === 2, "collapsed custom stocks must remain active in the watchlist");
assert(collapsedCustomStocks.isExpanded === false, "the custom-stock list must default to collapsed");
assert(collapsedCustomStocks.summary === "2 custom stocks active", "the collapsed list must retain a compact active count");
assert(customStockListViewModel([], true).isExpanded === false, "an empty custom-stock list cannot remain expanded");

const safeExternalUrl = new Function(
  `${functionSource("safeExternalUrl", "showCollecting")}; return safeExternalUrl;`
)();
assert(safeExternalUrl("https://example.com/report").startsWith("https://"), "HTTPS article links must remain usable");
assert(safeExternalUrl("javascript:alert(1)") === "#", "executable URL schemes must be rejected");

const istDayKey = new Function(
  `${functionSource("istDayKey", "readKitePromptDay")}; return istDayKey;`
)();
assert(
  istDayKey(new Date("2026-11-09T19:00:00.000Z")) === "2026-11-10",
  "daily Kite prompts must use the India calendar day"
);

const mergeTechnicalRows = new Function(
  `
    ${functionSource("normalizeCustomSymbol", "knownMatrixSymbols")}
    let currentMatrixRows = [{symbol: "TCS", rsi: 48, ltp: 100, change_percent: 1, session_volume: 1000, turnover_estimate: 100000, quote_epoch: 100, technical_updated_at: "2026-09-29T09:00:00+05:30"}];
    ${functionSource("mergeTechnicalRows", "mergePartialAlerts")}
    return mergeTechnicalRows;
  `
)();
const partialCoverage = mergeTechnicalRows(
  [{symbol: "ABB", rsi: 52, ltp: 210}],
  {
    watchlist_symbols: ["ABB", "TCS", "NEWAPP"],
    watchlist_quotes: [
      {symbol: "TCS", ltp: 105, quote_timestamp: "2026-09-29T09:30:00+05:30"},
      {symbol: "NEWAPP", ltp: 75, quote_timestamp: "2026-09-29T09:30:00+05:30"}
    ],
    technical_updated_at: "2026-09-29T09:30:00+05:30"
  }
);
const retainedTcs = partialCoverage.rows.find((row) => row.symbol === "TCS");
const quoteOnly = partialCoverage.rows.find((row) => row.symbol === "NEWAPP");
assert(partialCoverage.rows.length === 3, "partial scans must retain every active watchlist symbol");
assert(retainedTcs.technical_stale === true && retainedTcs.rsi === 48, "partial scans must keep the last valid technical values");
assert(retainedTcs.ltp === 105, "retained technical rows must still receive the latest quote");
assert(retainedTcs.session_volume === undefined && retainedTcs.turnover_estimate === undefined, "fresh price-only quotes must clear inherited flow fields");
assert(quoteOnly.technical_unavailable === true && quoteOnly.ltp === 75, "quote-only symbols must remain visible with missing technical state");
const restoredQuoteOnly = mergeTechnicalRows(
  [{symbol: "NEWAPP", ltp: 75, technical_unavailable: true}],
  {watchlist_symbols: ["NEWAPP"], watchlist_quotes: []},
  {fromCache: true}
).rows[0];
assert(restoredQuoteOnly.technical_unavailable === true, "restoring a saved quote-only row must preserve its NO TECH state");

const mergePartialAlerts = new Function(
  `${functionSource("normalizeCustomSymbol", "customStockListViewModel")}; ${functionSource("mergePartialAlerts", "numberOrNull")}; return mergePartialAlerts;`
)();
const mergedAlerts = mergePartialAlerts(
  [{category: "technical", symbol: "ABB", title: "ABB SELL"}],
  [{category: "technical", symbol: "TCS", title: "TCS SELL"}],
  ["ABB"]
);
assert(mergedAlerts.length === 2, "partial scans must preserve previous alerts for unfinished symbols");
const reconciledAlerts = mergePartialAlerts(
  [{category: "technical", symbol: "TCS", title: "TCS BUY"}],
  [{category: "technical", symbol: "TCS", title: "TCS SELL"}],
  ["TCS"]
);
assert(reconciledAlerts.length === 1 && reconciledAlerts[0].title === "TCS BUY", "fresh symbols must supersede contradictory saved alerts");

const mergeIntelItems = new Function(
  `${functionSource("normalizeCustomSymbol", "customStockListViewModel")}; ${functionSource("mergeIntelItems", "refreshIntelFromMatrix")}; return mergeIntelItems;`
)();
const mergedNews = mergeIntelItems(
  [{symbol: "ABB", title: "Fresh ABB"}],
  [{symbol: "ABB", title: "Old ABB"}, {symbol: "TCS", title: "Saved TCS"}],
  ["ABB"],
  (item) => item.title
);
assert(mergedNews.length === 2 && mergedNews[0].title === "Fresh ABB", "partial news must replace completed symbols and retain unfinished symbols");
assert(mergedNews[1].title === "Saved TCS" && mergedNews[1].stale === true, "retained partial-news rows must be marked saved");

const closeHelpers = [
  functionSource("roundClose", "loadDailyCloseBook"),
  functionSource("sourcePriority", "upsertDailyClose"),
  functionSource("upsertDailyClose", "getIstParts")
].join("\n");
const upsertDailyClose = new Function(
  `const CLOSE_HISTORY_LIMIT = 45; ${closeHelpers}; return upsertDailyClose;`
)();

const snapshotStore = new Map();
const snapshotHelpers = [
  functionSource("loadLastSuccessfulSnapshot", "saveLastSuccessfulSnapshot"),
  functionSource("saveLastSuccessfulSnapshot", "restoreLastSuccessfulSnapshot")
].join("\n");
const snapshotApi = new Function(
  "storage",
  `
    const localStorage = {
      getItem: (key) => storage.has(key) ? storage.get(key) : null,
      setItem: (key, value) => storage.set(key, value)
    };
    const LAST_SUCCESSFUL_SNAPSHOT_KEY = "stockUnifiedLastSuccessfulSnapshotV1";
    const SNAPSHOT_VERSION = 1;
    let currentDashboard = {alerts: [{title: "Previous alert"}]};
    let currentMacro = {usd_inr: {value: 83}};
    let currentMarketStatus = {is_open: true};
    let latestNewsActions = [{symbol: "ABB"}];
    let latestIntelNews = [{symbol: "ABB", title: "Saved headline"}];
    let lastSuccessfulSyncAt = 123456;
    ${snapshotHelpers}
    return {loadLastSuccessfulSnapshot, saveLastSuccessfulSnapshot};
  `
)(snapshotStore);
snapshotApi.saveLastSuccessfulSnapshot();
const restoredSnapshot = snapshotApi.loadLastSuccessfulSnapshot();
assert(restoredSnapshot.dashboard.alerts[0].title === "Previous alert", "saved dashboard alerts must restore intact");
assert(restoredSnapshot.newsActions[0].symbol === "ABB", "saved news alerts must restore intact");
assert(restoredSnapshot.intelNews[0].title === "Saved headline", "saved headlines must restore intact");
assert(restoredSnapshot.savedAt === 123456, "saved snapshot must retain its successful sync time");

const book = {
  stocks: {
    ABB: [{date: "2026-09-25", close: 100, source: "post_close_quote"}]
  }
};
const replaced = upsertDailyClose(book, "ABB", {
  date: "2026-09-25",
  close: 98,
  source: "derived_previous_close"
});
assert(replaced === false, "a derived close must not replace a post-close quote");
assert(book.stocks.ABB[0].close === 100, "authoritative close value must remain intact");

const streakHelpers = [
  functionSource("utcDateFromYmd", "ymdFromUtcDate"),
  functionSource("ymdFromUtcDate", "isWeekday"),
  functionSource("previousTradingDate", "rowQuoteDate"),
  functionSource("consecutiveFallingMoves", "liveClosePoint")
].join("\n");
const consecutiveFallingMoves = new Function(
  `${streakHelpers}; return consecutiveFallingMoves;`
)();
assert(consecutiveFallingMoves([
  {date: "2026-09-25", close: 100},
  {date: "2026-09-28", close: 99},
  {date: "2026-09-29", close: 98}
]) === 2, "Friday-to-Monday close weakness must remain consecutive");
assert(consecutiveFallingMoves([
  {date: "2026-09-25", close: 100},
  {date: "2026-09-29", close: 98}
]) === 0, "a missing weekday session must break the close weakness streak");
assert(consecutiveFallingMoves([
  {date: "2026-09-25", close: 100, source: "yahoo_adjusted_daily_close"},
  {date: "2026-09-29", close: 98, source: "yahoo_adjusted_daily_close"}
]) === 1, "Yahoo's authoritative session sequence must preserve exchange-holiday continuity");

assert(!source.includes("fallbackRows"), "live Matrix must not contain demonstration-price fallbacks");
assert(!source.includes("Setup probability"), "heuristic scores must not be labeled as probabilities");
assert(source.includes("window.StockBridge.requestJson"), "the WebView must use the asynchronous native request bridge");
assert(!source.includes("window.StockBridge[method]"), "synchronous dynamic bridge calls must not return");
assert(source.includes("stockUnifiedLastSuccessfulSnapshotV1"), "the last successful dashboard must persist across app launches");
assert(source.includes("restoreLastSuccessfulSnapshot();"), "saved alerts must render before the first live refresh completes");
assert(source.includes("MARKET_OPEN_REFRESH_MS = 30000"), "market-open refresh must use the efficient 30-second cadence");
assert(source.includes("MARKET_CLOSED_REFRESH_MS = 300000"), "market-closed refresh must back off to five minutes");
assert(!source.includes("setInterval(syncOnce"), "live sync must use adaptive scheduling instead of a fixed interval");
assert(!source.includes("falling.slice(0, 6)"), "close weakness must not cap the displayed watchlist");
assert(source.includes('data-close-symbol="'), "close weakness stocks must expose detail navigation controls");
assert(source.includes('openStockDetail(button.dataset.closeSymbol)'), "close weakness controls must open the stock Lens");
assert(source.includes("buildFallingCloseSynthesis(closeWatchlistRows())"), "close weakness must use the full watchlist merge");
assert(source.includes("base_watchlist_symbols"), "close weakness must distinguish the base universe from removable custom stocks");
assert(source.includes("requestId !== detailRequestSeq"), "stale Lens responses must not replace the latest selected stock");
assert(source.includes("requestedCustomStocksKey === JSON.stringify(customStocks)"), "stale dashboard responses must not restore removed custom stocks");
assert(source.includes('aria-controls="customStockChips"'), "custom stocks must have an accessible management disclosure");
assert(source.includes('id="stockInputClear"'), "the ticker search must expose an app-owned clear control");
assert(source.includes('<label class="visually-hidden" for="stockInput">'), "the ticker input must retain a real accessible label");
assert(source.includes("stockInput.value = \"\";\n          updateStockInputClearButton();\n          collapseCustomStockList();"), "a successful stock search must clear the input and collapse the custom-stock list");
assert(source.includes("saveCustomStocks();\n      collapseCustomStockList();"), "web-discovered stocks must also collapse the custom-stock list after addition");
assert(source.includes('class="row-open-button"'), "Matrix stock rows must expose a native keyboard-accessible detail button");
assert(source.includes("openStockDetail(button.dataset.openSymbol)"), "Matrix detail buttons must open the selected stock");
assert(!source.includes('source: "derived_previous_close"'), "the close ledger must not fabricate previous-session dates across exchange holidays");
assert(source.includes("!yahooSequence && previousTradingDate(current.date) !== previous.date"), "locally captured close streaks must break across missing weekday sessions");
assert(source.includes('callNativeAsync("getDailyCloseHistoryJsonForSymbols"'), "the full watchlist must recover daily close history from the native engine");
assert(source.includes("mergeTechnicalRows(predictions, data, options)"), "partial scans must retain the last valid Matrix rows");
assert(source.includes('"INSUFFICIENT DATA"'), "empty breadth must not be labeled bearish");
assert(nativeSource.includes('root.put("watchlist_symbols", watchlistSymbols)'), "native dashboard must expose the full watchlist universe");
assert(nativeSource.includes('root.put("base_watchlist_symbols", baseWatchlistSymbols)'), "native dashboard must expose the immutable base watchlist");
assert(nativeSource.includes('root.put("watchlist_quotes", watchlistQuotes)'), "native dashboard must expose quotes for the full watchlist");
assert(nativeSource.includes('case "getDailyCloseHistoryJsonForSymbols"'), "the native bridge must serve adjusted daily close history");
assert(nativeSource.includes('fetchSeries(yahooSymbol, "3mo", "1d")'), "daily close recovery must request sufficient history");
assert(nativeSource.includes('root.put("technical_complete", rows.size() == submitted)'), "native scans must expose partial completion explicitly");
assert(nativeSource.includes('root.put("error", message == null'), "failed dashboard refreshes must reject instead of replacing saved alerts");
assert(nativeSource.includes('.put("error", e.getMessage() == null'), "failed news refreshes must preserve saved news alerts");
assert(nativeSource.includes('private final Map<String, String> symbolNewsCache'), "news caching must be isolated per stock");
assert(nativeSource.includes('root.put("news_status", fetchResult.optString'), "native news responses must distinguish complete, partial, and failed scans");
assert(!nativeSource.includes('String originalUrl = resolveOriginalArticleUrl(articleUrl);'), "article redirects must not block headline display");
assert(!nativeSource.includes('return prediction;'), "neutral headlines must not inherit the stock technical direction");
assert(nativeSource.includes('article.put("is_breaking", containsAny('), "breaking-news classification must come from headline content");
assert(source.includes('"Update delayed · showing saved news"'), "news failures must retain visible saved headlines");
assert(source.includes('id="niftyPreviousClose"'), "Home must expose the previous close as a dedicated value");
assert(source.includes('id="niftySessionMove"'), "Home must expose the full day move as a dedicated value");
assert(source.includes('id="sectorFlowTitle">SECTORS IN FOCUS'), "Home must expose the sectors-in-focus panel");
assert(source.includes('id="kiteSessionTitle">Broker session'), "Home must reserve a stable Kite session card");
assert(source.includes('id="kiteAuthDialog" role="dialog" aria-modal="true"'), "daily Kite login must use an app-owned accessible dialog");
assert(source.includes('KITE_PROMPT_DAY_KEY = "stockUnifiedKitePromptDayV1"'), "the daily Kite prompt must persist only its last India calendar day");
assert(source.includes('checkKiteSession({offerDailyPrompt: true});\n        syncOnce();'), "returning from Zerodha login must recheck Kite before market sync");
assert(source.includes("Yahoo Finance remains active while Kite is disconnected"), "the daily login dialog must name the non-blocking fallback");
assert(!source.includes('type="password"'), "the Android asset must never request a broker password or API secret");
assert(!source.includes("KITE_API_SECRET"), "the Kite API secret must remain server-side");
const removedMoneyRotationMarkers = [
  "money rotation",
  "money-rotation",
  "moneyrotation",
  "rendermoneyrotation",
  "rotation-legend",
  "rotation-flow",
  "rotation-net",
  "flow-net"
];
[
  {name: "canonical generator", content: source},
  {name: "generated Android asset", content: generatedSource},
  ...durableUiDocs
].forEach(({name, content}) => {
  const normalized = content.toLowerCase();
  assert(
    removedMoneyRotationMarkers.every((marker) => !normalized.includes(marker)),
    `${name} must not contain remnants of the removed Money Rotation feature`
  );
});
assert(source.includes('id="sectorMapTitle">Sector map'), "Home must expose the turnover-sized sector map");
assert(source.includes('id="vixValue">--'), "Home must expose India VIX in the macro strip");
assert(source.includes("Estimated directional turnover = current price × session volume"), "sector flow must disclose its estimation method");
assert(source.includes("This is not exchange order-flow, FII/DII flow"), "sector flow must not be presented as institutional order flow");
assert(nativeSource.includes('quote.put("session_volume", snapshot.volume)'), "watchlist quotes must expose cumulative session volume");
assert(nativeSource.includes('row.put("session_volume", snapshot.volume)'), "technical rows must receive session-volume coverage");
assert(nativeSource.includes('intradayVolume(response)'), "Yahoo spark quotes must recover cumulative intraday volume");
assert(nativeSource.includes('item.optLong("regularMarketVolume", 0L)'), "legacy Yahoo quotes must retain regular-market volume");
assert(nativeSource.includes('symbols.add("^INDIAVIX")'), "macro quotes must request the Yahoo India VIX symbol");
assert(nativeSource.includes('root.put("india_vix", buildQuoteJsonSafe('), "macro payload must expose India VIX without coupling its failure to other macro cards");
assert(nativeSource.includes('quote.put("available", false)'), "individual macro failures must render as unavailable instead of failing the full macro batch");
assert(source.includes(".falling-prices"), "multi-day alerts must show current price and last close in dedicated fields");
assert(source.includes("grid-template-columns: repeat(2, minmax(0, 1fr));\n      border-top"), "mobile trade levels must wrap into readable columns");
assert(nativeSource.includes("WindowInsets.Type.statusBars()"), "the Android shell must keep content below the status bar");

console.log("Regression checks passed");
