import re

with open('src/api/main.py', 'r') as f:
    content = f.read()

new_html_func = """def get_dashboard_html() -> str:
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GeoPolitical Stock Monitor - Pro Terminal</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <style>
        :root {
            --bg-base: #020617;
            --bg-glass: rgba(15, 23, 42, 0.65);
            --bg-card: rgba(30, 41, 59, 0.5);
            --border-light: rgba(255, 255, 255, 0.08);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-primary: #3b82f6;
            --accent-glow: rgba(59, 130, 246, 0.5);
            --positive: #10b981;
            --positive-bg: rgba(16, 185, 129, 0.15);
            --negative: #ef4444;
            --negative-bg: rgba(239, 68, 68, 0.15);
            --warning: #f59e0b;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Inter', sans-serif; 
            background: radial-gradient(circle at top right, #0f172a, #020617 60%);
            background-attachment: fixed;
            min-height: 100vh; 
            color: var(--text-main); 
            -webkit-font-smoothing: antialiased;
        }
        
        /* Layout Grid */
        .container { max-width: 1920px; margin: 0 auto; padding: 1.5rem; display: flex; flex-direction: column; gap: 1.5rem; }
        .main-grid { display: grid; grid-template-columns: 280px 1fr 320px; gap: 1.5rem; height: calc(100vh - 180px); }
        
        /* Header / Navbar */
        .header { 
            background: var(--bg-glass); 
            backdrop-filter: blur(16px); 
            -webkit-backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--border-light); 
            position: sticky; top: 0; z-index: 100; 
            padding: 1rem 1.5rem;
            display: flex; flex-direction: column; gap: 1rem;
        }
        .header-top { display: flex; justify-content: space-between; align-items: center; }
        
        .logo { display: flex; align-items: center; gap: 0.8rem; font-size: 1.25rem; font-weight: 700; letter-spacing: -0.02em; }
        .logo-icon { 
            width: 32px; height: 32px; 
            background: linear-gradient(135deg, #3b82f6, #8b5cf6); 
            border-radius: 8px; 
            display: flex; align-items: center; justify-content: center; 
            font-size: 1rem;
            box-shadow: 0 0 15px var(--accent-glow);
        }
        
        .status-badge { display: flex; align-items: center; gap: 0.5rem; padding: 0.35rem 0.8rem; border-radius: 99px; font-size: 0.75rem; font-weight: 600; font-family: 'JetBrains Mono', monospace; text-transform: uppercase;}
        .market-open { background: var(--positive-bg); color: var(--positive); border: 1px solid rgba(16, 185, 129, 0.3); }
        .market-closed { background: var(--negative-bg); color: var(--negative); border: 1px solid rgba(239, 68, 68, 0.3); }
        .status-dot { width: 6px; height: 6px; border-radius: 50%; animation: pulse 2s infinite; }
        .market-open .status-dot { background: var(--positive); box-shadow: 0 0 8px var(--positive); }
        .market-closed .status-dot { background: var(--negative); }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; transform: scale(0.8); } }

        /* Nifty Banner */
        .nifty-banner { 
            background: linear-gradient(90deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.2)); 
            border: 1px solid var(--border-light); 
            border-radius: 10px; padding: 0.75rem 1.5rem; 
            display: flex; justify-content: space-between; align-items: center; 
        }
        .nifty-left { display: flex; gap: 1.25rem; align-items: center; }
        .nifty-label { color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; font-size: 0.8rem;}
        .nifty-ltp { font-size: 1.25rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
        .nifty-signal { padding: 0.25rem 0.6rem; border-radius: 6px; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;}
        .signal-bullish { background: var(--positive-bg); color: var(--positive); box-shadow: 0 0 10px rgba(16, 185, 129, 0.2); }
        .signal-bearish { background: var(--negative-bg); color: var(--negative); box-shadow: 0 0 10px rgba(239, 68, 68, 0.2); }
        .nifty-right { display: flex; gap: 2rem; }
        .nifty-metric { display: flex; flex-direction: column; align-items: flex-end; }
        .nifty-metric-label { font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.2rem;}
        .nifty-metric-val { font-weight: 600; font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; }
        
        /* KPI Grid */
        .stats-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 1rem; }
        .stat-card { 
            background: var(--bg-card); 
            border: 1px solid var(--border-light); 
            border-radius: 12px; padding: 1.25rem; 
            backdrop-filter: blur(8px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        .stat-card::before {
            content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
            transform: translateX(-100%); transition: transform 0.5s ease;
        }
        .stat-card:hover { transform: translateY(-4px); border-color: rgba(255,255,255,0.2); box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        .stat-card:hover::before { transform: translateX(100%); }
        .stat-label { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.75rem; font-weight: 600;}
        .stat-value { font-size: 1.75rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;}
        
        /* Cards */
        .card { 
            background: var(--bg-card); 
            border: 1px solid var(--border-light); 
            border-radius: 16px; 
            overflow: hidden; display: flex; flex-direction: column;
            backdrop-filter: blur(12px);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        .card-header { 
            padding: 1.25rem 1.5rem; 
            border-bottom: 1px solid var(--border-light); 
            background: rgba(15, 23, 42, 0.4);
            display: flex; justify-content: space-between; align-items: center;
        }
        .card-title { font-weight: 600; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; display: flex; align-items: center; gap: 0.75rem; color: #fff;}
        .card-body { padding: 1rem; overflow-y: auto; flex: 1; position: relative;}
        
        /* News Sidebar */
        .news-list { display: flex; flex-direction: column; gap: 0.75rem; }
        .news-item { 
            padding: 1rem; border-radius: 10px; 
            background: rgba(15, 23, 42, 0.4); 
            border: 1px solid rgba(255,255,255,0.03); 
            transition: all 0.2s; 
            cursor: pointer;
            animation: fadeIn 0.5s ease-out;
        }
        .news-item:hover { background: rgba(30, 41, 59, 0.8); border-color: rgba(255,255,255,0.1); transform: translateX(2px); }
        .news-source { font-size: 0.7rem; color: var(--text-muted); margin-bottom: 0.5rem; display: flex; justify-content: space-between; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;}
        .news-title { font-size: 0.9rem; font-weight: 500; line-height: 1.5; margin-bottom: 0.75rem; color: #fff; }
        .news-link { color: inherit; text-decoration: none; display: block; }
        .news-meta { display: flex; gap: 0.5rem; flex-wrap: wrap; }
        
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        /* Badges */
        .badge { font-size: 0.65rem; padding: 0.25rem 0.6rem; border-radius: 6px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; font-family: 'JetBrains Mono', monospace;}
        .badge-sentiment-strong_bullish { background: var(--positive-bg); color: var(--positive); border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge-sentiment-bullish { background: rgba(52, 211, 153, 0.1); color: #34d399; }
        .badge-sentiment-neutral { background: rgba(148, 163, 184, 0.1); color: var(--text-muted); }
        .badge-sentiment-bearish { background: rgba(248, 113, 113, 0.1); color: #f87171; }
        .badge-sentiment-strong_bearish { background: var(--negative-bg); color: var(--negative); border: 1px solid rgba(239, 68, 68, 0.3); }
        
        /* Confluence Table */
        .table-container { width: 100%; height: 100%; overflow-y: auto; overflow-x: hidden; padding-right: 0.5rem;}
        .confluence-table { width: 100%; border-collapse: separate; border-spacing: 0 4px; font-size: 0.85rem; }
        .confluence-table th { 
            position: sticky; top: 0; 
            background: rgba(2, 6, 23, 0.95); backdrop-filter: blur(12px); 
            padding: 1rem 0.75rem; text-align: left; 
            color: var(--text-muted); font-weight: 600; font-size: 0.75rem; 
            text-transform: uppercase; letter-spacing: 0.05em;
            z-index: 10; cursor: pointer; user-select: none; transition: color 0.2s;
            border-bottom: 1px solid var(--border-light);
        }
        .confluence-table th:hover { color: #fff; }
        .confluence-table tbody tr { 
            transition: all 0.2s; 
            background: rgba(15, 23, 42, 0.3);
        }
        .confluence-table td { 
            padding: 0.8rem 0.75rem; 
            border-top: 1px solid transparent; border-bottom: 1px solid transparent; 
            font-family: 'JetBrains Mono', monospace; 
            vertical-align: middle;
        }
        .confluence-table tbody tr:hover { 
            background: rgba(30, 41, 59, 0.6)!important; 
            transform: scale(1.01);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            position: relative; z-index: 5;
            border-radius: 8px;
        }
        .confluence-table tbody tr:hover td:first-child { border-top-left-radius: 8px; border-bottom-left-radius: 8px; }
        .confluence-table tbody tr:hover td:last-child { border-top-right-radius: 8px; border-bottom-right-radius: 8px; }
        
        .col-script { font-family: 'Inter', sans-serif !important; font-weight: 700; color: #fff; font-size: 0.95rem; display: flex; align-items: center; gap: 0.5rem;}
        
        /* Confluence Bar */
        .conf-cell { display: flex; align-items: center; gap: 0.75rem; justify-content: flex-end;}
        .conf-score { width: 45px; text-align: right; font-weight: 600; }
        .conf-bar-wrapper { 
            width: 70px; height: 6px; 
            background: rgba(0,0,0,0.5); 
            border-radius: 3px; overflow: hidden; position: relative;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.3);
        }
        .conf-bar-fill { position: absolute; top: 0; bottom: 0; border-radius: 3px; transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
        .conf-pos { background: linear-gradient(90deg, #10b981, #34d399); left: 50%; box-shadow: 0 0 8px rgba(16,185,129,0.5); }
        .conf-neg { background: linear-gradient(270deg, #ef4444, #f87171); right: 50%; box-shadow: 0 0 8px rgba(239,68,68,0.5); }
        
        /* Alerts */
        .alert-item { 
            padding: 1rem; border-radius: 10px; margin-bottom: 0.75rem; 
            font-size: 0.85rem; position: relative; overflow: hidden;
            animation: fadeIn 0.5s ease-out;
        }
        .alert-high { background: linear-gradient(90deg, rgba(239, 68, 68, 0.15), rgba(239,68,68,0.05)); border-left: 4px solid var(--negative); }
        .alert-medium { background: linear-gradient(90deg, rgba(245, 158, 11, 0.15), rgba(245,158,11,0.05)); border-left: 4px solid var(--warning); }
        .alert-title { font-weight: 600; color: #fff; margin-bottom: 0.4rem; font-family: 'Inter', sans-serif; display: flex; align-items: center; gap: 0.5rem;}
        .alert-time { font-size: 0.7rem; color: var(--text-muted); margin-top: 0.6rem; font-family: 'JetBrains Mono', monospace;}

        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: rgba(0,0,0,0.2); border-radius: 4px;}
        ::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.3); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(148, 163, 184, 0.5); }
        
        /* Utility */
        .val-pos { color: var(--positive); }
        .val-neg { color: var(--negative); }
        .text-glow-pos { text-shadow: 0 0 10px rgba(16,185,129,0.4); }
        .text-glow-neg { text-shadow: 0 0 10px rgba(239,68,68,0.4); }
        
        .skeleton { background: linear-gradient(90deg, #1e293b 25%, #334155 50%, #1e293b 75%); background-size: 400% 100%; animation: skeletonLoading 1.5s infinite; border-radius: 4px;}
        @keyframes skeletonLoading { 0% { background-position: 100% 50%; } 100% { background-position: 0 50%; } }
    </style>
</head>
<body>
    <header class="header">
        <div class="header-top">
            <div class="logo">
                <div class="logo-icon">⚡</div>
                <span style="background: linear-gradient(to right, #fff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Confluence Terminal</span>
            </div>
            <div style="display: flex; align-items: center; gap: 1.5rem;">
                <div style="display: flex; flex-direction: column; align-items: flex-end;">
                    <span style="font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Last Sync</span>
                    <span style="font-size: 0.85rem; font-family: 'JetBrains Mono', monospace; font-weight: 500;" id="lastUpdated">--:--:--</span>
                </div>
                <div class="status-badge market-closed" id="marketStatus">
                    <span class="status-dot"></span>
                    <span id="marketText">Checking...</span>
                </div>
            </div>
        </div>
        <!-- Nifty Banner -->
        <div class="nifty-banner" id="niftyBanner">
            <div class="nifty-left">
                <span class="nifty-label">NIFTY 50 Core Indicator</span>
                <span class="nifty-ltp" id="niftyLtp">--</span>
                <span class="nifty-signal" id="niftySignal">--</span>
            </div>
            <div class="nifty-right">
                <div class="nifty-metric">
                    <span class="nifty-metric-label">Momentum Velocity</span>
                    <span class="nifty-metric-val" id="niftyVel">--</span>
                </div>
                <div class="nifty-metric">
                    <span class="nifty-metric-label">Awesome Osc (AC)</span>
                    <span class="nifty-metric-val" id="niftyAc">--</span>
                </div>
                <div class="nifty-metric">
                    <span class="nifty-metric-label">Parabolic SAR AF</span>
                    <span class="nifty-metric-val" id="niftyAf" style="color: #60a5fa;">--</span>
                </div>
            </div>
        </div>
    </header>
    
    <div class="container">
        <!-- KPIs -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Articles Analyzed</div>
                <div class="stat-value" id="kpiNews">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Active Alpha Alerts</div>
                <div class="stat-value" style="color: var(--warning); text-shadow: 0 0 15px rgba(245,158,11,0.3);" id="kpiAlerts">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Bullish PSAR Breadth</div>
                <div class="stat-value val-pos text-glow-pos" id="kpiBullish">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Bearish PSAR Breadth</div>
                <div class="stat-value val-neg text-glow-neg" id="kpiBearish">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Global Avg AC</div>
                <div class="stat-value" id="kpiAf" style="color: #60a5fa;">0.00</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(139,92,246,0.1)); border-color: rgba(59,130,246,0.3);">
                <div class="stat-label" style="color: #93c5fd;">Engine Status</div>
                <div class="stat-value" style="color: #60a5fa; font-size: 1.4rem; display: flex; align-items:center; gap: 0.5rem;">
                    <span style="display:inline-block; width:10px; height:10px; background:#60a5fa; border-radius:50%; box-shadow: 0 0 10px #60a5fa; animation: pulse 2s infinite;"></span>
                    ONLINE
                </div>
            </div>
        </div>
        
        <div class="main-grid">
            <!-- Left: GeoPolitical News Stream -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">
                        <span style="font-size: 1.2rem;">📡</span>
                        Live Intelligence
                    </div>
                </div>
                <div class="card-body news-list" id="newsContainer">
                    <div style="text-align:center; padding: 2rem; color: var(--text-muted);">Syncing feeds...</div>
                </div>
            </div>
            
            <!-- Center: Confluence Screener -->
            <div class="card">
                <div class="card-header" style="background: linear-gradient(90deg, rgba(15,23,42,0.8), rgba(30,41,59,0.8));">
                    <div class="card-title">
                        <span style="font-size: 1.2rem;">🎯</span>
                        Algorithm Confluence Matrix
                    </div>
                </div>
                <div class="card-body" style="padding: 0;">
                    <div class="table-container">
                        <table class="confluence-table" id="confluenceTable">
                            <thead>
                                <tr>
                                    <th data-sort="symbol">Ticker</th>
                                    <th data-sort="ltp">Price (₹)</th>
                                    <th data-sort="ac">AC Osc</th>
                                    <th data-sort="velocity">Velocity</th>
                                    <th data-sort="psar_af">pSAR AF</th>
                                    <th data-sort="signal_strength">Tech Signal</th>
                                    <th data-sort="prediction">AI Sentiment</th>
                                    <th style="text-align:right;" data-sort="confluence_score">Confluence Score</th>
                                </tr>
                            </thead>
                            <tbody id="screenerBody">
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <!-- Right: Alerts & Sector Analysis -->
            <div style="display: flex; flex-direction: column; gap: 1.5rem; height: 100%;">
                <!-- Alerts -->
                <div class="card" style="flex: 1.2;">
                    <div class="card-header">
                        <div class="card-title">
                            <span style="font-size: 1.2rem;">🚨</span>
                            Actionable Alerts
                        </div>
                    </div>
                    <div class="card-body" id="alertsContainer">
                        <div style="text-align:center; padding: 2rem; color: var(--text-muted);">Awaiting signals...</div>
                    </div>
                </div>
                
                <!-- Macro Sentiment Chart -->
                <div class="card" style="flex: 1;">
                    <div class="card-header">
                        <div class="card-title">
                            <span style="font-size: 1.2rem;">🌐</span>
                            Macro Sentiment
                        </div>
                    </div>
                    <div class="card-body" style="display: flex; justify-content: center; align-items: center; padding: 0.5rem;" id="sentimentChart">
                        <!-- Plotly chart container -->
                        <div class="skeleton" style="width: 200px; height: 200px; border-radius: 50%;"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Global State
        let currentData = null;
        let sortCol = 'confluence_score';
        let sortDesc = true;
        let chartInitialized = false;

        // formatters
        const fmtNum = (n, d=2) => (n !== null && n !== undefined) ? Number(n).toFixed(d) : '--';
        const colorClass = (n) => n > 0 ? 'val-pos' : (n < 0 ? 'val-neg' : '');

        function updateDashboard() {
            fetch('/api/dashboard')
                .then(r => r.json())
                .then(data => {
                    currentData = data;
                    renderNifty(data.nifty);
                    renderKPIs(data);
                    renderNews(data.latest_news);
                    renderScreener(data.top_predictions);
                    renderAlerts(data.alerts);
                    renderChart(data);
                    
                    document.getElementById('lastUpdated').textContent = data.technical_updated || new Date().toLocaleTimeString();
                })
                .catch(err => console.error('Dashboard fetch error:', err));
                
            fetch('/api/market-status')
                .then(r => r.json())
                .then(data => {
                    const badge = document.getElementById('marketStatus');
                    const text = document.getElementById('marketText');
                    if (data.is_open) {
                        badge.className = 'status-badge market-open';
                        text.textContent = 'Market Open';
                    } else {
                        badge.className = 'status-badge market-closed';
                        text.textContent = `Market Closed`;
                    }
                });
        }

        function renderNifty(nifty) {
            if(!nifty) return;
            document.getElementById('niftyLtp').textContent = `₹${fmtNum(nifty.ltp)}`;
            
            const sigEl = document.getElementById('niftySignal');
            sigEl.textContent = nifty.trend;
            sigEl.className = `nifty-signal signal-${nifty.trend.toLowerCase()}`;
            
            const velEl = document.getElementById('niftyVel');
            velEl.textContent = (nifty.velocity >= 0 ? '+' : '') + fmtNum(nifty.velocity, 4);
            velEl.className = `nifty-metric-val ${colorClass(nifty.velocity)}`;
            
            const acEl = document.getElementById('niftyAc');
            acEl.textContent = (nifty.ac >= 0 ? '+' : '') + fmtNum(nifty.ac, 4);
            acEl.className = `nifty-metric-val ${colorClass(nifty.ac)}`;
            
            document.getElementById('niftyAf').textContent = fmtNum(nifty.psar_af);
        }

        function renderKPIs(data) {
            document.getElementById('kpiNews').textContent = data.latest_news?.length || 0;
            document.getElementById('kpiAlerts').textContent = data.alerts?.length || 0;
            if(data.market_summary) {
                document.getElementById('kpiBullish').textContent = data.market_summary.bullish || 0;
                document.getElementById('kpiBearish').textContent = data.market_summary.bearish || 0;
                document.getElementById('kpiAf').textContent = fmtNum(data.market_summary.avg_ac, 4);
            }
        }

        function renderNews(news) {
            const c = document.getElementById('newsContainer');
            if(!news || !news.length) { c.innerHTML = '<div style="padding:2rem; text-align:center; color:var(--text-muted);">No news events detected.</div>'; return; }
            
            const newHtml = news.map(n => `
                <div class="news-item">
                    <div class="news-source">
                        <span>${n.source}</span>
                        <span style="font-family:'JetBrains Mono', monospace;">${new Date(n.published_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                    </div>
                    <div class="news-title">
                        <a href="${n.url}" target="_blank" class="news-link">${n.title}</a>
                    </div>
                    <div class="news-meta">
                        <span class="badge badge-sentiment-${n.sentiment_label}">${n.sentiment_label.replace('strong_', 'Strong ')}</span>
                        ${n.affected_sectors[0] ? `<span class="badge" style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: var(--text-muted);">${n.affected_sectors[0]}</span>` : ''}
                        ${n.is_breaking ? `<span class="badge" style="background: var(--negative-bg); color: var(--negative); border: 1px solid rgba(239,68,68,0.3); box-shadow: 0 0 10px rgba(239,68,68,0.2);">BREAKING</span>` : ''}
                    </div>
                </div>
            `).join('');

            // Only update if changed to prevent animation flicker
            if(c.innerHTML !== newHtml) {
                c.innerHTML = newHtml;
            }
        }

        function renderScreener(preds) {
            const tbody = document.getElementById('screenerBody');
            if(!preds || !preds.length) { tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 2rem; color:var(--text-muted);">Fetching analysis data...</td></tr>'; return; }
            
            // Sort
            const sorted = [...preds].sort((a,b) => {
                let valA = a[sortCol];
                let valB = b[sortCol];
                
                if(sortCol === 'prediction') { valA = a.prediction; valB = b.prediction; }
                
                if(valA === null || valA === undefined) return 1;
                if(valB === null || valB === undefined) return -1;
                
                if(typeof valA === 'string') return sortDesc ? valB.localeCompare(valA) : valA.localeCompare(valB);
                return sortDesc ? valB - valA : valA - valB;
            });
            
            const sigEmoji = { 'STRONG_BUY': '🔥', 'BUY': '✨', 'NEUTRAL': '➖', 'SELL': '⚠️', 'STRONG_SELL': '⛔' };

            const newHtml = sorted.map((p, idx) => {
                const ac = p.ac || 0;
                const vel = p.velocity || 0;
                const confScore = p.confluence_score || 0;
                
                const barWidth = Math.min(Math.abs(confScore) * 100, 100);
                const barHtml = confScore >= 0 
                    ? `<div class="conf-bar-fill conf-pos" style="width: ${barWidth/2}%;"></div>`
                    : `<div class="conf-bar-fill conf-neg" style="width: ${barWidth/2}%;"></div>`;

                const techSigClass = typeof p.signal_strength === 'string' && p.signal_strength.includes('BUY') ? 'val-pos' : (typeof p.signal_strength === 'string' && p.signal_strength.includes('SELL') ? 'val-neg' : 'text-muted');

                return `
                <tr style="animation: fadeIn 0.3s ease-out ${idx * 0.02}s both;">
                    <td class="col-script">
                        <span style="opacity:0.5; font-size:0.7rem; font-family:'JetBrains Mono', monospace; width:15px;">${idx+1}</span>
                        ${p.symbol}
                    </td>
                    <td>${fmtNum(p.ltp)}</td>
                    <td class="${colorClass(ac)}">${ac >= 0 ? '+':''}${fmtNum(ac, 4)}</td>
                    <td class="${colorClass(vel)}">${vel >= 0 ? '+':''}${fmtNum(vel, 4)}</td>
                    <td style="color: #cbd5e1;">${fmtNum(p.psar_af, 2)}</td>
                    <td style="font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.05em;" class="${techSigClass}">
                        ${sigEmoji[p.signal_strength] || '➖'} ${p.signal_strength?.replace('_', ' ') || '-'}
                    </td>
                    <td>
                        <span class="badge badge-sentiment-${p.prediction}">${p.prediction.replace('strong_', 'Strong ')}</span>
                    </td>
                    <td>
                        <div class="conf-cell" title="Confluence Score: ${confScore}">
                            <span class="conf-score ${colorClass(confScore)}">${confScore >= 0 ? '+':''}${fmtNum(confScore, 2)}</span>
                            <div class="conf-bar-wrapper">${barHtml}</div>
                        </div>
                    </td>
                </tr>
            `}).join('');

            // To avoid losing scroll position completely wiping table, check if html changed
            // Usually we'd want a virtual DOM, but for this simple dash, diffing HTML string prevents most stutter
            if(tbody.innerHTML !== newHtml) {
                tbody.innerHTML = newHtml;
            }
        }

        function renderAlerts(alerts) {
            const c = document.getElementById('alertsContainer');
            if(!alerts || !alerts.length) { c.innerHTML = '<div style="padding:2rem; text-align:center; color:var(--text-muted); font-size:0.9rem;">No actionable alerts. System monitoring...</div>'; return; }
            
            const newHtml = alerts.map(a => `
                <div class="alert-item alert-${a.severity}">
                    <div class="alert-title">
                        ${a.severity === 'high' ? '⚠️' : '⚡'} ${a.title}
                    </div>
                    <div style="color: rgba(255,255,255,0.7); line-height: 1.5; font-size: 0.8rem;">${a.message}</div>
                    <div class="alert-time">${new Date(a.timestamp).toLocaleTimeString()}</div>
                </div>
            `).join('');

            if(c.innerHTML !== newHtml) {
                c.innerHTML = newHtml;
            }
        }

        function renderChart(data) {
            if(!data.sector_analysis) return;
            
            const counts = {'Bullish':0, 'Bearish':0, 'Neutral':0};
            data.top_predictions.forEach(p => {
                if(p.prediction.includes('bullish')) counts['Bullish']++;
                else if(p.prediction.includes('bearish')) counts['Bearish']++;
                else counts['Neutral']++;
            });
            
            const plotData = [{
                values: [counts['Bullish'], counts['Neutral'], counts['Bearish']],
                labels: ['Bullish', 'Neutral', 'Bearish'],
                type: 'pie',
                hole: 0.7,
                marker: { 
                    colors: ['#10b981', '#475569', '#ef4444'],
                    line: {color: '#1e293b', width: 2}
                },
                textinfo: 'none',
                hoverinfo: 'label+percent',
                hovertemplate: '<b>%{label}</b><br>%{percent}<extra></extra>'
            }];
            
            const layout = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                margin: {t:20, b:20, l:20, r:20},
                showlegend: true,
                legend: { orientation: 'h', y: -0.2, font: {color: '#cbd5e1', family: 'Inter'} },
                font: { color: '#f8fafc', family: 'Inter' },
                annotations: [{ font: {size: 16, color: '#f8fafc', weight: 600}, showarrow: false, text: 'Macro Bias' }],
                transition: {duration: 500, easing: 'cubic-in-out'}
            };
            
            const chartDiv = document.getElementById('sentimentChart');
            
            // KEY FIX: Use Plotly.react instead of Plotly.newPlot to update without recreating DOM
            if (!chartInitialized) {
                chartDiv.innerHTML = ''; // Clear skeleton
                Plotly.newPlot(chartDiv, plotData, layout, {displayModeBar: false, responsive: true});
                chartInitialized = true;
            } else {
                Plotly.react(chartDiv, plotData, layout, {displayModeBar: false, responsive: true});
            }
        }

        // Sorting Logic
        document.querySelectorAll('.confluence-table th').forEach(th => {
            th.addEventListener('click', () => {
                const col = th.dataset.sort;
                if(!col) return;
                
                // Add active state styling to headers
                document.querySelectorAll('.confluence-table th').forEach(h => h.style.color = 'var(--text-muted)');
                th.style.color = '#fff';
                
                if(sortCol === col) {
                    sortDesc = !sortDesc;
                } else {
                    sortCol = col;
                    sortDesc = true;
                }
                
                // Add visual indicator of sort direction
                document.querySelectorAll('.sort-arrow').forEach(a => a.remove());
                th.innerHTML += `<span class="sort-arrow" style="margin-left:5px; font-size:0.8rem; color:var(--accent-primary)">${sortDesc ? '↓' : '↑'}</span>`;
                
                if(currentData) renderScreener(currentData.top_predictions);
            });
        });

        // Initialize sort arrow on default column
        const defaultTh = document.querySelector('.confluence-table th[data-sort="confluence_score"]');
        if(defaultTh) {
            defaultTh.style.color = '#fff';
            defaultTh.innerHTML += `<span class="sort-arrow" style="margin-left:5px; font-size:0.8rem; color:var(--accent-primary)">↓</span>`;
        }

        // Init
        updateDashboard();
        
        // Refresh every 15s (won't hang UI anymore thanks to DOM diffing & Plotly.react)
        setInterval(updateDashboard, 15000); 
    </script>
</body>
</html>'''

with open('src/api/main.py', 'w') as f:
    f.write(re.sub(r'def get_dashboard_html\(\) -> str:[\s\S]+?if __name__ == "__main__":', new_html_func + '\n\nif __name__ == "__main__":', content))
"""
