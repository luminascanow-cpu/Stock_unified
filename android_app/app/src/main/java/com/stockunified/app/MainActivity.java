package com.stockunified.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowInsets;
import android.webkit.WebChromeClient;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.StringReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TimeZone;
import java.util.concurrent.CompletionService;
import java.util.concurrent.ExecutorCompletionService;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import javax.xml.parsers.DocumentBuilderFactory;

public class MainActivity extends Activity {
    private static final long TECHNICAL_CACHE_MS = 180_000L;
    private static final long QUOTE_CACHE_MS = 15_000L;
    private static final long MACRO_CACHE_MS = 15_000L;
    private static final long INTEL_CACHE_MS = 60_000L;
    private static final long DISCOVERY_CACHE_MS = 300_000L;
    private static final long DETAIL_CACHE_MS = 60_000L;
    private static final long DAILY_HISTORY_CACHE_MS = 6L * 60L * 60L * 1000L;
    private static final int DASHBOARD_SCAN_THREADS = 6;
    private static final int DASHBOARD_TOTAL_WAIT_MS = 24_000;
    private static final int DAILY_HISTORY_SCAN_THREADS = 6;
    private static final int DAILY_HISTORY_TOTAL_WAIT_MS = 36_000;
    private static final int DAILY_HISTORY_LIMIT = 45;
    private static final int QUOTE_BATCH_SIZE = 45;
    private static final int INTEL_SYMBOL_LIMIT = 10;
    private static final int INTEL_ARTICLE_LIMIT = 20;
    private static final int INTEL_NEWS_TIMEOUT_MS = 4_000;
    private static final int INTEL_TOTAL_WAIT_MS = 12_000;
    private static final int DISCOVERY_TOTAL_WAIT_MS = 13_000;
    private static final int DISCOVERY_LIMIT = 8;
    private static final int RSI_PERIOD = 14;
    private static final String[][] STOCK_TICKERS = {
            {"BEL.NS", "BEL"},
            {"MAZDOCK.NS", "MAZDOCK"},
            {"HAL.NS", "HAL"},
            {"EICHERMOT.NS", "EICHERMOT"},
            {"TVSMOTOR.NS", "TVSMOTOR"},
            {"HEROMOTOCO.NS", "HEROMOTOCO"},
            {"TATAMOTORS.NS", "TATAMOTORS"},
            {"TITAN.NS", "TITAN"},
            {"INDUSINDBK.NS", "INDUSINDBK"},
            {"SAMMAANCAP.NS", "SAMMAANCAP"},
            {"IREDA.NS", "IREDA"},
            {"LXCHEM.NS", "LXCHEM"},
            {"PIDILITIND.NS", "PIDILITIND"},
            {"YASHO.NS", "YASHO"},
            {"BALAMINES.NS", "BALAMINES"},
            {"CLEAN.NS", "CLEAN"},
            {"DEEPAKNTR.NS", "DEEPAKNTR"},
            {"DRREDDY.NS", "DRREDDY"},
            {"GODREJCP.NS", "GODREJCP"},
            {"HINDALCO.NS", "HINDALCO"},
            {"HINDPETRO.NS", "HINDPETRO"},
            {"HINDUNILVR.NS", "HINDUNILVR"},
            {"HINDZINC.NS", "HINDZINC"},
            {"ITC.NS", "ITC"},
            {"KOTAKBANK.NS", "KOTAKBANK"},
            {"LUPIN.NS", "LUPIN"},
            {"MARUTI.NS", "MARUTI"},
            {"NTPC.NS", "NTPC"},
            {"POWERGRID.NS", "POWERGRID"},
            {"RELIANCE.NS", "RELIANCE"},
            {"SBILIFE.NS", "SBILIFE"},
            {"SBIN.NS", "SBIN"},
            {"SUNPHARMA.NS", "SUNPHARMA"},
            {"TATACONSUM.NS", "TATACONSUM"},
            {"TCS.NS", "TCS"},
            {"TATASTEEL.NS", "TATASTEEL"},
            {"TECHM.NS", "TECHM"},
            {"ULTRACEMCO.NS", "ULTRACEMCO"},
            {"VEDL.NS", "VEDL"},
            {"WIPRO.NS", "WIPRO"},
            {"YESBANK.NS", "YESBANK"},
            {"TATACHEM.NS", "TATACHEM"},
            {"UPL.NS", "UPL"},
            {"SRF.NS", "SRF"},
            {"TATVA.NS", "TATVA"},
            {"RALLIS.NS", "RALLIS"},
            {"COALINDIA.NS", "COALINDIA"},
            {"TEJASNET.NS", "TEJASNET"},
            {"NELCO.NS", "NELCO"},
            {"LT.NS", "LT"},
            {"ACC.NS", "ACC"},
            {"GRASIM.NS", "GRASIM"},
            {"NYKAA.NS", "NYKAA"},
            {"TATAPOWER.NS", "TATAPOWER"},
            {"SJVN.NS", "SJVN"},
            {"DMART.NS", "DMART"},
            {"BALRAMCHIN.NS", "BALRAMCHIN"},
            {"INDHOTEL.NS", "INDHOTEL"},
            {"STOVEKRAFT.NS", "STOVEKRAFT"},
            {"LICI.NS", "LICI"},
            {"ANGELONE.NS", "ANGELONE"},
            {"IEX.NS", "IEX"},
            {"HEG.NS", "HEG"},
            {"POLYCAB.NS", "POLYCAB"},
            {"HAVELLS.NS", "HAVELLS"},
            {"TITAGARH.NS", "TITAGARH"},
            {"AFFLE.NS", "AFFLE"},
            {"ZEEL.NS", "ZEEL"},
            {"NMDC.NS", "NMDC"},
            {"JSWSTEEL.NS", "JSWSTEEL"},
            {"SAIL.NS", "SAIL"},
            {"INDIGO.NS", "INDIGO"},
            {"CIPLA.NS", "CIPLA"},
            {"GLENMARK.NS", "GLENMARK"},
            {"DIVISLAB.NS", "DIVISLAB"},
            {"PREMIERENE.NS", "PREMIERENE"},
            {"INFY.NS", "INFY"},
            {"INDIAMART.NS", "INDIAMART"},
            {"HAPPSTMNDS.NS", "HAPPSTMNDS"},
            {"RTNINDIA.NS", "RTNINDIA"},
            {"ZOMATO.NS", "ZOMATO"},
            {"IDEA.NS", "IDEA"},
            {"TATACOMM.NS", "TATACOMM"},
            {"BHARTIARTL.NS", "BHARTIARTL"},
            {"TRIDENT.NS", "TRIDENT"},
            {"WAAREEENER.NS", "WAAREEENER"},
            {"GRANULES.NS", "GRANULES"},
            {"MCX.NS", "MCX"},
            {"OLAELEC.NS", "OLAELEC"},
            {"INDUSTOWER.NS", "INDUSTOWER"},
            {"GRSE.NS", "GRSE"},
            {"CDSL.NS", "CDSL"},
            {"HDFCBANK.NS", "HDFCBANK"},
            {"FACT.NS", "FACT"},
            {"ARE&M.NS", "ARE&M"},
            {"MANAPPURAM.NS", "MANAPPURAM"},
            {"PAYTM.NS", "PAYTM"},
            {"POLICYBZR.NS", "POLICYBZR"},
            {"HDFCLIFE.NS", "HDFCLIFE"},
            {"ICICIPRULI.NS", "ICICIPRULI"},
            {"ICICIGI.NS", "ICICIGI"},
            {"STARHEALTH.NS", "STARHEALTH"},
            {"NIVABUPA.NS", "NIVABUPA"},
            {"NAUKRI.NS", "NAUKRI"},
            {"NCC.NS", "NCC"},
            {"TRENT.NS", "TRENT"},
            {"PNB.NS", "PNB"},
            {"GMRAIRPORT.NS", "GMRAIRPORT"},
            {"BDL.NS", "BDL"},
            {"KAYNES.NS", "KAYNES"},
            {"BSE.NS", "BSE"},
            {"AZAD.NS", "AZAD"},
            {"NBCC.NS", "NBCC"},
            {"IRCTC.NS", "IRCTC"},
            {"RVNL.NS", "RVNL"},
            {"CAMS.NS", "CAMS"},
            {"DLINKINDIA.NS", "DLINKINDIA"},
            {"GRAPHITE.NS", "GRAPHITE"},
            {"EXIDEIND.NS", "EXIDEIND"},
            {"GENSOL.NS", "GENSOL"},
            {"IDEAFORGE.NS", "IDEAFORGE"},
            {"BAJAJHFL.NS", "BAJAJHFL"},
            {"IFCI.NS", "IFCI"}
    };
    private static final String[][] MARKET_EVENTS = {
            {
                    "rbi-mpc-2026-08",
                    "RBI MPC policy decision",
                    "2026-08-05",
                    "Rates",
                    "high",
                    "Policy decision can move banks, NBFCs, INR, bonds, and rate-sensitive stocks."
            },
            {
                    "india-cpi-2026-07",
                    "India CPI for July 2026",
                    "2026-08-12",
                    "Inflation",
                    "high",
                    "Domestic inflation can reset RBI expectations and move banks, FMCG, INR, and bond yields."
            },
            {
                    "us-cpi-2026-07",
                    "U.S. CPI for July 2026",
                    "2026-08-12",
                    "Global macro",
                    "high",
                    "U.S. inflation can move Nasdaq, USD/INR, gold, IT stocks, and broader risk appetite."
            },
            {
                    "jackson-hole-2026",
                    "Jackson Hole Symposium begins",
                    "2026-08-27",
                    "Central banks",
                    "medium",
                    "Central-bank remarks can reset rate expectations, liquidity assumptions, and global risk tone."
            },
            {
                    "us-cpi-2026-08",
                    "U.S. CPI for August 2026",
                    "2026-09-11",
                    "Global macro",
                    "high",
                    "U.S. inflation can shift Fed pricing and spill into Indian IT, metals, and risk assets."
            },
            {
                    "fomc-2026-09",
                    "FOMC policy decision",
                    "2026-09-16",
                    "Global rates",
                    "high",
                    "Fed decision and projections can move global equities, USD/INR, gold, and foreign flows."
            },
            {
                    "us-cpi-2026-09",
                    "U.S. CPI for September 2026",
                    "2026-10-14",
                    "Global macro",
                    "high",
                    "A major inflation print ahead of year-end Fed pricing and global asset allocation."
            },
            {
                    "fomc-2026-10",
                    "FOMC policy decision",
                    "2026-10-28",
                    "Global rates",
                    "high",
                    "Fed rates guidance can affect foreign flows, currency pressure, and valuation multiples."
            }
    };

    private WebView webView;
    private ProgressBar progressBar;
    private View errorView;
    private Object backInvokedCallback;
    private final ExecutorService bridgeExecutor = Executors.newFixedThreadPool(4);
    private final Map<String, Future<?>> bridgeRequests = Collections.synchronizedMap(new HashMap<>());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        configureWindow();

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(11, 19, 33));
        applyStatusBarInset(root);

        webView = new WebView(this);
        configureWebView(webView);
        root.addView(webView, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
        ));

        progressBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progressBar.setMax(100);
        FrameLayout.LayoutParams progressParams = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                dp(3),
                Gravity.TOP
        );
        root.addView(progressBar, progressParams);

        errorView = createErrorView();
        errorView.setVisibility(View.GONE);
        root.addView(errorView, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
        ));

        setContentView(root);
        registerPredictiveBack();

        if (BuildConfig.DEBUG) {
            WebView.setWebContentsDebuggingEnabled(true);
        }

        webView.loadUrl(BuildConfig.START_URL);
    }

    private void configureWindow() {
        Window window = getWindow();
        window.setStatusBarColor(Color.rgb(11, 19, 33));
        window.setNavigationBarColor(Color.rgb(6, 14, 28));
        window.getDecorView().setSystemUiVisibility(0);
    }

    @SuppressWarnings("deprecation")
    private void applyStatusBarInset(View root) {
        root.setOnApplyWindowInsetsListener((view, insets) -> {
            int topInset = Build.VERSION.SDK_INT >= Build.VERSION_CODES.R
                    ? Api30Insets.statusBarTop(insets)
                    : insets.getSystemWindowInsetTop();
            view.setPadding(0, topInset, 0, 0);
            return insets;
        });
        root.requestApplyInsets();
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void configureWebView(WebView target) {
        WebSettings settings = target.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);

        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);

        target.addJavascriptInterface(new MarketBridge(), "StockBridge");
        target.setOverScrollMode(View.OVER_SCROLL_NEVER);
        target.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int progress) {
                progressBar.setProgress(progress);
                progressBar.setVisibility(progress >= 100 ? View.GONE : View.VISIBLE);
            }
        });
        target.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return openExternalUri(request.getUrl());
            }

            @SuppressWarnings("deprecation")
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return openExternalUri(Uri.parse(url));
            }

            private boolean openExternalUri(Uri uri) {
                String scheme = uri.getScheme();
                if ("file".equalsIgnoreCase(scheme)) {
                    return false;
                }
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, uri));
                } catch (Exception ignored) {
                    // Keep unsupported external schemes out of the bridge-enabled WebView.
                }
                return true;
            }

            @Override
            public void onPageStarted(WebView view, String url, android.graphics.Bitmap favicon) {
                errorView.setVisibility(View.GONE);
                progressBar.setVisibility(View.VISIBLE);
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    showOfflineState();
                }
            }

            @SuppressWarnings("deprecation")
            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                showOfflineState();
            }
        });
    }

    private View createErrorView() {
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setGravity(Gravity.CENTER);
        panel.setPadding(dp(28), dp(28), dp(28), dp(28));
        panel.setBackgroundColor(Color.rgb(11, 19, 33));

        TextView title = new TextView(this);
        title.setText(R.string.dashboard_offline);
        title.setTextColor(Color.rgb(219, 226, 246));
        title.setTextSize(24);
        title.setGravity(Gravity.CENTER);
        title.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        panel.addView(title, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
        ));

        TextView detail = new TextView(this);
        detail.setText(R.string.dashboard_offline_detail);
        detail.setTextColor(Color.rgb(197, 198, 204));
        detail.setTextSize(15);
        detail.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams detailParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
        );
        detailParams.setMargins(0, dp(10), 0, dp(20));
        panel.addView(detail, detailParams);

        Button retry = new Button(this);
        retry.setText(R.string.retry);
        retry.setAllCaps(false);
        retry.setOnClickListener(v -> {
            errorView.setVisibility(View.GONE);
            webView.loadUrl(BuildConfig.START_URL);
        });
        panel.addView(retry, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
        ));

        return panel;
    }

    private void showOfflineState() {
        progressBar.setVisibility(View.GONE);
        errorView.setVisibility(View.VISIBLE);
    }

    private final class MarketBridge {
        private String dashboardCache;
        private long dashboardCacheAt;
        private String dashboardCacheKey = "";
        private String macroCache;
        private long macroCacheAt;
        private String intelCache;
        private long intelCacheAt;
        private String intelCacheKey = "";
        private final Map<String, String> symbolNewsCache = Collections.synchronizedMap(new HashMap<>());
        private final Map<String, Long> symbolNewsCacheAt = Collections.synchronizedMap(new HashMap<>());
        private String discoveryCache;
        private long discoveryCacheAt;
        private Map<String, QuoteSnapshot> quoteSnapshotCache = new HashMap<>();
        private long quoteSnapshotCacheAt;
        private String quoteSnapshotCacheKey = "";
        private final Map<String, String> detailCache = Collections.synchronizedMap(new HashMap<>());
        private final Map<String, Long> detailCacheAt = Collections.synchronizedMap(new HashMap<>());
        private final Map<String, String> dailyHistoryCache = Collections.synchronizedMap(new HashMap<>());
        private final Map<String, Long> dailyHistoryCacheAt = Collections.synchronizedMap(new HashMap<>());

        @JavascriptInterface
        public String getDashboardJson() {
            return getDashboardJsonForSymbols("[]");
        }

        @JavascriptInterface
        public String getDashboardJsonForSymbols(String customSymbolsJson) {
            long now = System.currentTimeMillis();
            String cacheKey = normalizeSymbolListKey(customSymbolsJson);
            boolean needsTechnicalRefresh = dashboardCache == null
                    || !dashboardCacheKey.equals(cacheKey)
                    || now - dashboardCacheAt >= TECHNICAL_CACHE_MS;

            if (needsTechnicalRefresh) {
                try {
                    dashboardCache = buildDashboardJson(customSymbolsJson).toString();
                    dashboardCacheAt = now;
                    dashboardCacheKey = cacheKey;
                } catch (Exception e) {
                    return buildErrorDashboard(e.getMessage());
                }
            }

            return withFreshDashboardQuotes(dashboardCache, customSymbolsJson);
        }

        @JavascriptInterface
        public String getMacroJson() {
            long now = System.currentTimeMillis();
            if (macroCache != null && now - macroCacheAt < MACRO_CACHE_MS) {
                return macroCache;
            }

            try {
                List<String> symbols = new ArrayList<>();
                symbols.add("USDINR=X");
                symbols.add("CL=F");
                symbols.add("^INDIAVIX");
                Map<String, QuoteSnapshot> snapshots = getQuoteSnapshots(symbols);
                JSONObject root = new JSONObject();
                root.put("usd_inr", buildQuoteJsonSafe(
                        "USDINR=X",
                        "USD/INR",
                        "INR",
                        snapshots.get(normalizeQuoteSymbol("USDINR=X"))
                ));
                root.put("crude", buildQuoteJsonSafe(
                        "CL=F",
                        "WTI Crude",
                        "USD",
                        snapshots.get(normalizeQuoteSymbol("CL=F"))
                ));
                root.put("india_vix", buildQuoteJsonSafe(
                        "^INDIAVIX",
                        "India VIX",
                        "INDEX",
                        snapshots.get(normalizeQuoteSymbol("^INDIAVIX"))
                ));
                macroCache = root.toString();
                macroCacheAt = now;
                return macroCache;
            } catch (Exception e) {
                return errorJson("Macro data unavailable: " + e.getMessage());
            }
        }

        @JavascriptInterface
        public String getMarketStatusJson() {
            try {
                Calendar now = Calendar.getInstance(TimeZone.getTimeZone("Asia/Kolkata"));
                int day = now.get(Calendar.DAY_OF_WEEK);
                int minutes = now.get(Calendar.HOUR_OF_DAY) * 60 + now.get(Calendar.MINUTE);
                boolean weekday = day >= Calendar.MONDAY && day <= Calendar.FRIDAY;
                boolean open = weekday && minutes >= (9 * 60 + 15) && minutes <= (15 * 60 + 30);

                JSONObject status = new JSONObject();
                status.put("is_open", open);
                status.put("source", "Android local clock");
                status.put("timezone", "Asia/Kolkata");
                return status.toString();
            } catch (Exception e) {
                return errorJson("Market status unavailable: " + e.getMessage());
            }
        }

        @JavascriptInterface
        public void requestJson(String requestId, String method, String argsJson) {
            Future<?> request = bridgeExecutor.submit(() -> {
                String result;
                try {
                    JSONArray args = new JSONArray(argsJson == null || argsJson.isEmpty() ? "[]" : argsJson);
                    switch (method == null ? "" : method) {
                        case "getDashboardJsonForSymbols":
                            result = getDashboardJsonForSymbols(args.optString(0, "[]"));
                            break;
                        case "getMacroJson":
                            result = getMacroJson();
                            break;
                        case "getMarketStatusJson":
                            result = getMarketStatusJson();
                            break;
                        case "getDailyCloseHistoryJsonForSymbols":
                            result = getDailyCloseHistoryJsonForSymbols(args.optString(0, "[]"));
                            break;
                        case "getIntelJsonForRows":
                            result = getIntelJsonForRows(args.optString(0, "[]"));
                            break;
                        case "refreshIntelJsonForRows":
                            result = refreshIntelJsonForRows(args.optString(0, "[]"));
                            break;
                        case "discoverNewsStocksJson":
                            result = discoverNewsStocksJson();
                            break;
                        case "searchStockJson":
                            result = searchStockJson(args.optString(0, ""));
                            break;
                        case "getStockDetailJson":
                            result = getStockDetailJson(args.optString(0, ""));
                            break;
                        default:
                            result = errorJson("Unsupported native request");
                            break;
                    }
                } catch (Exception e) {
                    result = errorJson("Native request failed: " + e.getMessage());
                }
                try {
                    if (!Thread.currentThread().isInterrupted()) {
                        deliverAsyncJson(requestId, result);
                    }
                } finally {
                    bridgeRequests.remove(requestId);
                }
            });
            bridgeRequests.put(requestId, request);
            if (request.isDone()) {
                bridgeRequests.remove(requestId);
            }
        }

        @JavascriptInterface
        public void cancelRequest(String requestId) {
            Future<?> request = bridgeRequests.remove(requestId);
            if (request != null) {
                request.cancel(true);
            }
        }

        @JavascriptInterface
        public String getDailyCloseHistoryJsonForSymbols(String symbolsJson) {
            try {
                JSONArray requested = new JSONArray(symbolsJson == null || symbolsJson.trim().isEmpty() ? "[]" : symbolsJson);
                Map<String, String[]> unique = new HashMap<>();
                List<String[]> tickers = new ArrayList<>();
                for (int i = 0; i < requested.length(); i += 1) {
                    String raw = requested.optString(i, "").trim();
                    if (raw.isEmpty()) {
                        continue;
                    }
                    String displaySymbol = normalizeDisplaySymbol(raw);
                    addUniqueTicker(unique, tickers, resolveYahooSymbol(displaySymbol), displaySymbol);
                }

                JSONArray histories = new JSONArray();
                Set<String> returnedSymbols = new HashSet<>();
                long now = System.currentTimeMillis();
                List<String[]> missing = new ArrayList<>();
                for (String[] ticker : tickers) {
                    String displaySymbol = ticker[1];
                    String cached = dailyHistoryCache.get(displaySymbol);
                    Long cachedAt = dailyHistoryCacheAt.get(displaySymbol);
                    if (cached != null && cachedAt != null && now - cachedAt < DAILY_HISTORY_CACHE_MS) {
                        histories.put(new JSONObject(cached));
                        returnedSymbols.add(displaySymbol);
                    } else {
                        missing.add(ticker);
                    }
                }

                ExecutorService executor = Executors.newFixedThreadPool(
                        Math.min(DAILY_HISTORY_SCAN_THREADS, Math.max(1, missing.size()))
                );
                CompletionService<JSONObject> completion = new ExecutorCompletionService<>(executor);
                int submitted = 0;
                try {
                    for (String[] ticker : missing) {
                        completion.submit(() -> {
                            String yahooSymbol = ticker[0];
                            String displaySymbol = ticker[1];
                            try {
                                JSONObject history = buildDailyCloseHistoryJson(yahooSymbol, displaySymbol);
                                dailyHistoryCache.put(displaySymbol, history.toString());
                                dailyHistoryCacheAt.put(displaySymbol, System.currentTimeMillis());
                                return history;
                            } catch (Exception e) {
                                return new JSONObject()
                                        .put("symbol", displaySymbol)
                                        .put("error", e.getMessage() == null ? "Daily history unavailable" : e.getMessage());
                            }
                        });
                        submitted += 1;
                    }

                    long deadline = System.currentTimeMillis() + DAILY_HISTORY_TOTAL_WAIT_MS;
                    for (int completed = 0; completed < submitted; completed += 1) {
                        long waitMs = Math.max(0L, deadline - System.currentTimeMillis());
                        if (waitMs == 0L) {
                            break;
                        }
                        Future<JSONObject> future = completion.poll(waitMs, TimeUnit.MILLISECONDS);
                        if (future == null) {
                            break;
                        }
                        JSONObject history = future.get();
                        String symbol = history.optString("symbol", "");
                        if (!history.has("error")) {
                            returnedSymbols.add(symbol);
                            histories.put(history);
                        }
                    }
                } finally {
                    executor.shutdownNow();
                }

                JSONArray failedSymbols = new JSONArray();
                for (String[] ticker : tickers) {
                    if (!returnedSymbols.contains(ticker[1])) {
                        failedSymbols.put(ticker[1]);
                    }
                }

                JSONObject root = new JSONObject();
                root.put("histories", histories);
                root.put("requested_count", tickers.size());
                root.put("completed_count", histories.length());
                root.put("complete", histories.length() == tickers.size());
                root.put("failed_symbols", failedSymbols);
                root.put("updated_at", isoNow());
                root.put("source", "Yahoo Finance adjusted daily closes");
                return root.toString();
            } catch (Exception e) {
                return errorJson("Daily close history unavailable: " + e.getMessage());
            }
        }

        private JSONObject buildDailyCloseHistoryJson(String yahooSymbol, String displaySymbol) throws Exception {
            Series series = fetchSeries(yahooSymbol, "3mo", "1d");
            JSONArray closes = new JSONArray();
            int start = Math.max(0, series.close.size() - DAILY_HISTORY_LIMIT);
            for (int i = start; i < series.close.size(); i += 1) {
                long timestamp = series.timestamps.size() > i ? series.timestamps.get(i) : 0L;
                if (timestamp <= 0L || !isCompletedDailyCandle(timestamp)) {
                    continue;
                }
                double close = series.adjustedClose.size() > i
                        ? series.adjustedClose.get(i)
                        : series.close.get(i);
                closes.put(new JSONObject()
                        .put("date", formatEpochDate(timestamp))
                        .put("close", round(close, 2))
                        .put("source", "yahoo_adjusted_daily_close"));
            }

            return new JSONObject()
                    .put("symbol", displaySymbol)
                    .put("closes", closes)
                    .put("source", "Yahoo Finance adjusted 3mo/1d")
                    .put("updated_at", isoNow());
        }

        private boolean isCompletedDailyCandle(long epochSeconds) {
            Calendar candle = Calendar.getInstance(TimeZone.getTimeZone("Asia/Kolkata"));
            candle.setTimeInMillis(epochSeconds * 1000L);
            Calendar now = Calendar.getInstance(TimeZone.getTimeZone("Asia/Kolkata"));
            boolean sameDay = candle.get(Calendar.YEAR) == now.get(Calendar.YEAR)
                    && candle.get(Calendar.DAY_OF_YEAR) == now.get(Calendar.DAY_OF_YEAR);
            if (!sameDay) {
                return candle.before(now);
            }
            int minutes = now.get(Calendar.HOUR_OF_DAY) * 60 + now.get(Calendar.MINUTE);
            return minutes >= (15 * 60 + 30);
        }

        private void deliverAsyncJson(String requestId, String result) {
            String safeId = JSONObject.quote(requestId == null ? "" : requestId);
            String safeResult = JSONObject.quote(result == null ? "{}" : result);
            runOnUiThread(() -> {
                if (webView == null) {
                    return;
                }
                webView.evaluateJavascript(
                        "window.StockAsync && window.StockAsync.resolve(" + safeId + "," + safeResult + ")",
                        null
                );
            });
        }

        @JavascriptInterface
        public String getIntelJsonForRows(String rowsJson) {
            return buildIntelJsonForRows(rowsJson, false);
        }

        @JavascriptInterface
        public String refreshIntelJsonForRows(String rowsJson) {
            return buildIntelJsonForRows(rowsJson, true);
        }

        @JavascriptInterface
        public String discoverNewsStocksJson() {
            long now = System.currentTimeMillis();
            if (discoveryCache != null && now - discoveryCacheAt < DISCOVERY_CACHE_MS) {
                return discoveryCache;
            }

            try {
                JSONObject root = buildNewsStockDiscovery();
                discoveryCache = root.toString();
                discoveryCacheAt = now;
                return discoveryCache;
            } catch (Exception e) {
                try {
                    return new JSONObject()
                            .put("suggestions", new JSONArray())
                            .put("source", "Google News + Yahoo Finance")
                            .put("error", "Web discovery unavailable: " + e.getMessage())
                            .put("updated_at", isoNow())
                            .toString();
                } catch (Exception ignored) {
                    return "{\"suggestions\":[]}";
                }
            }
        }

        private String buildIntelJsonForRows(String rowsJson, boolean forceRefresh) {
            long now = System.currentTimeMillis();
            String cacheKey = normalizeIntelRowsKey(rowsJson);
            if (!forceRefresh && intelCache != null && intelCacheKey.equals(cacheKey) && now - intelCacheAt < INTEL_CACHE_MS) {
                try {
                    JSONObject cached = new JSONObject(intelCache);
                    cached.put("news_actions", buildNewsActions(
                            cached.optJSONArray("latest_news"),
                            parseRowsJson(rowsJson)
                    ));
                    cached.put("scored_at", isoNow());
                    return cached.toString();
                } catch (Exception ignored) {
                    return intelCache;
                }
            }

            try {
                List<JSONObject> rows = parseRowsJson(rowsJson);
                JSONObject fetchResult = buildIntelligence(rows, forceRefresh);
                JSONArray news = fetchResult.optJSONArray("items");
                if (news == null) {
                    news = new JSONArray();
                }
                JSONObject root = new JSONObject();
                root.put("latest_news", news);
                root.put("news_actions", buildNewsActions(news, rows));
                root.put("source", "Google News");
                root.put("updated_at", isoNow());
                root.put("news_status", fetchResult.optString("status", "complete"));
                root.put("requested_symbols", fetchResult.optJSONArray("requested_symbols"));
                root.put("completed_symbols", fetchResult.optJSONArray("completed_symbols"));
                root.put("failed_symbols", fetchResult.optJSONArray("failed_symbols"));
                root.put("stale_symbols", fetchResult.optJSONArray("stale_symbols"));
                if (!"failed".equals(fetchResult.optString("status", ""))) {
                    intelCache = root.toString();
                    intelCacheAt = now;
                    intelCacheKey = cacheKey;
                }
                return root.toString();
            } catch (Exception e) {
                try {
                    return new JSONObject()
                            .put("error", e.getMessage() == null
                                    ? "News refresh is unavailable"
                                    : "News refresh is unavailable: " + e.getMessage())
                            .toString();
                } catch (Exception ignored) {
                    return "{\"error\":\"News refresh is unavailable\"}";
                }
            }
        }

        private JSONObject buildNewsStockDiscovery() throws Exception {
            String query = URLEncoder.encode("Indian company shares stock NSE when:1d", StandardCharsets.UTF_8.name());
            String feedUrl = "https://news.google.com/rss/search?q="
                    + query
                    + "&hl=en-IN&gl=IN&ceid=IN:en";
            String xml = fetchUrl(feedUrl, INTEL_NEWS_TIMEOUT_MS);

            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            try {
                factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
                factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
                factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
            } catch (Exception ignored) {
                // Android XML providers vary; unsupported hardening flags are ignored.
            }

            Document doc = factory.newDocumentBuilder().parse(new InputSource(new StringReader(xml)));
            NodeList items = doc.getElementsByTagName("item");
            int candidateCount = Math.min(16, items.getLength());
            ExecutorService executor = Executors.newFixedThreadPool(Math.min(4, Math.max(1, candidateCount)));
            CompletionService<JSONObject> completion = new ExecutorCompletionService<>(executor);
            int submitted = 0;

            try {
                for (int i = 0; i < candidateCount; i += 1) {
                    Element item = (Element) items.item(i);
                    String title = normalizeWhitespace(childText(item, "title"));
                    String companyQuery = discoveryCompanyQuery(title);
                    if (companyQuery.isEmpty()) {
                        continue;
                    }
                    String source = normalizeWhitespace(childText(item, "source"));
                    String articleUrl = normalizeWhitespace(childText(item, "link"));
                    String publishedAt = normalizeWhitespace(childText(item, "pubDate"));
                    completion.submit(() -> searchYahooNseStock(
                            companyQuery,
                            title,
                            source,
                            articleUrl,
                            publishedAt
                    ));
                    submitted += 1;
                }

                JSONArray suggestions = new JSONArray();
                Set<String> seen = new HashSet<>();
                long deadline = System.currentTimeMillis() + DISCOVERY_TOTAL_WAIT_MS;
                for (int completed = 0; completed < submitted && suggestions.length() < DISCOVERY_LIMIT; completed += 1) {
                    long waitMs = Math.max(0L, deadline - System.currentTimeMillis());
                    if (waitMs == 0L) {
                        break;
                    }
                    JSONObject suggestion;
                    try {
                        Future<JSONObject> future = completion.poll(waitMs, TimeUnit.MILLISECONDS);
                        if (future == null) {
                            break;
                        }
                        suggestion = future.get();
                    } catch (Exception ignored) {
                        suggestion = null;
                    }
                    if (suggestion == null) {
                        continue;
                    }
                    String symbol = suggestion.optString("symbol", "");
                    if (!symbol.isEmpty() && seen.add(symbol)) {
                        suggestions.put(suggestion);
                    }
                }

                JSONObject root = new JSONObject();
                root.put("suggestions", suggestions);
                root.put("source", "Google News + Yahoo Finance symbol search");
                root.put("updated_at", isoNow());
                return root;
            } finally {
                executor.shutdownNow();
            }
        }

        private String discoveryCompanyQuery(String rawTitle) {
            String title = normalizeWhitespace(rawTitle);
            int sourceSuffix = title.lastIndexOf(" - ");
            if (sourceSuffix > 0) {
                title = title.substring(0, sourceSuffix).trim();
            }

            java.util.regex.Matcher nseSymbol = java.util.regex.Pattern
                    .compile("(?i)\\(NSE:([A-Z0-9&.-]{2,20})\\)")
                    .matcher(title);
            if (nseSymbol.find()) {
                return nseSymbol.group(1).toUpperCase(Locale.US);
            }

            title = title.replaceFirst("(?i)^stocks? to buy[^:]*:\\s*", "");
            title = title.replaceFirst("(?i)^should you buy\\s+", "");

            String lower = title.toLowerCase(Locale.US);
            String[] markers = {
                    " share price", " shares", " stock", " jumps", " jump", " surges", " surge",
                    " rallies", " rally", " rises", " rise", " gains", " gain", " falls", " fall",
                    " fell", " slips", " slip", " plunges", " plunge", " tumbles", " hits", " soars",
                    " approves", " reports", " announces", " posts", " wins", " receives"
            };
            int cut = title.length();
            for (String marker : markers) {
                int index = lower.indexOf(marker);
                if (index >= 3 && index < cut) {
                    cut = index;
                }
            }
            title = title.substring(0, cut).trim();
            title = title.replaceFirst("(?i)^(why|how|watch|buy|sell|stocks? to watch)[: -]+", "");
            int colon = title.indexOf(':');
            if (colon >= 3) {
                title = title.substring(0, colon).trim();
            }
            int comma = title.indexOf(',');
            if (comma >= 3) {
                title = title.substring(0, comma).trim();
            }
            title = normalizeWhitespace(title.replaceAll("[^A-Za-z0-9&.' -]", " "));
            String generic = title.toLowerCase(Locale.US);
            if (title.length() < 3 || title.length() > 70
                    || generic.matches("^(nse|bse|market|markets|top($|\\s.*))$")
                    || containsAny(generic, "stock market", "sensex", "nifty", "dalal street", "markets today")) {
                return "";
            }
            return title;
        }

        private JSONObject searchYahooNseStock(
                String companyQuery,
                String headline,
                String source,
                String articleUrl,
                String publishedAt
        ) {
            try {
                String encoded = URLEncoder.encode(companyQuery, StandardCharsets.UTF_8.name());
                String url = "https://query1.finance.yahoo.com/v1/finance/search?q="
                        + encoded
                        + "&quotesCount=5&newsCount=0&listsCount=0&enableFuzzyQuery=false";
                JSONObject payload = new JSONObject(fetchUrl(url, INTEL_NEWS_TIMEOUT_MS));
                JSONArray quotes = payload.optJSONArray("quotes");
                if (quotes == null) {
                    return null;
                }

                JSONObject best = null;
                int bestScore = 0;
                for (int i = 0; i < quotes.length(); i += 1) {
                    JSONObject quote = quotes.optJSONObject(i);
                    if (quote == null) {
                        continue;
                    }
                    String yahooSymbol = quote.optString("symbol", "").toUpperCase(Locale.US);
                    String quoteType = quote.optString("quoteType", "");
                    String exchange = quote.optString("exchange", "");
                    if (!yahooSymbol.endsWith(".NS")
                            || !"EQUITY".equalsIgnoreCase(quoteType)
                            || !("NSI".equalsIgnoreCase(exchange) || "NSE".equalsIgnoreCase(exchange))) {
                        continue;
                    }
                    String name = quote.optString("longname", quote.optString("shortname", ""));
                    int score = discoveryTokenScore(companyQuery, name);
                    String displaySymbol = normalizeDisplaySymbol(yahooSymbol);
                    String compactQuery = companyQuery.toUpperCase(Locale.US).replaceAll("[^A-Z0-9&.-]", "");
                    if (displaySymbol.equals(compactQuery)) {
                        score += 3;
                    } else if (i == 0 && score == 0 && companyQuery.length() >= 3) {
                        score = 1;
                    }
                    if (score > bestScore) {
                        best = quote;
                        bestScore = score;
                    }
                }
                if (best == null || bestScore <= 0) {
                    return null;
                }

                String symbol = normalizeDisplaySymbol(best.optString("symbol", ""));
                String company = best.optString("longname", best.optString("shortname", symbol));
                JSONObject suggestion = new JSONObject();
                suggestion.put("symbol", symbol);
                suggestion.put("company", company);
                suggestion.put("exchange", "NSE");
                suggestion.put("confidence", (int) clamp(58.0 + bestScore * 11.0, 60.0, 92.0));
                suggestion.put("headline", headline);
                suggestion.put("source", source.isEmpty() ? "Google News" : source);
                suggestion.put("published_at", publishedAt);
                suggestion.put("url", articleUrl);
                suggestion.put("reason", "Company name matched an NSE equity in a fresh market headline.");
                return suggestion;
            } catch (Exception ignored) {
                return null;
            }
        }

        private int discoveryTokenScore(String query, String companyName) {
            String normalizedName = companyName == null ? "" : companyName.toLowerCase(Locale.US);
            String[] tokens = query.toLowerCase(Locale.US).replaceAll("[^a-z0-9 ]", " ").split("\\s+");
            int score = 0;
            for (String token : tokens) {
                if (token.length() < 3 || containsAny(token,
                        "the", "and", "india", "indian", "limited", "ltd", "share", "shares", "stock", "company")) {
                    continue;
                }
                if (normalizedName.contains(token)) {
                    score += 1;
                }
            }

            String compactQuery = query.toUpperCase(Locale.US).replaceAll("[^A-Z0-9]", "");
            if (compactQuery.length() >= 2 && compactQuery.length() <= 6) {
                StringBuilder acronym = new StringBuilder();
                String[] companyTokens = normalizedName.replaceAll("[^a-z0-9 ]", " ").split("\\s+");
                for (String companyToken : companyTokens) {
                    if (companyToken.isEmpty() || "of".equals(companyToken) || "the".equals(companyToken)) {
                        continue;
                    }
                    acronym.append(Character.toUpperCase(companyToken.charAt(0)));
                }
                if (compactQuery.equals(acronym.toString())) {
                    score = Math.max(score, 3);
                }
            }
            return score;
        }

        @JavascriptInterface
        public String getStockDetailJson(String symbol) {
            String displaySymbol = normalizeDisplaySymbol(symbol);
            long now = System.currentTimeMillis();
            Long cachedAt = detailCacheAt.get(displaySymbol);
            if (cachedAt != null && detailCache.containsKey(displaySymbol) && now - cachedAt < DETAIL_CACHE_MS) {
                return detailCache.get(displaySymbol);
            }

            try {
                String payload = buildStockDetailJson(displaySymbol).toString();
                detailCache.put(displaySymbol, payload);
                detailCacheAt.put(displaySymbol, now);
                return payload;
            } catch (Exception e) {
                return errorJson("Stock detail unavailable: " + e.getMessage());
            }
        }

        @JavascriptInterface
        public String searchStockJson(String symbol) {
            try {
                String displaySymbol = normalizeDisplaySymbol(symbol);
                Analysis analysis = analyzeTicker(resolveYahooSymbol(displaySymbol), displaySymbol);
                if (analysis == null) {
                    return errorJson("No Yahoo data found for " + displaySymbol);
                }

                JSONObject root = new JSONObject();
                root.put("stock", analysis.toPredictionJson());
                root.put("source", analysis.quoteSource);
                root.put("updated_at", isoNow());
                return root.toString();
            } catch (Exception e) {
                return errorJson("Stock search unavailable: " + e.getMessage());
            }
        }

        private JSONObject buildStockDetailJson(String displaySymbol) throws Exception {
            String yahooSymbol = resolveYahooSymbol(displaySymbol);
            JSONObject root = new JSONObject();
            root.put("symbol", displaySymbol);
            root.put("yahoo_symbol", yahooSymbol);
            root.put("source", "Yahoo Finance + Google News");
            root.put("updated_at", isoNow());

            try {
                Analysis analysis = analyzeTicker(yahooSymbol, displaySymbol);
                root.put("quote", analysis == null ? JSONObject.NULL : analysis.toPredictionJson());
            } catch (Exception e) {
                root.put("quote", JSONObject.NULL);
                root.put("quote_error", e.getMessage());
            }

            try {
                root.put("range_52w", build52WeekRangeJson(yahooSymbol));
            } catch (Exception e) {
                root.put("range_52w", JSONObject.NULL);
                root.put("range_error", e.getMessage());
            }

            try {
                root.put("revenue", buildRevenueJson(yahooSymbol));
            } catch (Exception e) {
                root.put("revenue", new JSONArray());
                root.put("revenue_error", e.getMessage());
            }

            try {
                root.put("news", buildNewsJson(displaySymbol));
            } catch (Exception e) {
                root.put("news", new JSONArray());
                root.put("news_error", e.getMessage());
            }

            return root;
        }

        private JSONObject build52WeekRangeJson(String yahooSymbol) throws Exception {
            Series series = fetchSeries(yahooSymbol, "1y", "1d");
            double high = -Double.MAX_VALUE;
            double low = Double.MAX_VALUE;
            long highTs = 0L;
            long lowTs = 0L;

            for (int i = 0; i < series.close.size(); i += 1) {
                double highValue = series.high.get(i);
                double lowValue = series.low.get(i);
                long ts = series.timestamps.size() > i ? series.timestamps.get(i) : 0L;

                if (highValue > high) {
                    high = highValue;
                    highTs = ts;
                }
                if (lowValue < low) {
                    low = lowValue;
                    lowTs = ts;
                }
            }

            JSONObject range = new JSONObject();
            range.put("high", round(high, 2));
            range.put("low", round(low, 2));
            range.put("high_date", formatEpochDate(highTs));
            range.put("low_date", formatEpochDate(lowTs));
            range.put("source", "Yahoo Finance 1y/1d");
            return range;
        }

        private JSONArray buildRevenueJson(String yahooSymbol) throws Exception {
            long period2 = (System.currentTimeMillis() / 1000L) + (366L * 24L * 60L * 60L);
            long period1 = period2 - (8L * 366L * 24L * 60L * 60L);
            String encoded = URLEncoder.encode(yahooSymbol, StandardCharsets.UTF_8.name());
            String url = "https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/"
                    + encoded
                    + "?type=annualTotalRevenue,quarterlyTotalRevenue"
                    + "&period1=" + period1
                    + "&period2=" + period2;

            JSONObject timeseries = new JSONObject(fetchUrl(url)).getJSONObject("timeseries");
            JSONArray result = timeseries.optJSONArray("result");
            List<JSONObject> rows = extractRevenueRows(result, "annualTotalRevenue");
            String periodLabel = "Annual";
            if (rows.isEmpty()) {
                rows = extractRevenueRows(result, "quarterlyTotalRevenue");
                periodLabel = "Quarterly";
            }

            Collections.sort(rows, (left, right) ->
                    left.optString("date", "").compareTo(right.optString("date", ""))
            );

            JSONArray output = new JSONArray();
            int start = Math.max(0, rows.size() - 6);
            for (int i = start; i < rows.size(); i += 1) {
                JSONObject row = rows.get(i);
                row.put("period_label", periodLabel);
                output.put(row);
            }
            return output;
        }

        private List<JSONObject> extractRevenueRows(JSONArray result, String key) throws Exception {
            List<JSONObject> rows = new ArrayList<>();
            if (result == null) {
                return rows;
            }

            for (int i = 0; i < result.length(); i += 1) {
                JSONObject container = result.optJSONObject(i);
                if (container == null) {
                    continue;
                }
                JSONArray values = container.optJSONArray(key);
                if (values == null) {
                    continue;
                }

                for (int j = 0; j < values.length(); j += 1) {
                    JSONObject item = values.optJSONObject(j);
                    if (item == null) {
                        continue;
                    }
                    JSONObject reported = item.optJSONObject("reportedValue");
                    if (reported == null) {
                        continue;
                    }
                    double raw = reported.optDouble("raw", Double.NaN);
                    if (Double.isNaN(raw)) {
                        continue;
                    }

                    String date = item.optString("asOfDate", "");
                    String currency = item.optString("currencyCode", "INR");
                    String formatted = reported.optString("fmt", compactMoney(raw));

                    JSONObject row = new JSONObject();
                    row.put("date", date);
                    row.put("label", date.length() >= 4 ? date.substring(0, 4) : date);
                    row.put("value", raw);
                    row.put("formatted", "INR".equals(currency) ? "₹" + formatted : currency + " " + formatted);
                    row.put("currency", currency);
                    rows.add(row);
                }
            }
            return rows;
        }

        private JSONArray buildNewsJson(String displaySymbol) throws Exception {
            return fetchNewsForSymbol(displaySymbol, null, 8);
        }

        private JSONArray fetchNewsForSymbol(String displaySymbol, JSONObject signalRow, int limit) throws Exception {
            String query = URLEncoder.encode(displaySymbol + " NSE stock news when:2d", StandardCharsets.UTF_8.name());
            String url = "https://news.google.com/rss/search?q="
                    + query
                    + "&hl=en-IN&gl=IN&ceid=IN:en";
            String xml = fetchUrl(url, INTEL_NEWS_TIMEOUT_MS);

            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            try {
                factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
                factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
                factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
            } catch (Exception ignored) {
                // Some Android XML providers do not expose every hardening feature.
            }

            Document doc = factory.newDocumentBuilder().parse(new InputSource(new StringReader(xml)));
            NodeList items = doc.getElementsByTagName("item");
            JSONArray news = new JSONArray();
            int count = Math.min(Math.max(1, limit), items.getLength());

            for (int i = 0; i < count; i += 1) {
                Element item = (Element) items.item(i);
                String title = normalizeWhitespace(childText(item, "title"));
                String articleUrl = normalizeWhitespace(childText(item, "link"));
                String publishedAt = normalizeWhitespace(childText(item, "pubDate"));
                if (title.isEmpty() || articleUrl.isEmpty() || !isFreshPublication(publishedAt, 72)) {
                    continue;
                }
                String source = normalizeWhitespace(childText(item, "source"));
                String sourceUrl = normalizeWhitespace(childAttribute(item, "source", "url"));
                String description = childText(item, "description");
                String summary = buildArticleSummary(displaySymbol, title, description, signalRow);
                String sentiment = inferNewsSentiment(title + " " + description);
                JSONObject article = new JSONObject();
                article.put("symbol", normalizeDisplaySymbol(displaySymbol));
                article.put("title", title);
                article.put("summary", summary);
                article.put("url", articleUrl);
                article.put("original_url", articleUrl);
                article.put("google_news_url", articleUrl);
                article.put("source_url", sourceUrl);
                article.put("source", source.isEmpty() ? "Google News" : source);
                article.put("published_at", publishedAt);
                article.put("sentiment", sentiment);
                article.put("sentiment_label", sentiment);
                article.put("affected_sectors", new JSONArray().put(normalizeDisplaySymbol(displaySymbol)).put("NSE"));
                article.put("is_breaking", containsAny(
                        (title + " " + description).toLowerCase(Locale.US),
                        "breaking", "fraud", "ban", "default", "crash", "lower circuit", "upper circuit",
                        "emergency", "attack", "collapse"
                ));
                news.put(article);
            }
            return news;
        }

        private String childText(Element parent, String tag) {
            NodeList nodes = parent.getElementsByTagName(tag);
            if (nodes == null || nodes.getLength() == 0 || nodes.item(0) == null) {
                return "";
            }
            return nodes.item(0).getTextContent();
        }

        private String childAttribute(Element parent, String tag, String attribute) {
            NodeList nodes = parent.getElementsByTagName(tag);
            if (nodes == null || nodes.getLength() == 0 || nodes.item(0) == null) {
                return "";
            }
            if (!(nodes.item(0) instanceof Element)) {
                return "";
            }
            return ((Element) nodes.item(0)).getAttribute(attribute);
        }

        private String resolveOriginalArticleUrl(String articleUrl) {
            String directUrl = queryParameterUrl(articleUrl, "url");
            if (!directUrl.isEmpty()) {
                return directUrl;
            }

            directUrl = queryParameterUrl(articleUrl, "u");
            if (!directUrl.isEmpty()) {
                return directUrl;
            }

            String redirected = followRedirectUrl(articleUrl);
            if (!redirected.isEmpty()) {
                return redirected;
            }

            return normalizeWhitespace(articleUrl);
        }

        private String followRedirectUrl(String value) {
            if (!isGoogleNewsUrl(value)) {
                return normalizeWhitespace(value);
            }

            String current = normalizeWhitespace(value);
            for (int i = 0; i < 3; i += 1) {
                HttpURLConnection connection = null;
                try {
                    connection = (HttpURLConnection) new URL(current).openConnection();
                    connection.setInstanceFollowRedirects(false);
                    connection.setConnectTimeout(1_200);
                    connection.setReadTimeout(1_200);
                    connection.setRequestMethod("GET");
                    connection.setRequestProperty("Accept", "text/html, */*");
                    connection.setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/124 Mobile Safari/537.36 StockUnified/0.3");
                    int code = connection.getResponseCode();
                    if (code < 300 || code >= 400) {
                        break;
                    }

                    String location = normalizeWhitespace(connection.getHeaderField("Location"));
                    if (location.isEmpty()) {
                        break;
                    }
                    current = new URL(new URL(current), location).toString();
                    if (!isGoogleNewsUrl(current)) {
                        return current;
                    }
                } catch (Exception ignored) {
                    break;
                } finally {
                    if (connection != null) {
                        connection.disconnect();
                    }
                }
            }
            return "";
        }

        private boolean isGoogleNewsUrl(String value) {
            try {
                String host = Uri.parse(value).getHost();
                return host != null && host.toLowerCase(Locale.US).contains("news.google.");
            } catch (Exception ignored) {
                return false;
            }
        }

        private String queryParameterUrl(String value, String parameterName) {
            try {
                String decoded = normalizeWhitespace(Uri.parse(value).getQueryParameter(parameterName));
                if (decoded.startsWith("http://") || decoded.startsWith("https://")) {
                    return decoded;
                }
            } catch (Exception ignored) {
                // Google News link formats vary; keep the RSS link if there is no direct URL.
            }
            return "";
        }

        private String buildArticleSummary(String symbol, String title, String description, JSONObject signalRow) {
            String body = stripHtml(description);
            String cleanTitle = normalizeWhitespace(title);
            if (body.length() < 35 || body.equalsIgnoreCase(cleanTitle)) {
                body = cleanTitle;
            }
            body = body.replace(cleanTitle, "").trim();
            if (body.length() < 35) {
                body = cleanTitle;
            }

            String summary = shorten(body, 210);
            if (signalRow == null) {
                return summary;
            }

            double score = signalRow.optDouble("confluence_score", 0.0);
            String scoreText = (score >= 0 ? "+" : "") + String.format(Locale.US, "%.2f", score);
            String trend = signalRow.optString("psar_trend", "neutral").toUpperCase(Locale.US);
            String context = " Matrix context: "
                    + normalizeDisplaySymbol(symbol)
                    + " is "
                    + trend
                    + " with AF "
                    + String.format(Locale.US, "%.2f", signalRow.optDouble("psar_af", 0.0))
                    + " and score "
                    + scoreText
                    + ".";
            return shorten(summary + context, 320);
        }

        private String inferNewsSentiment(String text) {
            String lower = text == null ? "" : text.toLowerCase(Locale.US);
            String[] positive = {"surge", "surges", "soar", "soars", "rally", "rallies", "rise", "rises", "gain", "gains", "profit", "beats", "upgrade", "order win", "record", "growth", "approval", "relief", "upper circuit", "buyback", "ban lifted", "restriction lifted"};
            String[] negative = {"fall", "falls", "fell", "drop", "drops", "crash", "crashes", "plunge", "plunges", "loss", "downgrade", "probe", "fraud", "miss", "decline", "sell", "weak", "penalty", "lower circuit", "restriction"};
            int score = 0;
            for (String word : positive) {
                if (containsPhrase(lower, word)) {
                    score += 1;
                }
            }
            for (String word : negative) {
                if (containsPhrase(lower, word)) {
                    score -= 1;
                }
            }
            if (containsAny(lower, "no ban", "ban lifted", "restriction lifted", "penalty withdrawn", "probe closed", "cleared of")) {
                score = Math.max(1, score + 2);
            }
            if (score > 0) {
                return "bullish";
            }
            if (score < 0) {
                return "bearish";
            }
            return "neutral";
        }

        private boolean isFreshPublication(String value, int maxHours) {
            String publishedAt = normalizeWhitespace(value);
            if (publishedAt.isEmpty()) {
                return false;
            }
            try {
                SimpleDateFormat format = new SimpleDateFormat("EEE, dd MMM yyyy HH:mm:ss z", Locale.US);
                format.setLenient(false);
                Date published = format.parse(publishedAt);
                if (published == null) {
                    return false;
                }
                long ageMs = System.currentTimeMillis() - published.getTime();
                return ageMs >= -6L * 60L * 60L * 1000L
                        && ageMs <= maxHours * 60L * 60L * 1000L;
            } catch (Exception ignored) {
                return false;
            }
        }

        private String stripHtml(String value) {
            String cleaned = value == null ? "" : value
                    .replaceAll("(?is)<script.*?</script>", " ")
                    .replaceAll("(?is)<style.*?</style>", " ")
                    .replaceAll("(?is)<[^>]+>", " ");
            cleaned = cleaned
                    .replace("&amp;", "&")
                    .replace("&quot;", "\"")
                    .replace("&#39;", "'")
                    .replace("&apos;", "'")
                    .replace("&nbsp;", " ")
                    .replace("&lt;", "<")
                    .replace("&gt;", ">");
            return normalizeWhitespace(cleaned);
        }

        private String normalizeWhitespace(String value) {
            return value == null ? "" : value.replaceAll("\\s+", " ").trim();
        }

        private String shorten(String value, int maxLength) {
            String text = normalizeWhitespace(value);
            if (text.length() <= maxLength) {
                return text;
            }
            int sentenceEnd = text.lastIndexOf(".", maxLength);
            if (sentenceEnd > 80) {
                return text.substring(0, sentenceEnd + 1).trim();
            }
            return text.substring(0, Math.max(0, maxLength - 3)).trim() + "...";
        }

        private String normalizeDisplaySymbol(String symbol) {
            String cleaned = symbol == null ? "" : symbol.trim().toUpperCase(Locale.US);
            if (cleaned.endsWith(".NS")) {
                cleaned = cleaned.substring(0, cleaned.length() - 3);
            }
            return cleaned.isEmpty() ? "RELIANCE" : cleaned;
        }

        private String resolveYahooSymbol(String displaySymbol) {
            String normalized = normalizeDisplaySymbol(displaySymbol);
            for (String[] ticker : STOCK_TICKERS) {
                if (ticker[1].equalsIgnoreCase(normalized) || ticker[0].equalsIgnoreCase(normalized)) {
                    return ticker[0];
                }
            }
            return normalized + ".NS";
        }

        private JSONObject buildDashboardJson(String customSymbolsJson) throws Exception {
            List<String[]> scanTickers = buildScanTickers(customSymbolsJson);
            List<JSONObject> rows = new ArrayList<>();
            int bullish = 0;
            int bearish = 0;
            double acTotal = 0.0;
            ExecutorService executor = Executors.newFixedThreadPool(Math.min(DASHBOARD_SCAN_THREADS, scanTickers.size()));
            CompletionService<Analysis> completion = new ExecutorCompletionService<>(executor);
            int submitted = 0;
            int completedFutures = 0;

            try {
                for (String[] ticker : scanTickers) {
                    completion.submit(() -> {
                        try {
                            return analyzeTicker(ticker[0], ticker[1]);
                        } catch (Exception ignored) {
                            return null;
                        }
                    });
                    submitted += 1;
                }

                long deadline = System.currentTimeMillis() + DASHBOARD_TOTAL_WAIT_MS;
                for (int completed = 0; completed < submitted; completed += 1) {
                    long waitMs = Math.max(0L, deadline - System.currentTimeMillis());
                    if (waitMs == 0L) {
                        break;
                    }
                    try {
                        Future<Analysis> future = completion.poll(waitMs, TimeUnit.MILLISECONDS);
                        if (future == null) {
                            break;
                        }
                        completedFutures += 1;
                        Analysis analysis = future.get();
                        if (analysis == null) {
                            continue;
                        }
                        JSONObject row = analysis.toPredictionJson();
                        rows.add(row);
                        acTotal += analysis.ac;
                        if ("BULL".equals(analysis.trend)) {
                            bullish += 1;
                        } else if ("BEAR".equals(analysis.trend)) {
                            bearish += 1;
                        }
                    } catch (Exception ignored) {
                        // Keep the app responsive if a single Yahoo symbol fails.
                    }
                }
            } finally {
                executor.shutdownNow();
            }

            Collections.sort(rows, (left, right) -> {
                boolean leftPriority = left.optBoolean("rsi_priority", false);
                boolean rightPriority = right.optBoolean("rsi_priority", false);
                if (leftPriority != rightPriority) {
                    return rightPriority ? 1 : -1;
                }
                return Double.compare(
                        right.optDouble("psar_af", 0.0),
                        left.optDouble("psar_af", 0.0)
                );
            });

            JSONArray predictions = new JSONArray();
            for (JSONObject row : rows) {
                predictions.put(row);
            }

            JSONObject summary = new JSONObject();
            summary.put("total_stocks", rows.size());
            summary.put("bullish", bullish);
            summary.put("bearish", bearish);
            summary.put("neutral", Math.max(0, rows.size() - bullish - bearish));
            summary.put("avg_ac", rows.isEmpty() ? 0.0 : round(acTotal / rows.size(), 4));

            JSONObject niftyJson;
            try {
                Analysis nifty = analyzeTicker("^NSEI", "NIFTY 50", true);
                niftyJson = nifty == null ? new JSONObject() : nifty.toNiftyJson();
                niftyJson.put("available", nifty != null);
                niftyJson.put("interval", "5m");
            } catch (Exception e) {
                niftyJson = new JSONObject();
                niftyJson.put("available", false);
                niftyJson.put("interval", "5m");
                niftyJson.put("status", "Five-minute candle unavailable");
            }
            JSONObject root = new JSONObject();
            root.put("nifty", niftyJson);
            root.put("top_predictions", predictions);
            root.put("technical_requested_count", submitted);
            root.put("technical_completed_count", completedFutures);
            root.put("technical_result_count", rows.size());
            root.put("technical_complete", rows.size() == submitted);
            JSONArray watchlistSymbols = new JSONArray();
            for (String[] ticker : scanTickers) {
                watchlistSymbols.put(ticker[1]);
            }
            root.put("watchlist_symbols", watchlistSymbols);
            JSONArray baseWatchlistSymbols = new JSONArray();
            for (String[] ticker : STOCK_TICKERS) {
                baseWatchlistSymbols.put(ticker[1]);
            }
            root.put("base_watchlist_symbols", baseWatchlistSymbols);
            root.put("market_summary", summary);
            root.put("latest_news", new JSONArray());
            root.put("news_status", "deferred");
            root.put("sector_analysis", new JSONArray());
            root.put("upcoming_events", buildUpcomingEvents());
            root.put("alerts", buildAlerts(rows));
            root.put("technical_updated", new SimpleDateFormat("HH:mm:ss", Locale.US).format(new Date()));
            root.put("technical_updated_at", isoNow());
            root.put("data_source", "Yahoo Finance on-device");
            root.put("custom_symbols", new JSONArray(normalizeSymbolListKey(customSymbolsJson)));
            return root;
        }

        private List<String[]> buildScanTickers(String customSymbolsJson) {
            Map<String, String[]> unique = new HashMap<>();
            List<String[]> tickers = new ArrayList<>();

            for (String[] ticker : STOCK_TICKERS) {
                addUniqueTicker(unique, tickers, ticker[0], ticker[1]);
            }

            try {
                JSONArray custom = new JSONArray(customSymbolsJson == null || customSymbolsJson.trim().isEmpty() ? "[]" : customSymbolsJson);
                for (int i = 0; i < custom.length(); i += 1) {
                    String display = normalizeDisplaySymbol(custom.optString(i, ""));
                    if (display.isEmpty()) {
                        continue;
                    }
                    addUniqueTicker(unique, tickers, resolveYahooSymbol(display), display);
                }
            } catch (Exception ignored) {
                // Invalid custom list should not break the default scanner.
            }

            return tickers;
        }

        private void addUniqueTicker(Map<String, String[]> unique, List<String[]> tickers, String yahooSymbol, String displaySymbol) {
            String normalizedDisplay = normalizeDisplaySymbol(displaySymbol);
            String normalizedYahoo = yahooSymbol == null ? "" : yahooSymbol.trim().toUpperCase(Locale.US);
            if (normalizedYahoo.isEmpty()) {
                normalizedYahoo = normalizedDisplay + ".NS";
            }
            String key = normalizedYahoo;
            if (unique.containsKey(key)) {
                return;
            }
            String[] ticker = new String[]{normalizedYahoo, normalizedDisplay};
            unique.put(key, ticker);
            tickers.add(ticker);
        }

        private String normalizeSymbolListKey(String customSymbolsJson) {
            try {
                JSONArray custom = new JSONArray(customSymbolsJson == null || customSymbolsJson.trim().isEmpty() ? "[]" : customSymbolsJson);
                List<String> symbols = new ArrayList<>();
                for (int i = 0; i < custom.length(); i += 1) {
                    String symbol = normalizeDisplaySymbol(custom.optString(i, ""));
                    if (!symbol.isEmpty() && !symbols.contains(symbol)) {
                        symbols.add(symbol);
                    }
                }
                Collections.sort(symbols);
                return new JSONArray(symbols).toString();
            } catch (Exception ignored) {
                return "[]";
            }
        }

        private List<JSONObject> parseRowsJson(String rowsJson) {
            List<JSONObject> rows = new ArrayList<>();
            try {
                JSONArray array = new JSONArray(rowsJson == null || rowsJson.trim().isEmpty() ? "[]" : rowsJson);
                for (int i = 0; i < array.length(); i += 1) {
                    JSONObject row = array.optJSONObject(i);
                    if (row == null || row.optString("symbol", "").trim().isEmpty()) {
                        continue;
                    }
                    rows.add(row);
                }
            } catch (Exception ignored) {
                // Invalid browser payload should not break the standalone app.
            }
            return rows;
        }

        private String normalizeIntelRowsKey(String rowsJson) {
            List<JSONObject> rows = parseRowsJson(rowsJson);
            Collections.sort(rows, (left, right) -> Double.compare(
                    intelRowPriority(right),
                    intelRowPriority(left)
            ));

            List<String> symbols = new ArrayList<>();
            int limit = Math.min(INTEL_SYMBOL_LIMIT, rows.size());
            for (int i = 0; i < limit; i += 1) {
                JSONObject row = rows.get(i);
                String symbol = normalizeDisplaySymbol(row.optString("symbol", ""));
                if (!symbol.isEmpty()) {
                    symbols.add(symbol);
                }
            }
            Collections.sort(symbols);
            return new JSONArray(symbols).toString();
        }

        private double intelRowPriority(JSONObject row) {
            double move = Math.min(35.0, Math.abs(row.optDouble("change_percent", 0.0))) / 10.0;
            double confluence = Math.abs(row.optDouble("confluence_score", 0.0));
            double acceleration = row.optDouble("psar_af", 0.0) * 2.0;
            return move + confluence + acceleration;
        }

        private JSONObject buildIntelligence(List<JSONObject> rows, boolean forceRefresh) throws Exception {
            JSONArray items = new JSONArray();
            JSONObject result = new JSONObject();
            JSONArray requestedSymbols = new JSONArray();
            JSONArray completedSymbols = new JSONArray();
            JSONArray failedSymbols = new JSONArray();
            JSONArray staleSymbols = new JSONArray();
            if (rows.isEmpty()) {
                return result
                        .put("items", items)
                        .put("status", "complete")
                        .put("requested_symbols", requestedSymbols)
                        .put("completed_symbols", completedSymbols)
                        .put("failed_symbols", failedSymbols)
                        .put("stale_symbols", staleSymbols);
            }

            List<JSONObject> rankedRows = new ArrayList<>(rows);
            Collections.sort(rankedRows, (left, right) -> Double.compare(
                    intelRowPriority(right),
                    intelRowPriority(left)
            ));

            int candidateCount = Math.min(INTEL_SYMBOL_LIMIT, rankedRows.size());
            ExecutorService executor = Executors.newFixedThreadPool(Math.min(4, Math.max(1, candidateCount)));
            CompletionService<JSONObject> completion = new ExecutorCompletionService<>(executor);
            int submitted = 0;

            try {
                for (int i = 0; i < candidateCount; i += 1) {
                    final JSONObject row = rankedRows.get(i);
                    requestedSymbols.put(normalizeDisplaySymbol(row.optString("symbol", "")));
                    completion.submit(() -> fetchNewsForRow(row, forceRefresh));
                    submitted += 1;
                }

                Set<String> seen = new HashSet<>();
                Set<String> respondedSymbols = new HashSet<>();
                long deadline = System.currentTimeMillis() + INTEL_TOTAL_WAIT_MS;
                for (int completed = 0; completed < submitted && items.length() < INTEL_ARTICLE_LIMIT; completed += 1) {
                    JSONObject batch;
                    long waitMs = Math.max(0L, deadline - System.currentTimeMillis());
                    if (waitMs == 0L) {
                        break;
                    }
                    try {
                        Future<JSONObject> future = completion.poll(waitMs, TimeUnit.MILLISECONDS);
                        if (future == null) {
                            break;
                        }
                        batch = future.get();
                    } catch (Exception ignored) {
                        batch = null;
                    }
                    if (batch == null) {
                        continue;
                    }
                    String symbol = batch.optString("symbol", "");
                    respondedSymbols.add(symbol);
                    boolean success = batch.optBoolean("success", false);
                    boolean stale = batch.optBoolean("stale", false);
                    if (success) {
                        completedSymbols.put(symbol);
                    } else {
                        failedSymbols.put(symbol);
                    }
                    if (stale) {
                        staleSymbols.put(symbol);
                    }
                    JSONArray articles = batch.optJSONArray("articles");
                    if (articles == null) {
                        articles = new JSONArray();
                    }
                    for (int i = 0; i < articles.length() && items.length() < INTEL_ARTICLE_LIMIT; i += 1) {
                        JSONObject article = articles.optJSONObject(i);
                        if (article == null) {
                            continue;
                        }
                        String key = normalizeWhitespace(article.optString("url", "") + " " + article.optString("title", ""))
                                .toLowerCase(Locale.US);
                        if (key.isEmpty() || seen.contains(key)) {
                            continue;
                        }
                        if (stale) {
                            article.put("stale", true);
                        }
                        seen.add(key);
                        items.put(article);
                    }
                    if (items.length() >= INTEL_ARTICLE_LIMIT) {
                        break;
                    }
                }
                for (int i = 0; i < requestedSymbols.length(); i += 1) {
                    String symbol = requestedSymbols.optString(i, "");
                    if (!symbol.isEmpty() && !respondedSymbols.contains(symbol)) {
                        failedSymbols.put(symbol);
                    }
                }
            } finally {
                executor.shutdownNow();
            }

            String status = failedSymbols.length() == 0
                    ? "complete"
                    : (items.length() > 0 ? "partial" : "failed");
            return result
                    .put("items", items)
                    .put("status", status)
                    .put("requested_symbols", requestedSymbols)
                    .put("completed_symbols", completedSymbols)
                    .put("failed_symbols", failedSymbols)
                    .put("stale_symbols", staleSymbols);
        }

        private JSONObject fetchNewsForRow(JSONObject row, boolean forceRefresh) {
            String symbol = normalizeDisplaySymbol(row.optString("symbol", ""));
            long now = System.currentTimeMillis();
            String cached = symbolNewsCache.get(symbol);
            Long cachedAt = symbolNewsCacheAt.get(symbol);
            try {
                if (!forceRefresh && cached != null && cachedAt != null && now - cachedAt < INTEL_CACHE_MS) {
                    return new JSONObject()
                            .put("symbol", symbol)
                            .put("success", true)
                            .put("cached", true)
                            .put("articles", new JSONArray(cached));
                }

                JSONArray articles = fetchNewsForSymbol(symbol, row, 2);
                symbolNewsCache.put(symbol, articles.toString());
                symbolNewsCacheAt.put(symbol, now);
                return new JSONObject()
                        .put("symbol", symbol)
                        .put("success", true)
                        .put("cached", false)
                        .put("articles", articles);
            } catch (Exception e) {
                try {
                    return new JSONObject()
                            .put("symbol", symbol)
                            .put("success", false)
                            .put("stale", cached != null)
                            .put("error", e.getMessage() == null ? "News source unavailable" : e.getMessage())
                            .put("articles", cached == null ? new JSONArray() : new JSONArray(cached));
                } catch (Exception ignored) {
                    return new JSONObject();
                }
            }
        }

        private JSONArray buildNewsActions(JSONArray articles, List<JSONObject> rows) throws Exception {
            JSONArray output = new JSONArray();
            if (articles == null || rows.isEmpty()) {
                return output;
            }

            Map<String, JSONObject> rowsBySymbol = new HashMap<>();
            for (JSONObject row : rows) {
                rowsBySymbol.put(normalizeDisplaySymbol(row.optString("symbol", "")), row);
            }

            Map<String, JSONObject> strongestBySymbol = new HashMap<>();
            for (int i = 0; i < articles.length(); i += 1) {
                JSONObject article = articles.optJSONObject(i);
                if (article == null) {
                    continue;
                }
                String rawSymbol = article.optString("symbol", "").trim();
                if (rawSymbol.isEmpty()) {
                    continue;
                }
                String symbol = normalizeDisplaySymbol(rawSymbol);
                JSONObject row = rowsBySymbol.get(symbol);
                if (row == null) {
                    continue;
                }

                JSONObject action = scoreNewsAction(article, row, rowsBySymbol);
                if (action == null) {
                    continue;
                }
                JSONObject current = strongestBySymbol.get(symbol);
                if (current == null
                        || action.optDouble("priority_score", 0.0) > current.optDouble("priority_score", 0.0)) {
                    strongestBySymbol.put(symbol, action);
                }
            }

            List<JSONObject> ranked = new ArrayList<>(strongestBySymbol.values());
            Collections.sort(ranked, (left, right) -> Double.compare(
                    right.optDouble("priority_score", 0.0),
                    left.optDouble("priority_score", 0.0)
            ));
            for (int i = 0; i < Math.min(8, ranked.size()); i += 1) {
                JSONObject action = ranked.get(i);
                action.remove("priority_score");
                output.put(action);
            }
            return output;
        }

        private JSONObject scoreNewsAction(
                JSONObject article,
                JSONObject row,
                Map<String, JSONObject> rowsBySymbol
        ) throws Exception {
            if (!isFreshPublication(article.optString("published_at", ""), 72)) {
                return null;
            }
            String title = normalizeWhitespace(article.optString("title", ""));
            String summary = normalizeWhitespace(article.optString("summary", ""));
            int contextIndex = summary.indexOf(" Matrix context:");
            if (contextIndex >= 0) {
                summary = summary.substring(0, contextIndex).trim();
            }
            String lower = (title + " " + summary).toLowerCase(Locale.US);

            boolean regulatory = containsAny(lower,
                    "irdai", "irda", "sebi", "rbi", "regulator", "regulatory", "regulation",
                    "consultation paper", "commission cap", "policy change", "court", "tribunal",
                    "show-cause", "show cause", "penalty", "fine", "ban", "restriction", "licence", "license");
            boolean earnings = containsAny(lower,
                    "quarter", "results", "earnings", "revenue", "profit", "loss", "margin", "guidance", "ebitda");
            boolean corporate = containsAny(lower,
                    "order win", "contract", "acquisition", "merger", "stake sale", "buyback", "dividend",
                    "fundraise", "fund raising", "default", "insolvency", "resigns", "resignation");
            boolean rating = containsAny(lower,
                    "upgrade", "downgrade", "target price", "price target", "brokerage", "overweight", "underweight");
            boolean shock = containsAny(lower,
                    "crash", "plunge", "tumble", "slump", "surge", "soar", "lower circuit", "upper circuit");
            double changePercent = row.optDouble("change_percent", 0.0);
            if (!regulatory && !earnings && !corporate && !rating && !shock && Math.abs(changePercent) < 4.0) {
                return null;
            }

            int positiveHits = countKeywordHits(lower,
                    "surge", "surges", "soar", "soars", "rally", "rallies", "rise", "rises", "gain", "gains", "beats", "upgrade", "order win", "approval",
                    "relief", "record profit", "raises guidance", "upper circuit", "buyback");
            int negativeHits = countKeywordHits(lower,
                    "fall", "falls", "fell", "drop", "drops", "crash", "crashes", "plunge", "plunges", "tumble", "tumbles", "slump", "loss", "miss",
                    "downgrade", "underweight", "probe", "fraud", "penalty", "fine", "ban", "restriction",
                    "default", "lower circuit", "cuts guidance", "commission cap");
            boolean negatedRisk = containsAny(lower,
                    "no ban", "ban lifted", "restriction lifted", "penalty withdrawn", "probe closed", "cleared of");
            if (negatedRisk) {
                positiveHits += 3;
                negativeHits = Math.max(0, negativeHits - 2);
            }
            String sentiment = inferNewsSentiment(lower);
            int direction = positiveHits > negativeHits ? 1 : (negativeHits > positiveHits ? -1 : 0);
            if (direction == 0) {
                direction = "bullish".equals(sentiment) ? 1 : ("bearish".equals(sentiment) ? -1 : 0);
            }

            boolean severe = shock
                    || containsAny(lower, "fraud", "ban", "default", "lower circuit", "upper circuit", "commission cap")
                    || Math.abs(changePercent) >= 8.0;
            if (negatedRisk) {
                severe = Math.abs(changePercent) >= 8.0;
            }
            String catalyst = regulatory
                    ? "Regulatory"
                    : earnings
                    ? "Earnings"
                    : corporate
                    ? "Corporate"
                    : rating
                    ? "Broker action"
                    : "Price shock";

            double impactMin;
            double impactMax;
            if (direction < 0) {
                if (regulatory && severe) {
                    impactMin = -22.0;
                    impactMax = -8.0;
                } else if (regulatory) {
                    impactMin = -14.0;
                    impactMax = -5.0;
                } else if (severe) {
                    impactMin = -18.0;
                    impactMax = -7.0;
                } else if (earnings) {
                    impactMin = -10.0;
                    impactMax = -3.5;
                } else {
                    impactMin = -7.0;
                    impactMax = -2.0;
                }
            } else if (direction > 0) {
                if (regulatory || severe) {
                    impactMin = 4.0;
                    impactMax = 14.0;
                } else if (earnings || corporate) {
                    impactMin = 3.0;
                    impactMax = 10.0;
                } else {
                    impactMin = 2.0;
                    impactMax = 7.0;
                }
            } else {
                impactMin = -2.5;
                impactMax = 2.5;
            }

            String symbol = normalizeDisplaySymbol(row.optString("symbol", ""));
            double sensitivity = newsSensitivity(symbol, lower);
            impactMin *= sensitivity;
            impactMax *= sensitivity;
            if (direction < 0 && changePercent < 0.0) {
                impactMin = Math.min(impactMin, changePercent * 1.08);
                impactMax = Math.min(impactMax, changePercent * 0.55);
            } else if (direction > 0 && changePercent > 0.0) {
                impactMin = Math.max(impactMin, changePercent * 0.55);
                impactMax = Math.max(impactMax, changePercent * 1.08);
            }

            String trend = row.optString("psar_trend", row.optString("prediction", "neutral")).toLowerCase(Locale.US);
            boolean priceAligned = (direction < 0 && changePercent < -0.5) || (direction > 0 && changePercent > 0.5);
            boolean trendAligned = (direction < 0 && trend.contains("bear")) || (direction > 0 && trend.contains("bull"));
            double probability = 43.0;
            probability += regulatory ? 12.0 : 0.0;
            probability += earnings || corporate || rating ? 7.0 : 0.0;
            probability += severe ? 8.0 : 0.0;
            probability += priceAligned ? 10.0 : -6.0;
            probability += trendAligned ? 7.0 : -3.0;
            probability += Math.abs(changePercent) >= 3.0 ? 4.0 : 0.0;
            double rsi = row.optDouble("rsi", Double.NaN);
            if ((direction > 0 && Double.isFinite(rsi) && rsi >= 70.0)
                    || (direction < 0 && Double.isFinite(rsi) && rsi <= 30.0)) {
                probability -= 8.0;
            }
            if (direction == 0) {
                probability = Math.min(probability, 48.0);
            }
            probability = clamp(probability, 35.0, 84.0);

            double maxImpact = Math.max(Math.abs(impactMin), Math.abs(impactMax));
            String priority = probability >= 68.0 || maxImpact >= 15.0
                    ? "high"
                    : (probability >= 56.0 || maxImpact >= 7.0 ? "medium" : "low");
            String action;
            String strategy;
            if (direction < 0) {
                if (changePercent <= -8.0) {
                    action = "WAIT / SELL BOUNCE";
                    strategy = "Do not chase the first collapse. Wait for a weak bounce, then act only below the bounce low. Keep the stop above the news-day high and scale out into the model impact range.";
                } else if (trend.contains("bear")) {
                    action = "AVOID / SHORT";
                    strategy = "Avoid fresh longs. Consider bearish exposure only after a confirmed break of the prior low, with a stop above the prior close or PSAR.";
                } else {
                    action = "WAIT FOR BREAKDOWN";
                    strategy = "News is negative but price confirmation is incomplete. Wait for a close below support; cancel the setup if price reclaims the prior close.";
                }
            } else if (direction > 0) {
                if (changePercent >= 8.0) {
                    action = "WAIT FOR PULLBACK";
                    strategy = "Avoid chasing the opening spike. Prefer a pullback that holds above the prior close, with a stop below the news-day low or PSAR.";
                } else if (trend.contains("bull")) {
                    action = "BUY ON HOLD";
                    strategy = "Use a pullback or breakout retest as entry confirmation. Keep the stop below the news-day low or PSAR and scale out toward the upper impact estimate.";
                } else {
                    action = "WATCH BREAKOUT";
                    strategy = "Catalyst is positive but trend confirmation is missing. Enter only if price holds above resistance with volume; cancel below the prior close.";
                }
            } else {
                action = "NO TRADE";
                strategy = "The headline has no reliable directional edge yet. Wait for price, volume, and trend to agree before taking risk.";
            }

            JSONObject actionJson = new JSONObject();
            actionJson.put("symbol", symbol);
            actionJson.put("priority", priority);
            actionJson.put("action", action);
            actionJson.put("direction", direction < 0 ? "bearish" : (direction > 0 ? "bullish" : "neutral"));
            actionJson.put("catalyst", catalyst);
            actionJson.put("setup_score", Math.round(probability));
            actionJson.put("score_method", "Uncalibrated heuristic confidence, not an outcome probability");
            actionJson.put("impact_min_percent", round(Math.min(impactMin, impactMax), 1));
            actionJson.put("impact_max_percent", round(Math.max(impactMin, impactMax), 1));
            actionJson.put("time_horizon", "1-3 sessions");
            actionJson.put("current_price", round(row.optDouble("ltp", 0.0), 2));
            actionJson.put("change_percent", round(changePercent, 2));
            actionJson.put("strategy", strategy);
            actionJson.put("headline", title);
            actionJson.put("source", article.optString("source", "Google News"));
            actionJson.put("url", article.optString("original_url", article.optString("url", "")));
            actionJson.put("published_at", article.optString("published_at", ""));
            actionJson.put("related_symbols", relatedSymbolsForNews(lower, symbol, rowsBySymbol));
            appendTradePlan(
                    actionJson,
                    row,
                    direction,
                    impactMin,
                    impactMax,
                    changePercent,
                    action
            );
            actionJson.put("risk_note", "The score is an uncalibrated heuristic, not a win probability. Model zones are not guaranteed returns; confirm price, volume, spread, and liquidity.");
            actionJson.put("priority_score", probability + maxImpact + ("high".equals(priority) ? 12.0 : 0.0));
            return actionJson;
        }

        private void appendTradePlan(
                JSONObject actionJson,
                JSONObject row,
                int direction,
                double impactMin,
                double impactMax,
                double changePercent,
                String action
        ) throws Exception {
            double currentPrice = row.optDouble("ltp", 0.0);
            if (direction == 0 || currentPrice <= 0.0) {
                actionJson.put("stock_side", "NO TRADE");
                actionJson.put("option_side", "NO TRADE");
                return;
            }

            boolean bullish = direction > 0;
            boolean waitForPullback = bullish && action.contains("PULLBACK");
            boolean sellBounce = !bullish && action.contains("SELL BOUNCE");
            double entryLow;
            double entryHigh;
            String entryCondition;
            if (waitForPullback) {
                entryLow = currentPrice * 0.97;
                entryHigh = currentPrice * 0.99;
                entryCondition = "Buy only after the pullback stabilizes inside the zone and price turns back up.";
            } else if (sellBounce) {
                entryLow = currentPrice * 1.02;
                entryHigh = currentPrice * 1.05;
                entryCondition = "Short or buy puts only if a weak bounce rejects inside the zone.";
            } else {
                entryLow = currentPrice * 0.995;
                entryHigh = currentPrice * 1.005;
                entryCondition = bullish
                        ? "Enter only after price holds the entry zone with bullish volume confirmation."
                        : "Enter bearish exposure only after price loses the entry zone with volume confirmation.";
            }

            double previousClose = Double.NaN;
            double change = row.optDouble("change", Double.NaN);
            if (Double.isFinite(change) && currentPrice - change > 0.0) {
                previousClose = currentPrice - change;
            } else if (changePercent > -99.0) {
                previousClose = currentPrice / (1.0 + changePercent / 100.0);
            }
            if (!Double.isFinite(previousClose) || previousClose <= 0.0) {
                actionJson.put("stock_side", "NO TRADE");
                actionJson.put("option_side", "NO TRADE");
                actionJson.put("entry_condition", "Previous-session reference is unavailable; no price targets are issued.");
                return;
            }

            double totalImpactPercent = bullish
                    ? Math.max(impactMin, impactMax)
                    : Math.min(impactMin, impactMax);
            double modelBound = previousClose * (1.0 + totalImpactPercent / 100.0);
            boolean moveSpent = bullish
                    ? currentPrice >= modelBound * 0.995
                    : currentPrice <= modelBound * 1.005;
            double riskPercent = clamp(1.8 + Math.abs(changePercent) * 0.08, 1.8, 4.8);
            double entryAnchor = (entryLow + entryHigh) / 2.0;
            boolean invalidBound = bullish ? modelBound <= entryAnchor : modelBound >= entryAnchor;

            actionJson.put("model_reference_price", round(previousClose, 2));
            actionJson.put("model_bound_price", round(modelBound, 2));
            if (moveSpent || invalidBound) {
                actionJson.put("action", "MOVE SPENT / NO TRADE");
                actionJson.put("stock_side", "NO TRADE");
                actionJson.put("option_side", "NO TRADE");
                actionJson.put("model_exhausted", true);
                actionJson.put("entry_condition", "Current price has already consumed the modeled catalyst range. Wait for a new setup or updated news.");
                actionJson.put("strategy", "Do not chase an exhausted catalyst move. Reassess only after a new base, fresh news, and updated price confirmation.");
                return;
            }

            double stopLoss = bullish
                    ? entryLow * (1.0 - riskPercent / 100.0)
                    : entryHigh * (1.0 + riskPercent / 100.0);
            double targetOne = entryAnchor + (modelBound - entryAnchor) * 0.35;
            double targetTwo = entryAnchor + (modelBound - entryAnchor) * 0.65;
            double targetRunner = modelBound;

            actionJson.put("stock_side", bullish ? "BUY" : "SELL / SHORT");
            actionJson.put("stock_entry_low", round(entryLow, 2));
            actionJson.put("stock_entry_high", round(entryHigh, 2));
            actionJson.put("stock_stop_loss", round(stopLoss, 2));
            actionJson.put("stock_target_1", round(targetOne, 2));
            actionJson.put("stock_target_2", round(targetTwo, 2));
            actionJson.put("stock_target_runner", round(targetRunner, 2));
            actionJson.put("entry_condition", entryCondition);
            actionJson.put("profit_booking", "Book 35% at T1, 35% at T2, and trail the final 30% toward the runner target.");
            actionJson.put("invalidation", bullish
                    ? "Exit if price closes below the stop or the catalyst is contradicted."
                    : "Exit if price closes above the stop or the catalyst is contradicted.");

            actionJson.put("option_side", bullish ? "BUY CALL" : "BUY PUT");
            actionJson.put("option_contract", "Nearest monthly ATM or 1-step ITM contract with liquid OI and spread at or below 5%.");
            actionJson.put("option_stop_percent", -25);
            actionJson.put("option_target_1_percent", 20);
            actionJson.put("option_target_2_percent", 40);
            actionJson.put("option_target_runner_percent", 65);
            actionJson.put("option_profit_booking", "Book 40% at option T1, 35% at T2, and trail 25% toward the runner target.");
            actionJson.put("option_risk_note", "Premium exits are percentages from actual fill. Live strike, premium, IV, OI, and spread require an option-chain feed; event IV can collapse after the news.");
        }

        private double newsSensitivity(String symbol, String lower) {
            boolean insuranceNews = containsAny(lower, "irdai", "irda", "insurance", "commission cap");
            if (!insuranceNews) {
                return 1.0;
            }
            if ("POLICYBZR".equals(symbol)) {
                return 1.55;
            }
            if (containsAny(symbol, "HDFCLIFE", "ICICIPRULI", "ICICIGI", "SBILIFE", "LICI", "STARHEALTH", "NIVABUPA")) {
                return 0.55;
            }
            if ("NAUKRI".equals(symbol)) {
                return 0.45;
            }
            return 0.8;
        }

        private JSONArray relatedSymbolsForNews(
                String lower,
                String primary,
                Map<String, JSONObject> rowsBySymbol
        ) {
            List<String> candidates = new ArrayList<>();
            candidates.add(primary);
            if (containsAny(lower, "irdai", "irda", "insurance", "commission cap")) {
                Collections.addAll(candidates,
                        "POLICYBZR", "HDFCLIFE", "ICICIPRULI", "ICICIGI", "SBILIFE", "LICI", "STARHEALTH", "NIVABUPA", "NAUKRI");
            } else if (containsAny(lower, "rbi", "bank", "repo rate")) {
                Collections.addAll(candidates, "HDFCBANK", "KOTAKBANK", "SBIN", "PNB", "YESBANK", "INDUSINDBK");
            } else if (containsAny(lower, "crude", "oil", "opec")) {
                Collections.addAll(candidates, "RELIANCE", "ONGC", "OIL", "HINDPETRO");
            } else if (containsAny(lower, "defence", "defense", "missile", "warship")) {
                Collections.addAll(candidates, "BEL", "HAL", "MAZDOCK", "BDL", "GRSE");
            } else if (containsAny(lower, "telecom", "spectrum", "5g")) {
                Collections.addAll(candidates, "BHARTIARTL", "IDEA", "TEJASNET", "TATACOMM");
            }

            JSONArray related = new JSONArray();
            Set<String> seen = new HashSet<>();
            for (String candidate : candidates) {
                if (rowsBySymbol.containsKey(candidate) && seen.add(candidate)) {
                    related.put(candidate);
                    if (related.length() >= 6) {
                        break;
                    }
                }
            }
            return related;
        }

        private boolean containsAny(String text, String... needles) {
            String value = text == null ? "" : text.toLowerCase(Locale.US);
            for (String needle : needles) {
                if (containsPhrase(value, needle)) {
                    return true;
                }
            }
            return false;
        }

        private boolean containsPhrase(String text, String needle) {
            String value = text == null ? "" : text.toLowerCase(Locale.US);
            String phrase = needle == null ? "" : needle.toLowerCase(Locale.US).trim();
            if (phrase.isEmpty()) {
                return false;
            }
            String expression = "(?<![a-z0-9])"
                    + java.util.regex.Pattern.quote(phrase)
                    + "(?![a-z0-9])";
            return java.util.regex.Pattern.compile(expression).matcher(value).find();
        }

        private int countKeywordHits(String text, String... needles) {
            int count = 0;
            for (String needle : needles) {
                if (containsPhrase(text, needle)) {
                    count += 1;
                }
            }
            return count;
        }

        private JSONArray buildAlerts(List<JSONObject> rows) throws Exception {
            JSONArray alerts = new JSONArray();
            String now = isoNow();
            int count = 0;

            appendEventAlerts(alerts, now);

            for (JSONObject row : rows) {
                double score = row.optDouble("confluence_score", 0.0);
                if (Math.abs(score) < 0.45) {
                    continue;
                }

                JSONObject alert = new JSONObject();
                String symbol = row.optString("symbol", "Ticker");
                String signal = row.optString("signal_strength", "NEUTRAL").replace("_", " ");
                alert.put("severity", Math.abs(score) >= 0.70 ? "high" : "medium");
                alert.put("title", symbol + " " + signal);
                alert.put("message", "On-device Yahoo signal score "
                        + String.format(Locale.US, "%.2f", score)
                        + " with LTP INR " + String.format(Locale.US, "%.2f", row.optDouble("ltp", 0.0)));
                alert.put("timestamp", now);
                alert.put("symbol", row.optString("symbol", ""));
                alerts.put(alert);
                count += 1;
                if (count >= 6) {
                    break;
                }
            }

            return alerts;
        }

        private JSONArray buildUpcomingEvents() throws Exception {
            JSONArray events = new JSONArray();
            Calendar today = istToday();

            for (String[] event : MARKET_EVENTS) {
                Calendar eventDate = parseMarketEventDate(event[2]);
                int daysUntil = daysBetween(today, eventDate);
                if (daysUntil < 0) {
                    continue;
                }

                JSONObject item = new JSONObject();
                item.put("id", event[0]);
                item.put("title", event[1]);
                item.put("date", event[2]);
                item.put("category", event[3]);
                item.put("impact", event[4]);
                item.put("note", event[5]);
                item.put("days_until", daysUntil);
                item.put("alert_on", formatMarketEventDate(addDays(eventDate, -1)));
                item.put("source", "Built-in major market calendar");
                events.put(item);

                if (events.length() >= 8) {
                    break;
                }
            }

            return events;
        }

        private void appendEventAlerts(JSONArray alerts, String now) throws Exception {
            JSONArray events = buildUpcomingEvents();
            for (int i = 0; i < events.length(); i += 1) {
                JSONObject event = events.optJSONObject(i);
                if (event == null || event.optInt("days_until", -1) != 1) {
                    continue;
                }

                JSONObject alert = new JSONObject();
                String impact = event.optString("impact", "medium");
                alert.put("severity", "high".equals(impact) ? "high" : "medium");
                alert.put("title", "Event tomorrow: " + event.optString("title", "Market event"));
                alert.put("message", event.optString("date", "") + " | " + event.optString("note", ""));
                alert.put("timestamp", now);
                alert.put("category", "event");
                alert.put("event_id", event.optString("id", ""));
                alerts.put(alert);
            }
        }

        private String withFreshDashboardQuotes(String payload, String customSymbolsJson) {
            try {
                JSONObject root = new JSONObject(payload);
                List<String[]> scanTickers = buildScanTickers(customSymbolsJson);
                List<String> symbols = new ArrayList<>();
                for (String[] ticker : scanTickers) {
                    symbols.add(ticker[0]);
                }
                symbols.add("^NSEI");

                Map<String, QuoteSnapshot> snapshots = getQuoteSnapshots(symbols);
                long latestEpoch = 0L;

                JSONArray rows = root.optJSONArray("top_predictions");
                if (rows != null) {
                    for (int i = 0; i < rows.length(); i += 1) {
                        JSONObject row = rows.optJSONObject(i);
                        if (row == null) {
                            continue;
                        }
                        QuoteSnapshot snapshot = snapshots.get(normalizeQuoteSymbol(resolveYahooSymbol(row.optString("symbol", ""))));
                        if (applyQuoteSnapshot(row, snapshot)) {
                            latestEpoch = Math.max(latestEpoch, snapshot.marketTime);
                        }
                    }
                }

                JSONArray watchlistSymbols = new JSONArray();
                JSONArray watchlistQuotes = new JSONArray();
                for (String[] ticker : scanTickers) {
                    String yahooSymbol = ticker[0];
                    String displaySymbol = ticker[1];
                    watchlistSymbols.put(displaySymbol);
                    JSONObject quote = new JSONObject();
                    quote.put("symbol", displaySymbol);
                    QuoteSnapshot snapshot = snapshots.get(normalizeQuoteSymbol(yahooSymbol));
                    boolean available = snapshot != null && snapshot.hasPrice();
                    quote.put("available", available);
                    if (available) {
                        quote.put("ltp", round(snapshot.price, 2));
                        if (Double.isFinite(snapshot.change)) {
                            quote.put("change", round(snapshot.change, 2));
                        }
                        if (Double.isFinite(snapshot.changePercent)) {
                            quote.put("change_percent", round(snapshot.changePercent, 2));
                        }
                        if (snapshot.marketTime > 0L) {
                            quote.put("quote_epoch", snapshot.marketTime);
                            quote.put("quote_time", formatEpochTime(snapshot.marketTime));
                            quote.put("quote_timestamp", formatEpochIso(snapshot.marketTime));
                            latestEpoch = Math.max(latestEpoch, snapshot.marketTime);
                        }
                        if (snapshot.volume > 0L) {
                            quote.put("session_volume", snapshot.volume);
                            quote.put("turnover_estimate", round(snapshot.price * snapshot.volume, 2));
                        }
                        quote.put("quote_source", snapshot.source);
                    }
                    watchlistQuotes.put(quote);
                }
                root.put("watchlist_symbols", watchlistSymbols);
                root.put("watchlist_quotes", watchlistQuotes);
                JSONArray baseWatchlistSymbols = new JSONArray();
                for (String[] ticker : STOCK_TICKERS) {
                    baseWatchlistSymbols.put(ticker[1]);
                }
                root.put("base_watchlist_symbols", baseWatchlistSymbols);

                if (latestEpoch > 0L) {
                    root.put("quote_epoch", latestEpoch);
                    root.put("quote_timestamp", formatEpochIso(latestEpoch));
                    root.put("quote_updated", formatEpochTime(latestEpoch));
                }
                root.put("quote_refresh_interval_seconds", QUOTE_CACHE_MS / 1000L);
                return root.toString();
            } catch (Exception ignored) {
                return payload;
            }
        }

        private boolean applyQuoteSnapshot(JSONObject row, QuoteSnapshot snapshot) throws Exception {
            if (row == null
                    || snapshot == null
                    || !snapshot.hasPrice()
                    || !Double.isFinite(snapshot.change)
                    || !Double.isFinite(snapshot.changePercent)) {
                return false;
            }

            row.put("ltp", round(snapshot.price, 2));
            row.put("change", round(snapshot.change, 2));
            row.put("change_percent", round(snapshot.changePercent, 2));
            if (snapshot.volume > 0L) {
                row.put("session_volume", snapshot.volume);
                row.put("turnover_estimate", round(snapshot.price * snapshot.volume, 2));
            }
            if (snapshot.marketTime > 0L) {
                row.put("quote_epoch", snapshot.marketTime);
                row.put("quote_time", formatEpochTime(snapshot.marketTime));
                row.put("quote_timestamp", formatEpochIso(snapshot.marketTime));
            }
            row.put("quote_source", "Yahoo Finance quote");
            return true;
        }

        private Map<String, QuoteSnapshot> getQuoteSnapshots(List<String> symbols) {
            List<String> normalized = new ArrayList<>();
            Set<String> seen = new HashSet<>();
            for (String symbol : symbols) {
                String clean = normalizeQuoteSymbol(symbol);
                if (!clean.isEmpty() && seen.add(clean)) {
                    normalized.add(clean);
                }
            }
            Collections.sort(normalized);
            String cacheKey = joinQuoteSymbols(normalized);
            long now = System.currentTimeMillis();
            if (quoteSnapshotCacheKey.equals(cacheKey)
                    && !quoteSnapshotCache.isEmpty()
                    && now - quoteSnapshotCacheAt < QUOTE_CACHE_MS) {
                return quoteSnapshotCache;
            }

            Map<String, QuoteSnapshot> snapshots = new HashMap<>();
            long deadline = System.currentTimeMillis() + 12_000L;
            for (List<String> batch : chunkStrings(normalized, QUOTE_BATCH_SIZE)) {
                if (System.currentTimeMillis() >= deadline) {
                    break;
                }
                int countBeforeBatch = snapshots.size();
                try {
                    String url = "https://query2.finance.yahoo.com/v7/finance/spark?symbols="
                            + encodeQuoteSymbols(batch)
                            + "&range=1d&interval=1m";
                    int timeoutMs = (int) Math.max(500L, Math.min(4_000L, deadline - System.currentTimeMillis()));
                    String body = fetchUrl(url, timeoutMs);
                    JSONObject spark = new JSONObject(body).optJSONObject("spark");
                    JSONArray results = spark == null ? null : spark.optJSONArray("result");
                    if (results != null) {
                        for (int i = 0; i < results.length(); i += 1) {
                            JSONObject item = results.optJSONObject(i);
                            if (item == null) {
                                continue;
                            }
                            JSONArray responses = item.optJSONArray("response");
                            JSONObject response = responses == null ? null : responses.optJSONObject(0);
                            JSONObject meta = response == null ? null : response.optJSONObject("meta");
                            if (meta == null) {
                                continue;
                            }
                            QuoteSnapshot snapshot = new QuoteSnapshot();
                            snapshot.symbol = normalizeQuoteSymbol(item.optString("symbol", meta.optString("symbol", "")));
                            snapshot.price = firstFinite(
                                    optFinite(meta, "fulldayPrice", Double.NaN),
                                    optFinite(meta, "regularMarketPrice", Double.NaN)
                            );
                            snapshot.change = firstFinite(
                                    optFinite(meta, "fulldayChange", Double.NaN),
                                    optFinite(meta, "regularMarketChange", Double.NaN)
                            );
                            snapshot.changePercent = firstFinite(
                                    optFinite(meta, "fulldayChangePercent", Double.NaN),
                                    optFinite(meta, "regularMarketChangePercent", Double.NaN)
                            );
                            snapshot.volume = firstPositiveLong(
                                    meta.optLong("fulldayVolume", 0L),
                                    meta.optLong("regularMarketVolume", 0L),
                                    intradayVolume(response)
                            );
                            snapshot.marketTime = meta.optLong("regularMarketTime", 0L);
                            snapshot.source = "Yahoo Finance spark 1m";
                            if (!snapshot.symbol.isEmpty() && snapshot.hasPrice()) {
                                snapshots.put(snapshot.symbol, snapshot);
                            }
                        }
                    }
                } catch (Exception ignored) {
                    // Fall through to the legacy quote endpoint for this batch.
                }

                if (snapshots.size() > countBeforeBatch) {
                    continue;
                }
                if (System.currentTimeMillis() >= deadline) {
                    break;
                }
                try {
                    String url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=" + encodeQuoteSymbols(batch);
                    int timeoutMs = (int) Math.max(500L, Math.min(4_000L, deadline - System.currentTimeMillis()));
                    String body = fetchUrl(url, timeoutMs);
                    JSONObject response = new JSONObject(body).optJSONObject("quoteResponse");
                    JSONArray results = response == null ? null : response.optJSONArray("result");
                    if (results == null) {
                        continue;
                    }
                    for (int i = 0; i < results.length(); i += 1) {
                        JSONObject item = results.optJSONObject(i);
                        if (item == null) {
                            continue;
                        }
                        QuoteSnapshot snapshot = new QuoteSnapshot();
                        snapshot.symbol = normalizeQuoteSymbol(item.optString("symbol", ""));
                        snapshot.price = optFinite(item, "regularMarketPrice", Double.NaN);
                        snapshot.change = optFinite(item, "regularMarketChange", Double.NaN);
                        snapshot.changePercent = optFinite(item, "regularMarketChangePercent", Double.NaN);
                        snapshot.volume = item.optLong("regularMarketVolume", 0L);
                        snapshot.marketTime = item.optLong("regularMarketTime", 0L);
                        snapshot.source = "Yahoo Finance quote";
                        if (!snapshot.symbol.isEmpty() && snapshot.hasPrice()) {
                            snapshots.put(snapshot.symbol, snapshot);
                        }
                    }
                } catch (Exception ignored) {
                    // Quote snapshots are opportunistic; chart data remains the fallback.
                }
            }

            if (snapshots.isEmpty() && quoteSnapshotCacheKey.equals(cacheKey) && !quoteSnapshotCache.isEmpty()) {
                return quoteSnapshotCache;
            }

            quoteSnapshotCache = snapshots;
            quoteSnapshotCacheAt = now;
            quoteSnapshotCacheKey = cacheKey;
            return quoteSnapshotCache;
        }

        private long intradayVolume(JSONObject response) {
            if (response == null) {
                return 0L;
            }
            JSONObject indicators = response.optJSONObject("indicators");
            JSONArray quoteSeries = indicators == null ? null : indicators.optJSONArray("quote");
            JSONObject quote = quoteSeries == null ? null : quoteSeries.optJSONObject(0);
            JSONArray volumes = quote == null ? null : quote.optJSONArray("volume");
            if (volumes == null) {
                return 0L;
            }
            long total = 0L;
            for (int i = 0; i < volumes.length(); i += 1) {
                if (volumes.isNull(i)) {
                    continue;
                }
                long value = volumes.optLong(i, 0L);
                if (value > 0L && Long.MAX_VALUE - total >= value) {
                    total += value;
                }
            }
            return total;
        }

        private long firstPositiveLong(long... values) {
            for (long value : values) {
                if (value > 0L) {
                    return value;
                }
            }
            return 0L;
        }

        private String encodeQuoteSymbols(List<String> symbols) throws Exception {
            StringBuilder builder = new StringBuilder();
            for (String symbol : symbols) {
                if (builder.length() > 0) {
                    builder.append(",");
                }
                builder.append(URLEncoder.encode(symbol, StandardCharsets.UTF_8.name()));
            }
            return builder.toString();
        }

        private String joinQuoteSymbols(List<String> symbols) {
            StringBuilder builder = new StringBuilder();
            for (String symbol : symbols) {
                if (builder.length() > 0) {
                    builder.append(",");
                }
                builder.append(symbol);
            }
            return builder.toString();
        }

        private String normalizeQuoteSymbol(String symbol) {
            return symbol == null ? "" : symbol.trim().toUpperCase(Locale.US);
        }

        private JSONObject buildQuoteJson(
                String yahooSymbol,
                String label,
                String currency,
                QuoteSnapshot snapshot
        ) throws Exception {
            Series series = null;
            try {
                series = fetchQuoteSeries(yahooSymbol);
            } catch (Exception chartError) {
                if (snapshot == null || !snapshot.hasPrice()) {
                    throw chartError;
                }
            }

            double latest = snapshot != null && snapshot.hasPrice() ? snapshot.price : series.lastClose();
            long quoteEpoch = snapshot != null ? snapshot.marketTime : series.latestCandleEpochSeconds();
            String source = snapshot != null ? snapshot.source : "Yahoo Finance 1m extended";
            double previous = series == null ? Double.NaN : series.previousSessionClose();

            if (series != null && series.latestCandleEpochSeconds() >= quoteEpoch) {
                latest = series.lastClose();
                quoteEpoch = series.latestCandleEpochSeconds();
                source = "Yahoo Finance 1m extended";
            }
            if (series != null && series.regularMarketTime > quoteEpoch && Double.isFinite(series.regularMarketPrice)) {
                latest = series.regularMarketPrice;
                quoteEpoch = series.regularMarketTime;
                source = series.sourceLabel();
            }
            if (snapshot != null && snapshot.hasPrice() && snapshot.marketTime > quoteEpoch) {
                latest = snapshot.price;
                quoteEpoch = snapshot.marketTime;
                source = snapshot.source;
            }
            double change = previous > 0
                    ? latest - previous
                    : (snapshot != null && Double.isFinite(snapshot.change) ? snapshot.change : 0.0);
            double changePercent = previous > 0
                    ? (change / previous) * 100.0
                    : (snapshot != null && Double.isFinite(snapshot.changePercent) ? snapshot.changePercent : 0.0);

            JSONObject quote = new JSONObject();
            quote.put("available", true);
            quote.put("symbol", yahooSymbol);
            quote.put("label", label);
            quote.put("value", round(latest, "USDINR=X".equals(yahooSymbol) ? 4 : 2));
            quote.put("change", round(change, 4));
            quote.put("change_percent", round(changePercent, 3));
            quote.put("currency", currency);
            quote.put("source", source);
            quote.put("timestamp", quoteEpoch > 0L ? formatEpochIso(quoteEpoch) : isoNow());
            quote.put("quote_time", quoteEpoch > 0L ? formatEpochTime(quoteEpoch) : "");
            quote.put("refresh_interval_seconds", MACRO_CACHE_MS / 1000L);
            return quote;
        }

        private JSONObject buildQuoteJsonSafe(
                String yahooSymbol,
                String label,
                String currency,
                QuoteSnapshot snapshot
        ) throws Exception {
            try {
                return buildQuoteJson(yahooSymbol, label, currency, snapshot);
            } catch (Exception ignored) {
                JSONObject quote = new JSONObject();
                quote.put("available", false);
                quote.put("symbol", yahooSymbol);
                quote.put("label", label);
                quote.put("currency", currency);
                quote.put("source", "Yahoo Finance unavailable");
                quote.put("timestamp", isoNow());
                quote.put("quote_time", "");
                quote.put("refresh_interval_seconds", MACRO_CACHE_MS / 1000L);
                return quote;
            }
        }

        private Analysis analyzeTicker(String yahooSymbol, String displaySymbol) throws Exception {
            return analyzeTicker(yahooSymbol, displaySymbol, false);
        }

        private Analysis analyzeTicker(String yahooSymbol, String displaySymbol, boolean preferFiveMinuteCandles) throws Exception {
            Series series = preferFiveMinuteCandles
                    ? fetchFiveMinuteAnalysisSeries(yahooSymbol)
                    : fetchAnalysisSeries(yahooSymbol);
            if (series.close.size() < 10) {
                return null;
            }

            int last = series.close.size() - 1;
            double ltp = series.latestPrice();
            double previous = series.previousSessionClose();
            if (previous <= 0.0) {
                previous = series.close.get(Math.max(0, last - 12));
            }
            double change = previous > 0 ? ltp - previous : 0.0;
            double changePercent = previous > 0 ? (change / previous) * 100.0 : 0.0;
            double velocity = calculateVelocity(series);
            double ac = calculateAcceleration(series);
            double rsi = calculateRsi(series, RSI_PERIOD);
            PsarResult psar = calculatePsar(series);
            String trend = psar.value < series.low.get(last) ? "BULL" : "BEAR";
            double score = scoreSignal(ltp, changePercent, velocity, ac, trend);
            String signal = signalName(score);
            String prediction = score > 0.10 ? "bullish" : (score < -0.10 ? "bearish" : "neutral");

            Analysis analysis = new Analysis();
            analysis.symbol = displaySymbol;
            analysis.ltp = ltp;
            analysis.change = change;
            analysis.changePercent = changePercent;
            analysis.velocity = velocity;
            analysis.ac = ac;
            analysis.rsi = rsi;
            analysis.rsiPriority = Double.isFinite(rsi) && rsi < 70.0;
            analysis.trend = trend;
            analysis.signal = signal;
            analysis.prediction = prediction;
            analysis.confluenceScore = score;
            analysis.psarAf = psar.af;
            analysis.psarValue = psar.value;
            analysis.high = series.maxHigh();
            analysis.quoteEpoch = series.latestEpochSeconds();
            analysis.quoteTime = analysis.quoteEpoch > 0L ? formatEpochTime(analysis.quoteEpoch) : "";
            analysis.quoteTimestamp = analysis.quoteEpoch > 0L ? formatEpochIso(analysis.quoteEpoch) : "";
            analysis.quoteSource = series.sourceLabel();
            return analysis;
        }

        private PsarResult calculatePsar(Series series) {
            int length = series.close.size();
            if (length == 0) {
                return new PsarResult(0.0, 0.02);
            }
            if (length == 1) {
                return new PsarResult(series.low.get(0), 0.02);
            }

            boolean bull = series.close.get(1) >= series.close.get(0);
            double af = 0.02;
            double ep = bull ? series.high.get(0) : series.low.get(0);
            double psar = bull ? series.low.get(0) : series.high.get(0);

            for (int i = 1; i < length; i += 1) {
                psar = psar + af * (ep - psar);

                if (bull) {
                    psar = Math.min(psar, series.low.get(i - 1));
                    if (i > 1) {
                        psar = Math.min(psar, series.low.get(i - 2));
                    }

                    if (series.low.get(i) < psar) {
                        bull = false;
                        psar = ep;
                        ep = series.low.get(i);
                        af = 0.02;
                    } else if (series.high.get(i) > ep) {
                        ep = series.high.get(i);
                        af = Math.min(0.20, af + 0.02);
                    }
                } else {
                    psar = Math.max(psar, series.high.get(i - 1));
                    if (i > 1) {
                        psar = Math.max(psar, series.high.get(i - 2));
                    }

                    if (series.high.get(i) > psar) {
                        bull = true;
                        psar = ep;
                        ep = series.high.get(i);
                        af = 0.02;
                    } else if (series.low.get(i) < ep) {
                        ep = series.low.get(i);
                        af = Math.min(0.20, af + 0.02);
                    }
                }
            }

            return new PsarResult(psar, af);
        }

        private double calculateVelocity(Series series) {
            int last = series.close.size() - 1;
            if (last < 5) {
                return 0.0;
            }
            return sma(series.close, last, 5) - sma(series.close, last - 1, 5);
        }

        private double calculateAcceleration(Series series) {
            List<Double> midpoint = new ArrayList<>();
            for (int i = 0; i < series.close.size(); i += 1) {
                midpoint.add((series.high.get(i) + series.low.get(i)) / 2.0);
            }

            List<Double> ao = new ArrayList<>();
            for (int i = 0; i < midpoint.size(); i += 1) {
                if (i < 33) {
                    ao.add(0.0);
                } else {
                    ao.add(sma(midpoint, i, 5) - sma(midpoint, i, 34));
                }
            }

            int last = ao.size() - 1;
            if (last < 5) {
                return 0.0;
            }
            return ao.get(last) - sma(ao, last, 5);
        }

        private double calculateRsi(Series series, int period) {
            int size = series.close.size();
            if (size <= period) {
                return Double.NaN;
            }

            double avgGain = 0.0;
            double avgLoss = 0.0;
            for (int i = 1; i <= period; i += 1) {
                double change = series.close.get(i) - series.close.get(i - 1);
                if (change >= 0.0) {
                    avgGain += change;
                } else {
                    avgLoss += -change;
                }
            }
            avgGain /= period;
            avgLoss /= period;

            for (int i = period + 1; i < size; i += 1) {
                double change = series.close.get(i) - series.close.get(i - 1);
                double gain = Math.max(0.0, change);
                double loss = Math.max(0.0, -change);
                avgGain = ((avgGain * (period - 1)) + gain) / period;
                avgLoss = ((avgLoss * (period - 1)) + loss) / period;
            }

            if (avgLoss == 0.0) {
                return avgGain == 0.0 ? 50.0 : 100.0;
            }
            double rs = avgGain / avgLoss;
            return 100.0 - (100.0 / (1.0 + rs));
        }

        private double scoreSignal(double ltp, double changePercent, double velocity, double ac, String trend) {
            double trendWeight = "BULL".equals(trend) ? 0.25 : -0.25;
            double momentum = Math.tanh(changePercent / 2.0) * 0.35;
            double velocityScore = Math.tanh((velocity / Math.max(1.0, ltp)) * 180.0) * 0.25;
            double acScore = Math.tanh((ac / Math.max(1.0, ltp)) * 60.0) * 0.15;
            return round(clamp(trendWeight + momentum + velocityScore + acScore, -0.95, 0.95), 2);
        }

        private String signalName(double score) {
            if (score >= 0.55) {
                return "STRONG_BUY";
            }
            if (score >= 0.15) {
                return "BUY";
            }
            if (score <= -0.55) {
                return "STRONG_SELL";
            }
            if (score <= -0.15) {
                return "SELL";
            }
            return "NEUTRAL";
        }

        private Series fetchAnalysisSeries(String symbol) throws Exception {
            Exception firstError = null;
            try {
                Series series = fetchSeries(symbol, "1d", "1m");
                if (series.close.size() >= 10) {
                    return series;
                }
            } catch (Exception e) {
                firstError = e;
            }

            try {
                return fetchSeries(symbol, "5d", "5m");
            } catch (Exception e) {
                if (firstError != null) {
                    throw firstError;
                }
                throw e;
            }
        }

        private Series fetchFiveMinuteAnalysisSeries(String symbol) throws Exception {
            Series series = fetchSeries(symbol, "5d", "5m");
            if (series.close.size() < 10) {
                throw new IllegalStateException("Insufficient five-minute candles for " + symbol);
            }
            return series;
        }

        private Series fetchQuoteSeries(String symbol) throws Exception {
            Exception firstError = null;
            try {
                return fetchSeries(symbol, "1d", "1m", true);
            } catch (Exception e) {
                firstError = e;
            }

            try {
                return fetchSeries(symbol, "2d", "5m", true);
            } catch (Exception e) {
                if (firstError != null) {
                    throw firstError;
                }
                throw e;
            }
        }

        private Series fetchSeries(String symbol, String range, String interval) throws Exception {
            return fetchSeries(symbol, range, interval, false);
        }

        private Series fetchSeries(String symbol, String range, String interval, boolean includePrePost) throws Exception {
            String encoded = URLEncoder.encode(symbol, StandardCharsets.UTF_8.name());
            String query = encoded
                    + "?range=" + range
                    + "&interval=" + interval
                    + "&includePrePost=" + includePrePost;
            String body;
            try {
                body = fetchUrl("https://query2.finance.yahoo.com/v8/finance/chart/" + query);
            } catch (Exception primaryError) {
                body = fetchUrl("https://query1.finance.yahoo.com/v8/finance/chart/" + query);
            }
            JSONObject chart = new JSONObject(body).getJSONObject("chart");
            JSONArray result = chart.optJSONArray("result");
            if (result == null || result.length() == 0 || result.isNull(0)) {
                throw new IllegalStateException("No Yahoo chart data for " + symbol);
            }

            JSONObject first = result.getJSONObject(0);
            JSONObject meta = first.optJSONObject("meta");
            JSONArray timestamps = first.optJSONArray("timestamp");
            JSONObject quote = first.getJSONObject("indicators").getJSONArray("quote").getJSONObject(0);
            JSONArray close = quote.optJSONArray("close");
            JSONArray adjustedClose = null;
            JSONObject indicators = first.optJSONObject("indicators");
            JSONArray adjustedSeries = indicators == null ? null : indicators.optJSONArray("adjclose");
            if (adjustedSeries != null && adjustedSeries.length() > 0 && !adjustedSeries.isNull(0)) {
                adjustedClose = adjustedSeries.optJSONObject(0).optJSONArray("adjclose");
            }
            JSONArray high = quote.optJSONArray("high");
            JSONArray low = quote.optJSONArray("low");
            JSONArray volume = quote.optJSONArray("volume");

            Series series = new Series();
            series.interval = interval;
            series.range = range;
            if (meta != null) {
                series.regularMarketPrice = optFinite(meta, "regularMarketPrice", Double.NaN);
                series.regularMarketPreviousClose = firstFinite(
                        optFinite(meta, "chartPreviousClose", Double.NaN),
                        optFinite(meta, "previousClose", Double.NaN),
                        optFinite(meta, "regularMarketPreviousClose", Double.NaN)
                );
                series.regularMarketChange = optFinite(meta, "regularMarketChange", Double.NaN);
                series.regularMarketChangePercent = optFinite(meta, "regularMarketChangePercent", Double.NaN);
                series.regularMarketTime = meta.optLong("regularMarketTime", 0L);
                series.exchangeName = meta.optString("exchangeName", "");
            }
            int length = close == null ? 0 : close.length();
            for (int i = 0; i < length; i += 1) {
                double closeValue = optDouble(close, i, Double.NaN);
                if (Double.isNaN(closeValue)) {
                    continue;
                }
                double highValue = optDouble(high, i, closeValue);
                double lowValue = optDouble(low, i, closeValue);
                series.close.add(closeValue);
                double adjustedValue = optDouble(adjustedClose, i, closeValue);
                series.adjustedClose.add(Double.isNaN(adjustedValue) ? closeValue : adjustedValue);
                series.high.add(Double.isNaN(highValue) ? closeValue : highValue);
                series.low.add(Double.isNaN(lowValue) ? closeValue : lowValue);
                series.volume.add(optLong(volume, i, 0L));
                series.timestamps.add(optLong(timestamps, i, 0L));
            }

            if (series.close.isEmpty()) {
                throw new IllegalStateException("Empty Yahoo chart close values for " + symbol);
            }
            return series;
        }

        private String fetchUrl(String value) throws Exception {
            return fetchUrl(value, 12_000);
        }

        private String fetchUrl(String value, int timeoutMs) throws Exception {
            HttpURLConnection connection = null;
            try {
                connection = (HttpURLConnection) new URL(value).openConnection();
                connection.setConnectTimeout(timeoutMs);
                connection.setReadTimeout(timeoutMs);
                connection.setRequestMethod("GET");
                connection.setUseCaches(false);
                connection.setRequestProperty("Accept", "application/json, application/rss+xml, text/xml, */*");
                connection.setRequestProperty("Cache-Control", "no-cache");
                connection.setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/124 Mobile Safari/537.36 StockUnified/0.3");

                int code = connection.getResponseCode();
                InputStream stream = code >= 200 && code < 300
                        ? connection.getInputStream()
                        : connection.getErrorStream();
                String response = readAll(stream);
                if (code < 200 || code >= 300) {
                    throw new IllegalStateException("Yahoo HTTP " + code);
                }
                return response;
            } finally {
                if (connection != null) {
                    connection.disconnect();
                }
            }
        }

        private String readAll(InputStream stream) throws Exception {
            if (stream == null) {
                return "";
            }
            BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8));
            StringBuilder builder = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                builder.append(line);
            }
            reader.close();
            return builder.toString();
        }

        private double sma(List<Double> values, int end, int window) {
            if (values.isEmpty()) {
                return 0.0;
            }
            int start = Math.max(0, end - window + 1);
            double total = 0.0;
            int count = 0;
            for (int i = start; i <= end && i < values.size(); i += 1) {
                total += values.get(i);
                count += 1;
            }
            return count == 0 ? 0.0 : total / count;
        }

        private double optDouble(JSONArray values, int index, double fallback) {
            if (values == null || index >= values.length() || values.isNull(index)) {
                return fallback;
            }
            return values.optDouble(index, fallback);
        }

        private long optLong(JSONArray values, int index, long fallback) {
            if (values == null || index >= values.length() || values.isNull(index)) {
                return fallback;
            }
            return values.optLong(index, fallback);
        }

        private double optFinite(JSONObject values, String key, double fallback) {
            if (values == null || !values.has(key) || values.isNull(key)) {
                return fallback;
            }
            double value = values.optDouble(key, fallback);
            return Double.isFinite(value) ? value : fallback;
        }

        private double firstFinite(double... values) {
            for (double value : values) {
                if (Double.isFinite(value)) {
                    return value;
                }
            }
            return Double.NaN;
        }

        private List<List<String>> chunkStrings(List<String> items, int size) {
            List<List<String>> chunks = new ArrayList<>();
            for (int i = 0; i < items.size(); i += size) {
                chunks.add(items.subList(i, Math.min(items.size(), i + size)));
            }
            return chunks;
        }

        private double round(double value, int places) {
            double scale = Math.pow(10.0, places);
            return Math.round(value * scale) / scale;
        }

        private double clamp(double value, double min, double max) {
            return Math.max(min, Math.min(max, value));
        }

        private String isoNow() {
            return formatIsoDate(new Date());
        }

        private String formatEpochIso(long epochSeconds) {
            if (epochSeconds <= 0L) {
                return "";
            }
            return formatIsoDate(new Date(epochSeconds * 1000L));
        }

        private String formatIsoDate(Date date) {
            SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssZ", Locale.US);
            format.setTimeZone(TimeZone.getTimeZone("Asia/Kolkata"));
            String raw = format.format(date);
            if (raw.length() < 5) {
                return raw;
            }
            return raw.substring(0, raw.length() - 2) + ":" + raw.substring(raw.length() - 2);
        }

        private String formatEpochTime(long epochSeconds) {
            if (epochSeconds <= 0L) {
                return "";
            }
            SimpleDateFormat format = new SimpleDateFormat("HH:mm:ss", Locale.US);
            format.setTimeZone(TimeZone.getTimeZone("Asia/Kolkata"));
            return format.format(new Date(epochSeconds * 1000L));
        }

        private String formatEpochDate(long epochSeconds) {
            if (epochSeconds <= 0) {
                return "";
            }
            SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd", Locale.US);
            format.setTimeZone(TimeZone.getTimeZone("Asia/Kolkata"));
            return format.format(new Date(epochSeconds * 1000L));
        }

        private Calendar istToday() {
            Calendar calendar = Calendar.getInstance(TimeZone.getTimeZone("Asia/Kolkata"));
            calendar.set(Calendar.HOUR_OF_DAY, 0);
            calendar.set(Calendar.MINUTE, 0);
            calendar.set(Calendar.SECOND, 0);
            calendar.set(Calendar.MILLISECOND, 0);
            return calendar;
        }

        private Calendar parseMarketEventDate(String value) throws Exception {
            SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd", Locale.US);
            format.setTimeZone(TimeZone.getTimeZone("Asia/Kolkata"));
            Date parsed = format.parse(value);
            Calendar calendar = Calendar.getInstance(TimeZone.getTimeZone("Asia/Kolkata"));
            calendar.setTime(parsed == null ? new Date() : parsed);
            calendar.set(Calendar.HOUR_OF_DAY, 0);
            calendar.set(Calendar.MINUTE, 0);
            calendar.set(Calendar.SECOND, 0);
            calendar.set(Calendar.MILLISECOND, 0);
            return calendar;
        }

        private Calendar addDays(Calendar date, int amount) {
            Calendar copy = (Calendar) date.clone();
            copy.add(Calendar.DAY_OF_MONTH, amount);
            return copy;
        }

        private String formatMarketEventDate(Calendar date) {
            SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd", Locale.US);
            format.setTimeZone(TimeZone.getTimeZone("Asia/Kolkata"));
            return format.format(date.getTime());
        }

        private int daysBetween(Calendar start, Calendar end) {
            long millis = end.getTimeInMillis() - start.getTimeInMillis();
            return (int) (millis / TimeUnit.DAYS.toMillis(1));
        }

        private String compactMoney(double value) {
            double abs = Math.abs(value);
            if (abs >= 1_000_000_000_000.0) {
                return String.format(Locale.US, "%.2fT", value / 1_000_000_000_000.0);
            }
            if (abs >= 1_000_000_000.0) {
                return String.format(Locale.US, "%.2fB", value / 1_000_000_000.0);
            }
            if (abs >= 1_000_000.0) {
                return String.format(Locale.US, "%.2fM", value / 1_000_000.0);
            }
            return String.format(Locale.US, "%.0f", value);
        }

        private String buildErrorDashboard(String message) {
            try {
                JSONObject root = new JSONObject();
                root.put("error", message == null
                        ? "Live market data is unavailable. Check the network connection."
                        : "Live market data is unavailable: " + message);
                root.put("nifty", JSONObject.NULL);
                root.put("top_predictions", new JSONArray());
                root.put("market_summary", new JSONObject()
                        .put("total_stocks", 0)
                        .put("bullish", 0)
                        .put("bearish", 0)
                        .put("neutral", 0)
                        .put("avg_ac", 0));
                root.put("latest_news", new JSONArray());
                root.put("sector_analysis", new JSONArray());
                root.put("upcoming_events", buildUpcomingEvents());
                root.put("alerts", new JSONArray().put(new JSONObject()
                        .put("severity", "medium")
                        .put("title", "Yahoo data unavailable")
                        .put("message", message == null ? "Check network connection." : message)
                        .put("timestamp", isoNow())));
                root.put("technical_updated", new SimpleDateFormat("HH:mm:ss", Locale.US).format(new Date()));
                root.put("data_source", "Yahoo Finance on-device");
                return root.toString();
            } catch (Exception ignored) {
                return "{\"error\":\"Live market data is unavailable\"}";
            }
        }

        private String errorJson(String message) {
            try {
                return new JSONObject().put("error", message).toString();
            } catch (Exception ignored) {
                return "{\"error\":\"Unavailable\"}";
            }
        }
    }

    private static final class Series {
        final List<Double> close = new ArrayList<>();
        final List<Double> adjustedClose = new ArrayList<>();
        final List<Double> high = new ArrayList<>();
        final List<Double> low = new ArrayList<>();
        final List<Long> volume = new ArrayList<>();
        final List<Long> timestamps = new ArrayList<>();
        double regularMarketPrice = Double.NaN;
        double regularMarketPreviousClose = Double.NaN;
        double regularMarketChange = Double.NaN;
        double regularMarketChangePercent = Double.NaN;
        long regularMarketTime = 0L;
        String exchangeName = "";
        String range = "";
        String interval = "";

        double lastClose() {
            return close.get(close.size() - 1);
        }

        double previousClose() {
            return close.size() > 1 ? close.get(close.size() - 2) : lastClose();
        }

        double latestPrice() {
            return Double.isFinite(regularMarketPrice) ? regularMarketPrice : lastClose();
        }

        double previousSessionClose() {
            return Double.isFinite(regularMarketPreviousClose) ? regularMarketPreviousClose : previousClose();
        }

        long latestEpochSeconds() {
            if (regularMarketTime > 0L) {
                return regularMarketTime;
            }
            return latestCandleEpochSeconds();
        }

        long latestCandleEpochSeconds() {
            for (int i = timestamps.size() - 1; i >= 0; i -= 1) {
                long value = timestamps.get(i);
                if (value > 0L) {
                    return value;
                }
            }
            return 0L;
        }

        String sourceLabel() {
            if (interval == null || interval.isEmpty()) {
                return "Yahoo Finance";
            }
            return "Yahoo Finance " + interval;
        }

        double maxHigh() {
            double value = 0.0;
            for (double item : high) {
                value = Math.max(value, item);
            }
            return value;
        }
    }

    private static final class QuoteSnapshot {
        String symbol = "";
        double price = Double.NaN;
        double change = Double.NaN;
        double changePercent = Double.NaN;
        long volume = 0L;
        long marketTime = 0L;
        String source = "Yahoo Finance quote";

        boolean hasPrice() {
            return Double.isFinite(price);
        }
    }

    private static final class PsarResult {
        final double value;
        final double af;

        PsarResult(double value, double af) {
            this.value = value;
            this.af = af;
        }
    }

    private final class Analysis {
        String symbol;
        double ltp;
        double change;
        double changePercent;
        double velocity;
        double ac;
        double rsi = Double.NaN;
        boolean rsiPriority;
        double psarAf;
        double psarValue;
        String trend;
        String signal;
        String prediction;
        double confluenceScore;
        double high;
        long quoteEpoch;
        String quoteTime = "";
        String quoteTimestamp = "";
        String quoteSource = "Yahoo Finance";

        JSONObject toPredictionJson() throws Exception {
            JSONObject row = new JSONObject();
            row.put("symbol", symbol);
            row.put("ltp", roundForJson(ltp, 2));
            row.put("change", roundForJson(change, 2));
            row.put("change_percent", roundForJson(changePercent, 2));
            row.put("velocity", roundForJson(velocity, 4));
            row.put("ac", roundForJson(ac, 4));
            if (Double.isFinite(rsi)) {
                row.put("rsi", roundForJson(rsi, 2));
            } else {
                row.put("rsi", JSONObject.NULL);
            }
            row.put("rsi_priority", rsiPriority);
            row.put("psar_af", roundForJson(psarAf, 2));
            row.put("psar_value", roundForJson(psarValue, 2));
            row.put("psar_trend", trend.toLowerCase(Locale.US));
            row.put("signal_strength", signal);
            row.put("prediction", prediction);
            row.put("confluence_score", confluenceScore);
            row.put("high_52w", roundForJson(high, 2));
            if (quoteEpoch > 0L) {
                row.put("quote_epoch", quoteEpoch);
                row.put("quote_time", quoteTime);
                row.put("quote_timestamp", quoteTimestamp);
            }
            row.put("quote_source", quoteSource);
            return row;
        }

        JSONObject toNiftyJson() throws Exception {
            JSONObject row = new JSONObject();
            row.put("ltp", roundForJson(ltp, 2));
            row.put("change", roundForJson(change, 2));
            row.put("change_percent", roundForJson(changePercent, 2));
            row.put("velocity", roundForJson(velocity, 4));
            row.put("ac", roundForJson(ac, 4));
            if (Double.isFinite(rsi)) {
                row.put("rsi", roundForJson(rsi, 2));
            } else {
                row.put("rsi", JSONObject.NULL);
            }
            row.put("psar_af", roundForJson(psarAf, 2));
            row.put("psar_value", roundForJson(psarValue, 2));
            row.put("trend", trend);
            row.put("reversal_count", 0);
            if (quoteEpoch > 0L) {
                row.put("quote_epoch", quoteEpoch);
                row.put("quote_time", quoteTime);
                row.put("quote_timestamp", quoteTimestamp);
            }
            row.put("quote_source", quoteSource);
            return row;
        }

        private double roundForJson(double value, int places) {
            double scale = Math.pow(10.0, places);
            return Math.round(value * scale) / scale;
        }
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private void registerPredictiveBack() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            backInvokedCallback = Api33Back.register(this, this::handleBackNavigation);
        }
    }

    private void handleBackNavigation() {
        if (webView == null) {
            finishAfterTransition();
            return;
        }
        webView.evaluateJavascript(
                "window.handleNativeBack ? window.handleNativeBack() : false",
                handled -> {
                    if ("true".equalsIgnoreCase(handled)) {
                        return;
                    }
                    if (webView != null && webView.canGoBack()) {
                        webView.goBack();
                    } else {
                        finishAfterTransition();
                    }
                }
        );
    }

    @SuppressLint("GestureBackNavigation")
    @Override
    public void onBackPressed() {
        handleBackNavigation();
    }

    @Override
    protected void onDestroy() {
        bridgeExecutor.shutdownNow();
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU && backInvokedCallback != null) {
            Api33Back.unregister(this, backInvokedCallback);
            backInvokedCallback = null;
        }
        if (webView != null) {
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }

    @SuppressLint("NewApi")
    private static final class Api30Insets {
        private Api30Insets() {
        }

        static int statusBarTop(WindowInsets insets) {
            return insets.getInsets(WindowInsets.Type.statusBars()).top;
        }
    }

    @SuppressLint("NewApi")
    private static final class Api33Back {
        private Api33Back() {
        }

        static Object register(Activity activity, Runnable action) {
            android.window.OnBackInvokedCallback callback = action::run;
            activity.getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                    android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT,
                    callback
            );
            return callback;
        }

        static void unregister(Activity activity, Object value) {
            activity.getOnBackInvokedDispatcher().unregisterOnBackInvokedCallback(
                    (android.window.OnBackInvokedCallback) value
            );
        }
    }
}
