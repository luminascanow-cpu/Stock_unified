import fs from "node:fs";
import path from "node:path";

const repoRoot = path.resolve(import.meta.dirname, "../..");
const outputDir = path.join(repoRoot, "android_app/app/src/main/assets");
const outputPath = path.join(outputDir, "index.html");

const html = String.raw`<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Confluence Terminal</title>
  <style>
    :root {
      --bg: #0b1321;
      --bg-deep: #060e1c;
      --surface-low: #141c2a;
      --surface: #18202e;
      --surface-high: #222a39;
      --surface-higher: #2d3544;
      --line: #45474c;
      --line-soft: rgba(143, 144, 150, 0.32);
      --text: #dbe2f6;
      --muted: #c5c6cc;
      --dim: #777d8c;
      --teal: #36ffc4;
      --teal-2: #00e1ab;
      --red: #e73b3e;
      --red-soft: #2e0002;
      --yellow: #ffd60a;
      --black: #002116;
    }

    * { box-sizing: border-box; }
    html, body { margin: 0; min-height: 100%; background: var(--bg); color: var(--text); }
    body {
      font-family: "Hanken Grotesk", "Avenir Next", system-ui, sans-serif;
      -webkit-font-smoothing: antialiased;
      -webkit-text-size-adjust: 100%;
      text-size-adjust: 100%;
      overflow-x: hidden;
    }

    .app {
      min-height: 100dvh;
      background: linear-gradient(180deg, #0b1321 0%, #08101d 100%);
      padding-bottom: 118px;
      padding-bottom: calc(100px + max(18px, env(safe-area-inset-bottom)));
      transition: filter 220ms ease, opacity 220ms ease;
    }

    .topbar {
      position: sticky;
      top: 0;
      z-index: 5;
      min-height: 56px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 0 16px;
      background: rgba(11, 19, 33, 0.96);
      border-bottom: 1px solid var(--line);
      backdrop-filter: blur(14px);
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
      font-family: "JetBrains Mono", "SFMono-Regular", monospace;
      font-weight: 800;
      color: #fff;
      letter-spacing: 0;
      font-size: 16px;
      white-space: nowrap;
      flex: 1 1 auto;
      overflow: hidden;
    }

    .brand > span:last-child {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .terminal-mark {
      width: 20px;
      height: 20px;
      display: grid;
      place-items: center;
      border: 1px solid #fff;
      border-radius: 2px;
      color: #fff;
      font-size: 12px;
      line-height: 1;
      flex: 0 0 auto;
    }

    .live-pill {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 7px 9px;
      background: var(--surface-high);
      border: 1px solid var(--line);
      border-radius: 999px;
      color: var(--teal);
      font: 800 10px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      flex: 0 0 auto;
    }

    .dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: var(--teal);
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0% { box-shadow: 0 0 0 0 rgba(54, 255, 196, 0.45); }
      70% { box-shadow: 0 0 0 9px rgba(54, 255, 196, 0); }
      100% { box-shadow: 0 0 0 0 rgba(54, 255, 196, 0); }
    }

    main { padding: 16px; max-width: 760px; margin: 0 auto; }
    .view { display: none; animation: enter 180ms ease-out; }
    .view.active { display: block; }
    @keyframes enter { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

    .section-label {
      margin: 0 0 6px;
      color: var(--muted);
      font: 800 10px/12px "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .headline {
      margin: 0;
      font: 800 20px/28px "JetBrains Mono", "SFMono-Regular", monospace;
      color: #fff;
      letter-spacing: 0;
    }

    .body-copy {
      margin: 7px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }

    .panel {
      position: relative;
      overflow: hidden;
      background: var(--surface-low);
      border: 1px solid var(--line);
      border-radius: 4px;
    }

    .panel-pad { padding: 16px; }
    .stack { display: grid; gap: 12px; }
    .grid-2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .grid-3 { display: grid; grid-template-columns: minmax(0, 1fr); gap: 12px; }

    .hero {
      min-height: 310px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }

    .scanline {
      position: absolute;
      left: 0;
      right: 0;
      height: 2px;
      background: linear-gradient(90deg, transparent, var(--teal), transparent);
      opacity: 0.14;
      animation: scan 4s linear infinite;
    }

    @keyframes scan { from { top: -5%; } to { top: 105%; } }

    .hero-top {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: flex-start;
    }

    .hero-top > * { min-width: 0; }

    .price {
      text-align: right;
      color: var(--teal);
      font: 700 19px/1.25 "JetBrains Mono", "SFMono-Regular", monospace;
      font-variant-numeric: tabular-nums lining-nums;
    }

    .price-value { display: block; white-space: nowrap; }

    .quote-facts {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
      margin-top: 10px;
      color: var(--text);
      text-align: left;
    }

    .quote-fact {
      min-width: 0;
      padding: 7px;
      border: 1px solid rgba(69, 71, 76, 0.72);
      background: rgba(6, 14, 28, 0.68);
    }

    .quote-fact span {
      display: block;
      color: var(--dim);
      font: 800 7px/1.2 "JetBrains Mono", "SFMono-Regular", monospace;
      text-transform: uppercase;
    }

    .quote-fact strong {
      display: block;
      margin-top: 4px;
      color: #fff;
      font: 900 10px/1.25 "JetBrains Mono", "SFMono-Regular", monospace;
      overflow-wrap: anywhere;
    }

    .change {
      display: block;
      margin-top: 8px;
      font-size: 14px;
      letter-spacing: 0;
    }

    .hero-word {
      color: var(--teal);
      font: 900 54px/0.92 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      margin: 26px 0 18px;
    }

    .spark {
      font-size: 46px;
      letter-spacing: 0;
      color: var(--teal);
      margin-left: 8px;
    }

    .bar {
      height: 5px;
      background: var(--surface-higher);
      overflow: hidden;
      margin-bottom: 12px;
    }

    .bar > span {
      display: block;
      height: 100%;
      background: var(--teal);
      width: var(--value, 70%);
    }

    .gauge {
      min-height: 350px;
      text-align: center;
      display: grid;
      place-items: center;
    }

    .gauge-box {
      width: 208px;
      height: 208px;
      border: 12px solid var(--surface-higher);
      border-radius: 12px;
      display: grid;
      place-items: center;
      position: relative;
      margin: 14px auto;
    }

    .gauge-box:after {
      content: "";
      position: absolute;
      width: 150px;
      height: 150px;
      border-top: 16px solid var(--teal);
      border-right: 16px solid var(--teal);
      transform: rotate(45deg);
      right: -30px;
      top: 24px;
      border-radius: 4px;
    }

    .gauge-value {
      position: relative;
      z-index: 1;
      font: 800 42px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      color: #fff;
    }

    .gauge-value span {
      display: block;
      margin-top: 8px;
      color: var(--teal);
      font-size: 14px;
      letter-spacing: 0;
    }

    .metric-card {
      background: var(--surface-low);
      border: 1px solid var(--line);
      border-radius: 4px;
      padding: 16px;
      min-height: 118px;
    }

    .macro-strip {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }

    .macro-card {
      background: var(--surface-low);
      border: 1px solid var(--line);
      border-radius: 4px;
      padding: 14px;
      min-width: 0;
    }

    .metric-row {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 12px;
      margin-top: 20px;
      min-width: 0;
    }

    .metric-main {
      color: #fff;
      font: 800 20px/1.2 "JetBrains Mono", "SFMono-Regular", monospace;
      font-variant-numeric: tabular-nums lining-nums;
      min-width: 0;
      overflow-wrap: anywhere;
    }

    .metric-side {
      color: var(--teal);
      font: 800 11px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      font-variant-numeric: tabular-nums lining-nums;
      white-space: nowrap;
    }

    .macro-card .metric-row {
      display: grid;
      justify-content: stretch;
      gap: 7px;
      margin-top: 14px;
    }

    .macro-card .metric-side { justify-self: start; }

    .vix-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }

    .vix-regime {
      color: var(--muted);
      border-color: var(--line);
    }

    .vix-scale {
      position: relative;
      height: 8px;
      margin-top: 16px;
      background: linear-gradient(90deg, var(--teal) 0 28%, var(--yellow) 50% 70%, var(--red) 100%);
      opacity: 0.78;
    }

    .vix-scale-marker {
      position: absolute;
      top: -5px;
      left: var(--vix-position, 0%);
      width: 3px;
      height: 18px;
      background: #fff;
      box-shadow: 0 0 0 2px var(--bg-deep);
      transform: translateX(-50%);
    }

    .vix-context {
      min-height: 30px;
      margin: 12px 0 0;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.35;
    }

    .sector-flow-panel {
      background:
        linear-gradient(110deg, rgba(54, 255, 196, 0.09), transparent 34%),
        var(--surface-low);
      border: 1px solid var(--line);
      border-radius: 4px;
      overflow: hidden;
    }

    .sector-flow-head {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 14px;
      padding: 16px;
      border-bottom: 1px solid var(--line);
    }

    .sector-flow-title {
      margin: 0;
      color: #fff;
      font: 800 20px/1.2 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
    }

    .sector-flow-session {
      margin-left: 0;
      color: var(--teal);
      border-color: rgba(54, 255, 196, 0.45);
      white-space: nowrap;
    }

    .sector-flow-summary {
      min-height: 54px;
      margin: 0;
      padding: 14px 16px;
      color: var(--text);
      font: 800 13px/1.5 "JetBrains Mono", "SFMono-Regular", monospace;
      border-bottom: 1px solid rgba(69, 71, 76, 0.72);
    }

    .sector-flow-kpis {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      border-bottom: 1px solid var(--line);
      background: var(--bg-deep);
    }

    .sector-flow-kpi {
      min-width: 0;
      min-height: 74px;
      padding: 12px 14px;
      border-right: 1px solid rgba(69, 71, 76, 0.72);
      border-bottom: 1px solid rgba(69, 71, 76, 0.72);
    }

    .sector-flow-kpi:nth-child(even) { border-right: 0; }
    .sector-flow-kpi:nth-last-child(-n+2) { border-bottom: 0; }

    .sector-flow-kpi span {
      display: block;
      color: var(--dim);
      font: 800 9px/1.2 "JetBrains Mono", "SFMono-Regular", monospace;
      text-transform: uppercase;
    }

    .sector-flow-kpi strong {
      display: block;
      margin-top: 8px;
      color: #fff;
      font: 800 15px/1.2 "JetBrains Mono", "SFMono-Regular", monospace;
      font-variant-numeric: tabular-nums lining-nums;
      overflow-wrap: anywhere;
    }

    .flow-visual-section {
      border-bottom: 1px solid var(--line);
      background: rgba(6, 14, 28, 0.42);
    }

    .flow-section-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 9px 14px;
      padding: 14px 16px 10px;
    }

    .flow-section-title {
      margin: 0;
      color: #fff;
      font: 900 12px/1.2 "JetBrains Mono", "SFMono-Regular", monospace;
      text-transform: uppercase;
    }

    .flow-section-note {
      color: var(--dim);
      font: 800 9px/1.3 "JetBrains Mono", "SFMono-Regular", monospace;
      text-transform: uppercase;
    }

    .sector-map-wrap {
      padding: 0 12px 14px;
    }

    .sector-map-grid {
      position: relative;
      width: 100%;
      aspect-ratio: 16 / 10;
      min-height: 260px;
      background: var(--bg-deep);
      border: 1px solid var(--line);
      overflow: hidden;
    }

    .sector-map-tile {
      position: absolute;
      min-width: 0;
      min-height: 0;
      padding: 9px;
      overflow: hidden;
      border: 1px solid rgba(219, 226, 246, 0.18);
      color: #fff;
      text-align: left;
    }

    .sector-map-tile strong,
    .sector-map-tile span,
    .sector-map-tile small {
      display: block;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .sector-map-tile strong {
      font: 900 10px/1.2 "JetBrains Mono", "SFMono-Regular", monospace;
      text-transform: uppercase;
      white-space: nowrap;
    }

    .sector-map-tile span {
      margin-top: 6px;
      font: 900 12px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      font-variant-numeric: tabular-nums lining-nums;
    }

    .sector-map-tile small {
      margin-top: 5px;
      color: rgba(255, 255, 255, 0.74);
      font: 800 8px/1.25 "JetBrains Mono", "SFMono-Regular", monospace;
      white-space: nowrap;
    }

    .sector-map-tile.compact { padding: 6px; }
    .sector-map-tile.compact span { margin-top: 4px; font-size: 9px; }
    .sector-map-tile.compact small { display: none; }

    .flow-detail-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 12px 16px;
      color: var(--dim);
      font: 800 9px/1.2 "JetBrains Mono", "SFMono-Regular", monospace;
      text-transform: uppercase;
      border-bottom: 1px solid rgba(69, 71, 76, 0.58);
    }

    .sector-flow-list {
      display: grid;
    }

    .sector-flow-row {
      display: grid;
      gap: 9px;
      padding: 13px 16px;
      border-bottom: 1px solid rgba(69, 71, 76, 0.58);
    }

    .sector-flow-row:last-child { border-bottom: 0; }

    .sector-flow-row-head,
    .sector-flow-row-foot,
    .sector-flow-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      min-width: 0;
    }

    .sector-flow-row-foot { flex-wrap: wrap; }

    .sector-flow-name {
      color: #fff;
      font: 900 12px/1.2 "JetBrains Mono", "SFMono-Regular", monospace;
      text-transform: uppercase;
    }

    .sector-flow-value {
      color: var(--text);
      font: 900 12px/1.2 "JetBrains Mono", "SFMono-Regular", monospace;
      font-variant-numeric: tabular-nums lining-nums;
      text-align: right;
    }

    .sector-flow-direction {
      color: var(--muted);
      font: 800 9px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      text-transform: uppercase;
    }

    .sector-flow-track {
      position: relative;
      height: 8px;
      background: var(--surface-higher);
      overflow: hidden;
    }

    .sector-flow-track:after {
      content: "";
      position: absolute;
      inset: 0 auto 0 50%;
      width: 1px;
      background: rgba(219, 226, 246, 0.6);
    }

    .sector-flow-bar {
      position: absolute;
      top: 0;
      bottom: 0;
      width: var(--flow-size, 0%);
    }

    .sector-flow-bar.inflow {
      left: 50%;
      background: var(--teal);
    }

    .sector-flow-bar.outflow {
      right: 50%;
      background: var(--red);
    }

    .sector-flow-meta {
      justify-content: flex-start;
      color: var(--dim);
      font: 800 9px/1.3 "JetBrains Mono", "SFMono-Regular", monospace;
      text-transform: uppercase;
    }

    .sector-flow-leader {
      max-width: 100%;
      min-height: 32px;
      border: 1px solid rgba(54, 255, 196, 0.34);
      background: rgba(54, 255, 196, 0.06);
      color: var(--teal);
      padding: 0 9px;
      font: 900 9px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      text-transform: uppercase;
      overflow-wrap: anywhere;
      cursor: pointer;
    }

    .sector-flow-leader:focus-visible {
      outline: 2px solid #fff;
      outline-offset: 2px;
    }

    .sector-flow-leader:active { transform: translateY(1px); }

    @media (hover: hover) {
      .sector-flow-leader:hover {
        color: #fff;
        border-color: #fff;
      }
    }

    .sector-flow-empty {
      min-height: 148px;
      display: grid;
      place-items: center;
      padding: 24px 18px;
      color: var(--muted);
      text-align: center;
      font-size: 13px;
      line-height: 1.5;
    }

    .sector-flow-footnote {
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 7px 14px;
      padding: 11px 16px;
      border-top: 1px solid var(--line);
      color: var(--dim);
      font: 800 9px/1.4 "JetBrains Mono", "SFMono-Regular", monospace;
      text-transform: uppercase;
    }

    .sector-flow-method {
      margin: 0;
      padding: 11px 16px 14px;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.45;
      border-top: 1px solid rgba(69, 71, 76, 0.55);
    }

    .summary {
      background: var(--surface-high);
      border: 1px solid var(--line);
    }

    .summary > div {
      padding: 18px;
      border-right: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
      min-height: 112px;
    }

    .summary > div:nth-child(even) { border-right: 0; }
    .summary > div:nth-last-child(-n+2) { border-bottom: 0; }

    .summary-value {
      margin-top: 10px;
      font: 800 19px/1.25 "JetBrains Mono", "SFMono-Regular", monospace;
      color: #fff;
      font-variant-numeric: tabular-nums lining-nums;
      overflow-wrap: anywhere;
    }

    .tiny-chip {
      display: inline-block;
      padding: 3px 5px;
      margin-left: 4px;
      border: 1px solid var(--line);
      color: var(--muted);
      font: 700 10px/1 "JetBrains Mono", "SFMono-Regular", monospace;
    }

    .status-line {
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
      padding: 14px 16px;
      background: var(--surface-low);
      border: 1px solid var(--line);
      font: 800 12px/1.4 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
    }

    .table-card {
      background: var(--surface-low);
      border: 1px solid var(--line);
      overflow: hidden;
    }

    .data-status-row {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 8px 14px;
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      background: var(--bg-deep);
      color: var(--muted);
      font: 800 10px/1.35 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .table-scroll { overflow-x: auto; }
    table { width: 100%; min-width: 780px; border-collapse: collapse; }
    th, td {
      padding: 12px 10px;
      border-bottom: 1px solid rgba(69, 71, 76, 0.72);
      text-align: left;
      white-space: nowrap;
    }

    th {
      color: var(--muted);
      font: 800 10px/12px "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      background: var(--bg-deep);
      text-transform: uppercase;
    }

    td {
      color: #fff;
      font: 700 13px/16px "JetBrains Mono", "SFMono-Regular", monospace;
    }

    .right { text-align: right; }
    .teal { color: var(--teal) !important; }
    .red { color: #ffb3ae !important; }
    .yellow { color: var(--yellow) !important; }
    .muted { color: var(--muted) !important; }
    .dim { color: var(--dim) !important; }

    .cmp-cell {
      display: grid;
      gap: 3px;
      justify-items: end;
      line-height: 1;
    }

    .cmp-value {
      color: #fff;
      font: 800 13px/1 "JetBrains Mono", "SFMono-Regular", monospace;
    }

    .cmp-change {
      font: 900 10px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
    }

    .symbol-cell {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-width: 0;
    }

    .fo-badge,
    .rsi-pill {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 1px solid currentColor;
      font: 900 9px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .fo-badge {
      min-height: 18px;
      padding: 0 5px;
      color: var(--yellow);
      background: rgba(255, 214, 10, 0.12);
    }

    .rsi-stack {
      display: inline-grid;
      gap: 3px;
      justify-items: end;
      line-height: 1;
    }

    .rsi-pill {
      min-width: 44px;
      min-height: 22px;
      color: var(--muted);
      background: rgba(197, 198, 204, 0.08);
    }

    .rsi-pill.priority {
      color: var(--teal);
      background: rgba(54, 255, 196, 0.1);
    }

    .rsi-pill.hot {
      color: var(--yellow);
      background: rgba(255, 214, 10, 0.12);
    }

    .rsi-label {
      color: var(--dim);
      font: 900 8px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .matrix-action-head {
      width: 42px;
    }

    .row-delete-button {
      width: 30px;
      height: 30px;
      display: inline-grid;
      place-items: center;
      border: 1px solid rgba(231, 59, 62, 0.45);
      border-radius: 2px;
      background: rgba(231, 59, 62, 0.08);
      color: #ffb3ae;
      font: 900 13px/1 "JetBrains Mono", "SFMono-Regular", monospace;
    }

    .row-delete-button:active {
      background: rgba(231, 59, 62, 0.2);
      transform: scale(0.96);
    }

    .badge {
      display: inline-flex;
      align-items: center;
      padding: 4px 6px;
      border: 1px solid currentColor;
      font: 800 10px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .badge.teal { background: rgba(54, 255, 196, 0.12); }
    .badge.red { background: rgba(231, 59, 62, 0.13); }
    .badge.gray { color: var(--muted); background: rgba(197, 198, 204, 0.08); }
    .badge.yellow { color: var(--yellow); background: rgba(255, 214, 10, 0.12); }

    .score {
      height: 6px;
      width: 82px;
      background: var(--surface-higher);
      position: relative;
      display: inline-block;
      vertical-align: middle;
      margin-left: 8px;
    }

    .score span {
      position: absolute;
      inset: 0 auto 0 50%;
      background: var(--teal);
      width: var(--w, 34%);
    }

    .intel-card,
    .alert-card,
    .event-card {
      background: var(--surface-low);
      border: 1px solid var(--line);
      border-radius: 4px;
      padding: 16px;
    }

    .intel-card {
      display: grid;
      gap: 12px;
      color: inherit;
      text-decoration: none;
    }

    a.intel-card:active { border-color: var(--teal); }

    .intel-image {
      min-height: 145px;
      border: 1px solid rgba(69, 71, 76, 0.74);
      background:
        linear-gradient(115deg, rgba(54, 255, 196, 0.16), transparent 42%),
        repeating-linear-gradient(0deg, rgba(219, 226, 246, 0.08) 0 1px, transparent 1px 10px),
        linear-gradient(140deg, #0b1321, #111b2a 62%, #1d2637);
      position: relative;
      overflow: hidden;
    }

    .intel-image:before {
      content: "";
      position: absolute;
      inset: 20% -20% auto -20%;
      height: 1px;
      background: var(--teal);
      box-shadow: 0 32px 0 rgba(54, 255, 196, 0.5), 0 78px 0 rgba(231, 59, 62, 0.55);
      transform: rotate(-8deg);
    }

    .source-row,
    .alert-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      color: var(--muted);
      font: 800 10px/1.3 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .source-row span:first-child,
    .alert-top span:first-child {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .intel-title,
    .alert-title {
      margin: 0;
      color: #fff;
      font: 800 14px/20px "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
    }

    .intel-summary {
      margin-top: -2px;
    }

    .intel-link-row {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }

    .intel-head {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: start;
    }

    .alert-card {
      border-left-width: 4px;
      display: grid;
      gap: 12px;
    }

    .alert-card.critical { border-left-color: var(--red); }
    .alert-card.warn { border-left-color: var(--teal); }
    .alert-card.info { border-left-color: var(--line); }

    .alert-body {
      padding: 12px;
      background: var(--bg);
      border: 1px solid rgba(69, 71, 76, 0.54);
      color: var(--text);
      font-size: 13px;
      line-height: 1.45;
    }

    .news-action-card { gap: 14px; }

    .news-action-metrics {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      border: 1px solid rgba(69, 71, 76, 0.68);
      background: var(--bg-deep);
    }

    .news-action-metric {
      min-width: 0;
      padding: 10px;
      border-right: 1px solid rgba(69, 71, 76, 0.68);
    }

    .news-action-metric:nth-child(2) { border-right: 0; }
    .news-action-metric:last-child {
      grid-column: 1 / -1;
      border-top: 1px solid rgba(69, 71, 76, 0.68);
      border-right: 0;
    }
    .news-action-metric span {
      display: block;
      color: var(--dim);
      font: 800 8px/1.2 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .news-action-metric strong {
      display: block;
      margin-top: 6px;
      color: #fff;
      font: 900 13px/1.2 "JetBrains Mono", "SFMono-Regular", monospace;
      overflow-wrap: anywhere;
    }

    .news-action-headline,
    .news-action-strategy,
    .news-action-risk { margin: 0; }

    .news-action-headline {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }

    .news-action-strategy {
      padding: 12px;
      border-left: 2px solid var(--teal);
      background: var(--bg);
      color: var(--text);
      font-size: 13px;
      line-height: 1.5;
    }

    .news-action-risk {
      color: var(--dim);
      font-size: 10px;
      line-height: 1.4;
    }

    .trade-plan {
      border: 1px solid rgba(69, 71, 76, 0.72);
      background: var(--bg-deep);
      overflow: hidden;
    }

    .trade-plan-head,
    .option-plan-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 9px 10px;
      color: var(--muted);
      font: 900 9px/1.25 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .trade-levels {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      border-top: 1px solid rgba(69, 71, 76, 0.72);
    }

    .trade-level {
      min-width: 0;
      padding: 10px;
      border-right: 1px solid rgba(69, 71, 76, 0.72);
      border-bottom: 1px solid rgba(69, 71, 76, 0.72);
    }

    .trade-level:nth-child(2n) { border-right: 0; }
    .trade-level:last-child {
      grid-column: 1 / -1;
      border-right: 0;
      border-bottom: 0;
    }
    .trade-level > span,
    .trade-note-label {
      display: block;
      color: var(--dim);
      font: 800 8px/1.2 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .trade-level strong {
      display: block;
      margin-top: 5px;
      color: #fff;
      font: 900 13px/1.3 "JetBrains Mono", "SFMono-Regular", monospace;
      font-variant-numeric: tabular-nums lining-nums;
      overflow-wrap: anywhere;
    }

    .trade-range {
      display: grid !important;
      gap: 2px;
    }

    .trade-condition,
    .option-plan-note {
      margin: 0;
      padding: 10px;
      border-top: 1px solid rgba(69, 71, 76, 0.52);
      color: var(--muted);
      font-size: 11px;
      line-height: 1.45;
    }

    .option-plan {
      border-top: 2px solid rgba(255, 214, 10, 0.7);
      background: rgba(255, 214, 10, 0.035);
    }

    .option-plan-head strong { color: var(--yellow); }

    .intel-actions {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 8px;
    }

    .discovery-panel {
      padding: 12px 0;
      border-top: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
    }

    .discovery-list { display: grid; }

    .discovery-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: center;
      padding: 12px 0;
      border-top: 1px solid rgba(69, 71, 76, 0.5);
    }

    .discovery-row:first-child { border-top: 0; }
    .discovery-symbol {
      color: #fff;
      font: 900 13px/1.2 "JetBrains Mono", "SFMono-Regular", monospace;
    }

    .discovery-headline {
      margin: 5px 0 0;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.4;
    }

    .collecting-overlay {
      position: fixed;
      inset: 0;
      z-index: 40;
      display: none;
      place-items: center;
      padding: 24px;
      background: rgba(6, 14, 28, 0.88);
      backdrop-filter: blur(8px);
    }

    .collecting-overlay.active { display: grid; }

    .collecting-panel {
      width: min(100%, 320px);
      padding: 20px;
      border: 1px solid var(--line);
      background: var(--surface-low);
      box-shadow: 0 18px 52px rgba(0, 0, 0, 0.42);
    }

    .collecting-grid {
      position: relative;
      width: 76px;
      height: 76px;
      margin-bottom: 18px;
      overflow: hidden;
      border: 1px solid var(--teal);
      background-image:
        linear-gradient(rgba(54, 255, 196, 0.12) 1px, transparent 1px),
        linear-gradient(90deg, rgba(54, 255, 196, 0.12) 1px, transparent 1px);
      background-size: 15px 15px;
    }

    .collecting-grid::before {
      content: "";
      position: absolute;
      left: 0;
      right: 0;
      height: 2px;
      background: var(--teal);
      box-shadow: 0 0 12px rgba(54, 255, 196, 0.7);
      animation: collect-scan 1.25s linear infinite;
    }

    .collecting-grid::after {
      content: "+";
      position: absolute;
      inset: 0;
      display: grid;
      place-items: center;
      color: #fff;
      font: 900 24px/1 "JetBrains Mono", "SFMono-Regular", monospace;
    }

    .collecting-title {
      margin: 0;
      color: #fff;
      font: 900 14px/1.35 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
    }

    .collecting-step {
      min-height: 36px;
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }

    .collecting-bars {
      display: grid;
      grid-template-columns: 1fr 0.7fr 0.42fr;
      gap: 5px;
      margin-top: 16px;
    }

    .collecting-bars span {
      height: 3px;
      background: var(--teal);
      transform-origin: left;
      animation: collect-bars 1.1s ease-in-out infinite alternate;
    }

    .collecting-bars span:nth-child(2) { animation-delay: 160ms; }
    .collecting-bars span:nth-child(3) { animation-delay: 320ms; }

    @keyframes collect-scan { from { top: -2px; } to { top: 76px; } }
    @keyframes collect-bars { from { transform: scaleX(0.25); opacity: 0.45; } to { transform: scaleX(1); opacity: 1; } }

    @media (prefers-reduced-motion: reduce) {
      .collecting-grid::before,
      .collecting-bars span,
      .dot,
      .scanline,
      .view { animation: none !important; }
    }

    .news-source-link {
      color: var(--teal);
      font: 900 10px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      text-decoration: none;
    }

    .close-synthesis .alert-body {
      display: grid;
      gap: 10px;
    }

    .falling-row {
      width: 100%;
      appearance: none;
      display: grid;
      gap: 9px;
      padding-top: 10px;
      color: inherit;
      font: inherit;
      text-align: left;
      background: transparent;
      border-right: 0;
      border-bottom: 0;
      border-left: 0;
      border-top: 1px solid rgba(69, 71, 76, 0.54);
      cursor: pointer;
      transition: background-color 160ms ease, border-color 160ms ease, transform 120ms ease;
    }

    .falling-row:hover {
      border-top-color: rgba(54, 255, 196, 0.7);
      background: rgba(54, 255, 196, 0.035);
    }

    .falling-row:focus-visible {
      outline: 2px solid var(--teal);
      outline-offset: 3px;
    }

    .falling-row:active {
      transform: translateY(1px);
    }

    .falling-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
    }

    .falling-symbol {
      color: #fff;
      font: 900 13px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
    }

    .falling-open {
      display: inline-block;
      margin-left: 7px;
      color: var(--teal);
      font: 800 8px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      vertical-align: 1px;
    }

    .falling-meta {
      margin-top: 4px;
      color: var(--muted);
      font: 800 10px/1.3 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      text-transform: uppercase;
      overflow-wrap: anywhere;
    }

    .falling-drop {
      color: #ffb3ae;
      font: 900 13px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      text-align: right;
      font-variant-numeric: tabular-nums lining-nums;
      white-space: nowrap;
    }

    .falling-prices {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }

    .falling-price {
      min-width: 0;
      padding: 8px;
      border: 1px solid rgba(69, 71, 76, 0.54);
      background: rgba(6, 14, 28, 0.6);
    }

    .falling-price span {
      display: block;
      color: var(--dim);
      font: 800 8px/1.2 "JetBrains Mono", "SFMono-Regular", monospace;
      text-transform: uppercase;
    }

    .falling-price strong {
      display: block;
      margin-top: 5px;
      color: #fff;
      font: 900 12px/1.2 "JetBrains Mono", "SFMono-Regular", monospace;
      font-variant-numeric: tabular-nums lining-nums;
      overflow-wrap: anywhere;
    }

    .event-grid {
      display: grid;
      gap: 10px;
    }

    .event-card {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: center;
      border-left: 4px solid var(--line);
    }

    .event-card.high { border-left-color: var(--red); }
    .event-card.medium { border-left-color: var(--teal); }

    .event-copy {
      min-width: 0;
      display: grid;
      gap: 6px;
    }

    .event-title {
      margin: 0;
      color: #fff;
      font: 800 13px/18px "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
    }

    .event-note {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }

    .event-countdown {
      min-width: 52px;
      text-align: right;
      color: var(--teal);
      font: 900 17px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
    }

    .matrix-row { cursor: pointer; }
    .row-open-button {
      appearance: none;
      display: inline-flex;
      max-width: 100%;
      padding: 4px;
      margin: -4px;
      border: 0;
      border-radius: 4px;
      color: inherit;
      background: transparent;
      font: inherit;
      text-align: left;
      cursor: pointer;
    }
    .row-open-button:focus-visible {
      outline: 2px solid var(--teal);
      outline-offset: 2px;
    }
    .matrix-row.fo-row {
      background: linear-gradient(90deg, rgba(255, 214, 10, 0.08), transparent 42%);
    }
    .matrix-row.fo-row td:first-child {
      box-shadow: inset 3px 0 0 rgba(255, 214, 10, 0.86);
    }
    .matrix-row.news-priority {
      background: rgba(231, 59, 62, 0.11);
    }
    .matrix-row.news-priority td:first-child {
      box-shadow: inset 4px 0 0 var(--red);
    }
    .matrix-row.news-watch {
      background: rgba(54, 255, 196, 0.06);
    }
    .news-symbol-badge {
      display: inline-flex;
      align-items: center;
      min-height: 18px;
      padding: 0 5px;
      border: 1px solid currentColor;
      color: #ffb3ae;
      background: rgba(231, 59, 62, 0.15);
      font: 900 9px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
    }
    .matrix-row:active { background: rgba(54, 255, 196, 0.08); }
    .matrix-row.stale-technical {
      background: linear-gradient(90deg, rgba(255, 214, 10, 0.07), transparent 48%);
    }
    .data-quality-badge {
      display: inline-flex;
      min-height: 18px;
      align-items: center;
      padding: 0 5px;
      border: 1px solid currentColor;
      color: var(--muted);
      background: rgba(197, 198, 204, 0.08);
      font: 900 8px/1 "JetBrains Mono", "SFMono-Regular", monospace;
    }
    .cmp-freshness {
      color: var(--dim);
      font: 800 8px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      text-transform: uppercase;
    }

    .detail-hero {
      min-height: 190px;
      display: grid;
      gap: 16px;
      align-content: space-between;
      background:
        linear-gradient(135deg, rgba(54, 255, 196, 0.12), transparent 38%),
        linear-gradient(180deg, var(--surface-low), #111a28);
    }

    .detail-symbol {
      margin: 8px 0 0;
      color: var(--teal);
      font: 900 50px/0.92 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
    }

    .detail-actions {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
    }

    .mini-action {
      min-height: 48px;
      border: 1px solid var(--teal);
      background: rgba(54, 255, 196, 0.12);
      color: var(--teal);
      padding: 9px 11px;
      font: 900 10px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .mini-action:disabled {
      opacity: 0.52;
      color: var(--muted);
      border-color: var(--line);
    }

    .detail-stats {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      border: 1px solid var(--line);
      background: var(--surface-high);
    }

    .detail-stats > div {
      padding: 14px;
      border-right: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
      min-width: 0;
    }

    .detail-stats > div:nth-child(even) { border-right: 0; }
    .detail-stats > div:nth-last-child(-n+2) { border-bottom: 0; }

    .detail-block {
      background: var(--surface-low);
      border: 1px solid var(--line);
      padding: 16px;
    }

    .revenue-chart {
      display: grid;
      gap: 12px;
      margin-top: 14px;
    }

    .revenue-row {
      display: grid;
      grid-template-columns: 54px minmax(0, 1fr) 72px;
      gap: 10px;
      align-items: center;
      color: var(--muted);
      font: 800 10px/1 "JetBrains Mono", "SFMono-Regular", monospace;
    }

    .revenue-track {
      height: 14px;
      background: var(--surface-higher);
      overflow: hidden;
    }

    .revenue-track span {
      display: block;
      height: 100%;
      width: var(--w, 10%);
      background: linear-gradient(90deg, var(--teal), #b9ffe9);
    }

    .detail-news {
      display: grid;
      gap: 10px;
      margin-top: 14px;
    }

    .news-link-card {
      display: grid;
      gap: 8px;
      padding: 13px;
      color: inherit;
      text-decoration: none;
      background: var(--bg);
      border: 1px solid rgba(69, 71, 76, 0.62);
    }

    .news-link-card:active { border-color: var(--teal); }

    .filter-row {
      display: flex;
      gap: 4px;
      overflow-x: auto;
      margin: 16px 0 12px;
      padding-bottom: 4px;
    }

    .filter-row button {
      border: 0;
      color: var(--muted);
      background: transparent;
      padding: 12px 16px;
      font: 800 10px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      white-space: nowrap;
    }

    .filter-row button.active {
      background: var(--teal);
      color: var(--black);
    }

    .add-stock-panel {
      display: grid;
      gap: 10px;
      padding: 12px;
      border: 1px solid var(--line);
      background:
        linear-gradient(90deg, rgba(54, 255, 196, 0.08), transparent 44%),
        var(--surface-low);
    }

    .add-stock-form {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 8px;
    }

    .visually-hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }

    .stock-input-wrap {
      position: relative;
      min-width: 0;
    }

    .stock-input {
      min-height: 42px;
      width: 100%;
      border: 1px solid var(--line);
      background: var(--bg-deep);
      color: #fff;
      padding: 0 44px 0 12px;
      border-radius: 2px;
      outline: none;
      font: 800 12px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .stock-input:focus {
      border-color: var(--teal);
      box-shadow: 0 0 0 3px rgba(54, 255, 196, 0.12);
    }

    .stock-input-clear {
      position: absolute;
      inset: 3px 3px 3px auto;
      width: 36px;
      border: 0;
      background: transparent;
      color: var(--muted);
      font: 900 17px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      cursor: pointer;
    }

    .stock-input-clear[hidden] { display: none; }

    .stock-input-clear:focus-visible {
      outline: 2px solid var(--teal);
      outline-offset: -2px;
    }

    .add-stock-button {
      min-height: 42px;
      min-width: 86px;
      border: 0;
      background: var(--teal);
      color: var(--black);
      padding: 0 14px;
      font: 900 11px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .add-stock-button:disabled {
      opacity: 0.58;
      background: var(--surface-higher);
      color: var(--muted);
    }

    .custom-stock-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }

    .custom-stock-chips[hidden] {
      display: none;
    }

    .stock-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 26px;
      padding: 0 8px;
      border: 1px solid rgba(54, 255, 196, 0.45);
      background: rgba(54, 255, 196, 0.08);
      color: var(--teal);
      font: 900 10px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
    }

    .stock-chip button {
      border: 0;
      background: transparent;
      color: inherit;
      min-width: 26px;
      min-height: 26px;
      padding: 0 4px;
      font: 900 14px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      cursor: pointer;
    }

    .stock-chip button:focus-visible {
      outline: 2px solid #fff;
      outline-offset: 2px;
    }

    .stock-add-status {
      min-height: 14px;
      color: var(--dim);
      font: 800 10px/14px "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .matrix-manage-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      min-height: 26px;
    }

    .custom-stock-summary {
      color: var(--dim);
      font: 800 10px/14px "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .custom-stock-manage-button {
      flex: 0 0 auto;
      min-height: 36px;
      cursor: pointer;
    }

    .custom-stock-manage-button:focus-visible {
      outline: 2px solid #fff;
      outline-offset: 2px;
    }

    .custom-stock-manage-button:active,
    .stock-chip button:active {
      transform: translateY(1px);
    }

    @media (hover: hover) {
      .custom-stock-manage-button:hover,
      .stock-chip button:hover,
      .stock-input-clear:hover {
        color: #fff;
        border-color: #fff;
      }
    }

    .restore-hidden-button {
      border: 1px solid rgba(54, 255, 196, 0.45);
      background: rgba(54, 255, 196, 0.08);
      color: var(--teal);
      min-height: 28px;
      padding: 0 9px;
      font: 900 10px/1 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .restore-hidden-button[hidden],
    .stock-add-status[hidden] {
      display: none;
    }

    .nav {
      position: fixed;
      left: 0;
      right: 0;
      bottom: 18px;
      bottom: max(18px, env(safe-area-inset-bottom));
      z-index: 10;
      height: 66px;
      padding: 0 8px;
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      background: rgba(6, 14, 28, 0.98);
      border-top: 1px solid var(--line);
      border-bottom: 1px solid rgba(69, 71, 76, 0.5);
      backdrop-filter: blur(14px);
    }

    .nav button {
      border: 0;
      background: transparent;
      color: var(--muted);
      font: 800 10px/1.2 "JetBrains Mono", "SFMono-Regular", monospace;
      letter-spacing: 0;
      display: grid;
      place-items: center;
      align-content: center;
      gap: 4px;
      padding-top: 5px;
      position: relative;
    }

    .nav button:before {
      content: "";
      width: 28px;
      height: 2px;
      background: transparent;
      position: absolute;
      top: 0;
    }

    .nav button.active { color: var(--teal); }
    .nav button.active:before { background: var(--teal); }
    .nav-icon { font-size: 23px; line-height: 1; }
    .nav-alert-dot {
      position: absolute;
      top: 13px;
      right: calc(50% - 18px);
      width: 8px;
      height: 8px;
      border-radius: 99px;
      background: #ffb3ae;
    }

    @media (max-width: 519px) {
      main { padding: 12px; }
      .topbar { padding-left: 12px; padding-right: 12px; }
      .brand { font-size: 12px; }
      .live-pill { padding: 6px 7px; font-size: 9px; }
      .hero { min-height: 350px; }
      .hero-top { grid-template-columns: minmax(0, 1fr); }
      .price { text-align: left; font-size: 22px; }
      .change { font-size: 11px; }
      .quote-facts { max-width: 280px; }
      .hero-word { font-size: 42px; line-height: 1; overflow-wrap: anywhere; }
      .spark { font-size: 34px; }
      .metric-card { min-height: 0; }
      .metric-card .metric-row { margin-top: 14px; }
      .sector-map-grid { aspect-ratio: 1 / 1.08; min-height: 300px; }
      .source-row, .alert-top { align-items: flex-start; }
      .source-row { flex-wrap: wrap; }
      .alert-card { padding: 13px; }
    }

    @media (max-width: 349px) {
      .macro-strip { grid-template-columns: minmax(0, 1fr); }
      .summary { grid-template-columns: minmax(0, 1fr); }
      .summary > div { border-right: 0; }
      .summary > div:nth-last-child(-n+2) { border-bottom: 1px solid var(--line); }
      .summary > div:last-child { border-bottom: 0; }
      .falling-prices { grid-template-columns: minmax(0, 1fr); }
    }

    @media (min-width: 520px) {
      .grid-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .news-action-metrics { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .news-action-metric:nth-child(2) { border-right: 1px solid rgba(69, 71, 76, 0.68); }
      .news-action-metric:last-child {
        grid-column: auto;
        border-top: 0;
      }
    }

    @media (min-width: 620px) {
      .trade-levels { grid-template-columns: repeat(5, minmax(0, 1fr)); }
      .trade-level,
      .trade-level:nth-child(2n) {
        border-right: 1px solid rgba(69, 71, 76, 0.72);
        border-bottom: 0;
      }
      .trade-level:last-child {
        grid-column: auto;
        border-right: 0;
      }
    }

    @media (min-width: 700px) {
      .home-grid { display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 12px; }
      .hero, .gauge { min-height: 360px; }
      .summary { grid-template-columns: repeat(4, minmax(0, 1fr)); }
      .summary > div { border-bottom: 0; }
      .summary > div:nth-child(even) { border-right: 1px solid var(--line); }
      .summary > div:last-child { border-right: 0; }
    }
  </style>
</head>
<body>
  <div class="collecting-overlay" id="collectingOverlay" role="status" aria-live="polite" aria-hidden="true">
    <div class="collecting-panel">
      <div class="collecting-grid" aria-hidden="true"></div>
      <p class="collecting-title" id="collectingTitle">COLLECTING MARKET INTELLIGENCE</p>
      <p class="collecting-step" id="collectingStep">Quotes, technicals, and fresh market context are being synchronized.</p>
      <div class="collecting-bars" aria-hidden="true"><span></span><span></span><span></span></div>
    </div>
  </div>
  <div class="app" id="appShell">
    <header class="topbar">
      <div class="brand"><span class="terminal-mark">&gt;_</span><span>CONFLUENCE_TERMINAL</span></div>
      <div class="live-pill"><span class="dot"></span><span id="keyState">SYNCING</span></div>
    </header>

    <main>
      <section class="view active" data-view="home">
        <div class="stack">
          <div class="home-grid stack">
            <article class="panel panel-pad hero">
              <div class="scanline"></div>
              <div class="hero-top">
                <div>
                  <p class="section-label">Master Index</p>
                  <h1 class="headline">Nifty 50 Core<br>Indicator</h1>
                </div>
                <div class="price">
                  <span class="price-value" id="niftyLtp">--</span>
                  <span class="change" id="niftyChange">SYNCING LIVE DATA</span>
                  <div class="quote-facts">
                    <div class="quote-fact"><span>Previous close</span><strong id="niftyPreviousClose">--</strong></div>
                    <div class="quote-fact"><span>Day move</span><strong id="niftySessionMove">--</strong></div>
                  </div>
                </div>
              </div>
              <div>
                <div class="hero-word"><span id="niftyTrend">SYNC</span> <span class="spark">/\/</span></div>
                <div class="bar" style="--value:0%" id="niftyBar"><span></span></div>
                <p class="body-copy" id="niftySummary">Syncing live confluence data from Yahoo Finance inside this app.</p>
              </div>
            </article>

            <article class="panel panel-pad gauge">
              <div style="width:100%">
                <p class="section-label" style="text-align:left">Macro Bias</p>
                <div class="gauge-box"><div class="gauge-value"><span id="macroBiasValue" style="display:inline;color:#fff;font-size:42px;letter-spacing:0">--</span><span id="macroBiasLabel">SYNC</span></div></div>
                <div class="grid-2" style="border-top:1px solid var(--line); padding-top:14px">
                  <div><p class="section-label">Volatility</p><div class="metric-main">LOW</div></div>
                  <div><p class="section-label">Regime</p><div class="metric-main">TRENDING</div></div>
                </div>
              </div>
            </article>
          </div>

          <div class="macro-strip">
            <article class="macro-card">
              <p class="section-label">USD/INR</p>
              <div class="metric-row"><span class="metric-main" id="usdInrValue">--</span><span class="metric-side" id="usdInrDelta">--</span></div>
              <p class="section-label" id="usdInrSource" style="margin-top:14px">Waiting</p>
            </article>
            <article class="macro-card">
              <p class="section-label">Crude LTP</p>
              <div class="metric-row"><span class="metric-main" id="crudeValue">--</span><span class="metric-side" id="crudeDelta">--</span></div>
              <p class="section-label" id="crudeSource" style="margin-top:14px">Waiting</p>
            </article>
            <article class="macro-card vix-card">
              <div class="vix-head"><p class="section-label">India VIX</p><span class="tiny-chip vix-regime" id="vixRegime">WAITING</span></div>
              <div class="metric-row"><span class="metric-main" id="vixValue">--</span><span class="metric-side" id="vixDelta">--</span></div>
              <div class="vix-scale" aria-hidden="true"><span class="vix-scale-marker" id="vixMarker" hidden></span></div>
              <p class="vix-context" id="vixContext">Waiting for the NSE volatility index.</p>
              <p class="section-label" id="vixSource" style="margin-top:10px">Waiting</p>
            </article>
          </div>

          <section class="sector-flow-panel" aria-labelledby="sectorFlowTitle">
            <header class="sector-flow-head">
              <div>
                <p class="section-label">Watchlist Market Rotation</p>
                <h2 class="sector-flow-title" id="sectorFlowTitle">SECTORS IN FOCUS</h2>
              </div>
              <span class="tiny-chip sector-flow-session" id="sectorFlowSession">WAITING</span>
            </header>
            <p class="sector-flow-summary" id="sectorFlowSummary" role="status" aria-live="polite">Waiting for price and session-volume coverage.</p>
            <div class="sector-flow-kpis" aria-label="Sector flow summary">
              <div class="sector-flow-kpi"><span>Estimated inflow</span><strong class="teal" id="sectorFlowIn">--</strong></div>
              <div class="sector-flow-kpi"><span>Estimated outflow</span><strong class="red" id="sectorFlowOut">--</strong></div>
              <div class="sector-flow-kpi"><span>Net direction</span><strong id="sectorFlowNet">--</strong></div>
              <div class="sector-flow-kpi"><span>Breadth</span><strong id="sectorFlowBreadth">--</strong></div>
            </div>
            <section class="flow-visual-section" aria-labelledby="sectorMapTitle">
              <div class="flow-section-head">
                <h3 class="flow-section-title" id="sectorMapTitle">Sector map</h3>
                <span class="flow-section-note">Size = turnover · Colour = weighted move</span>
              </div>
              <div class="sector-map-wrap">
                <div class="sector-map-grid" id="sectorMapGrid" role="list" aria-label="Sector turnover map">
                  <div class="sector-flow-empty">Sector map will appear after a complete quote batch.</div>
                </div>
              </div>
            </section>
            <div class="flow-detail-head"><span>Sector detail</span><span>Tap stock → Lens</span></div>
            <div class="sector-flow-list" id="sectorFlowList" role="list">
              <div class="sector-flow-empty">Live sector rotation appears after a successful quote batch supplies session volume.</div>
            </div>
            <div class="sector-flow-footnote"><span id="sectorFlowCoverage">FLOW COVERAGE --</span><span id="sectorFlowFreshness">UPDATED --</span></div>
            <p class="sector-flow-method">Estimated directional turnover = current price × session volume, assigned by price direction across the classified watchlist. This is not exchange order-flow, FII/DII flow, or a buy/sell recommendation.</p>
          </section>

          <div class="grid-3 grid-md-3">
            <article class="metric-card">
              <p class="section-label">Momentum Velocity</p>
              <div class="metric-row"><span class="metric-main" id="niftyVelocityCard">--</span><span class="metric-side" id="niftyAfCard">AF --</span></div>
              <div class="bar" style="--value:84%; margin-top:18px"><span></span></div>
            </article>
            <article class="metric-card">
              <p class="section-label">Awesome Osc</p>
              <div class="metric-row"><span class="metric-main" id="niftyAcCard">--</span><span class="metric-side" id="niftyTrendCard">--</span></div>
              <div class="bar" style="--value:74%; margin-top:18px"><span></span></div>
            </article>
            <article class="metric-card">
              <p class="section-label">Parabolic SAR</p>
              <div class="metric-row"><span class="metric-main" id="niftyPsarCard">--</span><span class="metric-side" id="niftyPsarPoint">P: --</span></div>
              <p class="section-label" style="margin-top:16px">Trend from PSAR point position</p>
            </article>
          </div>

          <section class="summary grid-2">
            <div><p class="section-label">Total Articles</p><div class="summary-value"><span id="kpiNews">--</span> <span class="tiny-chip">LIVE</span></div></div>
            <div><p class="section-label">Alpha Alerts</p><div class="summary-value"><span id="kpiAlerts">--</span> <span class="tiny-chip red">CRITICAL</span></div></div>
            <div><p class="section-label">Bullish Breadth</p><div class="summary-value teal"><span id="kpiBullish">--</span></div></div>
            <div><p class="section-label">Bearish Breadth</p><div class="summary-value red"><span id="kpiBearish">--</span></div></div>
          </section>

          <footer class="status-line"><span><span class="dot" style="display:inline-block;vertical-align:-1px;margin-right:8px"></span>ENGINE STATUS: <span class="teal" id="engineStatus">LOCKED</span></span><span id="lastSync">--:--:--</span></footer>
        </div>
      </section>

      <section class="view" data-view="matrix">
        <div class="stack">
          <div>
            <p class="section-label">Confluence Matrix</p>
            <h2 class="headline">ALGORITHM_MATRIX</h2>
            <p class="body-copy">RSI below 70 is ranked first, then live Parabolic SAR acceleration. F&O stocks are amber.</p>
          </div>
          <div class="filter-row" aria-label="Matrix filter">
            <button class="active" data-matrix-filter="all" type="button" onclick="setMatrixFilter('all')">ALL</button><button data-matrix-filter="bullish" type="button" onclick="setMatrixFilter('bullish')">BULLISH</button><button data-matrix-filter="bearish" type="button" onclick="setMatrixFilter('bearish')">BEARISH</button><button data-matrix-filter="watchlist" type="button" onclick="setMatrixFilter('watchlist')">WATCHLIST</button>
          </div>
          <section class="add-stock-panel" aria-label="Add stock to matrix">
            <form class="add-stock-form" id="addStockForm" novalidate>
              <div class="stock-input-wrap">
                <label class="visually-hidden" for="stockInput">NSE ticker symbol</label>
                <input class="stock-input" id="stockInput" name="stock" type="text" autocomplete="off" autocapitalize="characters" spellcheck="false" placeholder="ADD NSE TICKER">
                <button class="stock-input-clear" id="stockInputClear" type="button" aria-label="Clear NSE ticker" onclick="clearStockInput()" hidden>×</button>
              </div>
              <button class="add-stock-button" id="stockSearchButton" type="submit">Search</button>
            </form>
            <div class="matrix-manage-row">
              <span class="custom-stock-summary" id="customStockSummary">No custom stocks added</span>
              <button class="restore-hidden-button custom-stock-manage-button" id="customStockManageButton" type="button" aria-expanded="false" aria-controls="customStockChips" onclick="toggleCustomStockList()" hidden>Manage</button>
            </div>
            <div class="custom-stock-chips" id="customStockChips" aria-label="Custom stocks" hidden></div>
            <div class="stock-add-status" id="stockAddStatus" role="status" aria-live="polite">Enter symbol like ABB or ABB.NS</div>
            <div class="matrix-manage-row">
              <span class="stock-add-status" id="hiddenStockStatus" hidden></span>
              <button class="restore-hidden-button" id="restoreHiddenStocks" type="button" onclick="restoreHiddenMatrixStocks()" hidden>Restore</button>
            </div>
          </section>
          <div class="table-card">
            <div class="data-status-row" role="status" aria-live="polite">
              <span id="matrixCoverageStatus">TECHNICAL COVERAGE --</span>
              <span id="closeHistoryStatus">CLOSE HISTORY --</span>
            </div>
            <div class="table-scroll">
              <table>
                <thead><tr><th>Ticker</th><th class="right">CMP</th><th class="right">RSI</th><th class="right">AF</th><th>Trend</th><th>Signal</th><th class="right">Score</th><th class="right matrix-action-head">Del</th></tr></thead>
                <tbody id="matrixRows"></tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      <section class="view" data-view="detail">
        <div class="stack">
          <article class="panel panel-pad detail-hero">
            <div class="detail-actions">
              <p class="section-label" id="detailSource">Stock Lens</p>
              <button class="mini-action" id="detailRefresh" type="button" onclick="selectedSymbol && openStockDetail(selectedSymbol)">Refresh</button>
            </div>
            <div>
              <h2 class="detail-symbol" id="detailSymbol">SELECT</h2>
              <p class="body-copy" id="detailSubtitle">Tap any stock in Matrix to load news, 52-week range, and revenue history.</p>
            </div>
          </article>

          <section class="detail-stats">
            <div><p class="section-label">LTP</p><div class="summary-value" id="detailLtp">--</div></div>
            <div><p class="section-label">AF</p><div class="summary-value teal" id="detailAf">--</div></div>
            <div><p class="section-label">52W High</p><div class="summary-value" id="detailHigh">--</div><p class="section-label" id="detailHighDate" style="margin-top:8px">--</p></div>
            <div><p class="section-label">52W Low</p><div class="summary-value" id="detailLow">--</div><p class="section-label" id="detailLowDate" style="margin-top:8px">--</p></div>
          </section>

          <section class="detail-block">
            <div class="source-row"><span id="revenueTitle">Revenue Chart</span><span>Yahoo Finance</span></div>
            <div class="revenue-chart" id="revenueChart">
              <div class="body-copy">Select a stock to load revenue history.</div>
            </div>
          </section>

          <section class="detail-block">
            <div class="source-row"><span>News Search</span><span>Google News</span></div>
            <div class="detail-news" id="detailNews">
              <div class="body-copy">Select a stock to search recent articles.</div>
            </div>
          </section>
        </div>
      </section>

      <section class="view" data-view="intel">
        <div class="stack">
          <div class="intel-head">
            <div>
              <p class="section-label">System Feed</p>
              <h2 class="headline">LIVE_INTELLIGENCE</h2>
            </div>
            <div class="intel-actions">
              <button class="mini-action" id="webDiscoveryButton" type="button" onclick="scanWebForWatchlist(true)">Scan Web</button>
              <button class="mini-action" id="intelRefresh" type="button" onclick="refreshIntelFromMatrix(latestMatrixRows, true)">Refresh</button>
            </div>
          </div>
          <div>
            <p class="body-copy">Matrix-ranked stock news, summarized from live web sources.</p>
            <p class="section-label" id="intelStatus" style="margin-top:10px">Waiting for Matrix scan</p>
          </div>
          <section class="discovery-panel" aria-label="Web-discovered watchlist candidates">
            <div class="source-row"><span>WEB DISCOVERY</span><span id="webDiscoveryStatus">READY</span></div>
            <div class="discovery-list" id="webDiscoveryList">
              <p class="body-copy">Fresh NSE companies found in market headlines will appear here.</p>
            </div>
          </section>
          <div class="stack" id="intelList"></div>
        </div>
      </section>

      <section class="view" data-view="alerts">
        <div class="stack">
          <div>
            <div class="source-row"><span>SYSTEM_PRIORITY</span><span></span></div>
            <h2 class="headline" style="margin-top:8px">ACTIVE_ALERTS_STREAM</h2>
            <p class="body-copy">News-impact strategy, local close ledger, confluence alerts, and sentiment monitoring.</p>
          </div>
          <div class="filter-row" aria-label="Alert channel filter">
            <button class="active" type="button" data-alert-filter="all" onclick="setAlertFilter('all')">ALL</button><button type="button" data-alert-filter="news" onclick="setAlertFilter('news')">NEWS</button><button type="button" data-alert-filter="technical" onclick="setAlertFilter('technical')">TECHNICAL</button><button type="button" data-alert-filter="close" onclick="setAlertFilter('close')">CLOSE</button>
          </div>
          <div class="event-grid" id="eventsList"></div>
          <div class="stack" id="alertsList"></div>
        </div>
      </section>
    </main>

    <nav class="nav" aria-label="Primary">
      <button class="active" type="button" data-tab="home" onclick="openView('home')"><span class="nav-icon">⌂</span><span>Home</span></button>
      <button type="button" data-tab="matrix" onclick="openView('matrix')"><span class="nav-icon">▦</span><span>Matrix</span></button>
      <button type="button" data-tab="detail" onclick="openView('detail')"><span class="nav-icon">⌕</span><span>Lens</span></button>
      <button type="button" data-tab="intel" onclick="openView('intel')"><span class="nav-icon">⌁</span><span>Intel</span></button>
      <button type="button" data-tab="alerts" onclick="openView('alerts')"><span class="nav-icon">⌐</span><span>Alerts</span><span class="nav-alert-dot"></span></button>
    </nav>
  </div>

  <script>
    const CUSTOM_STOCKS_KEY = "stockUnifiedCustomStocks";
    const HIDDEN_STOCKS_KEY = "stockUnifiedHiddenStocks";
    const DAILY_CLOSES_KEY = "stockUnifiedDailyClosesV1";
    const LAST_SUCCESSFUL_SNAPSHOT_KEY = "stockUnifiedLastSuccessfulSnapshotV1";
    const SNAPSHOT_VERSION = 1;
    const MARKET_OPEN_REFRESH_MS = 30000;
    const MARKET_CLOSED_REFRESH_MS = 300000;
    const SYNC_RETRY_MS = 60000;
    const CLOSE_HISTORY_LIMIT = 45;
    const FALLING_STREAK_MIN = 2;
    const FO_SYMBOLS = new Set(("360ONE,ABB,ABCAPITAL,ADANIENSOL,ADANIENT,ADANIGREEN,ADANIPORTS,ADANIPOWER,ALKEM,AMBER,AMBUJACEM,ANGELONE,APLAPOLLO,APOLLOHOSP,ASHOKLEY,ASIANPAINT,ASTRAL,ATHERENERG,AUBANK,AUROPHARMA,AXISBANK,BAJAJ-AUTO,BAJAJFINSV,BAJAJHLDNG,BAJFINANCE,BANDHANBNK,BANKBARODA,BANKINDIA,BDL,BEL,BHARATFORG,BHARTIARTL,BHEL,BIOCON,BLUESTARCO,BOSCHLTD,BPCL,BRITANNIA,BSE,CAMS,CANBK,CDSL,CGPOWER,CHOLAFIN,CIPLA,COALINDIA,COCHINSHIP,COFORGE,COLPAL,CONCOR,CROMPTON,CUMMINSIND,DABUR,DELHIVERY,DIVISLAB,DIXON,DLF,DMART,DRREDDY,EICHERMOT,ETERNAL,FEDERALBNK,FORCEMOT,FORTIS,GAIL,GLENMARK,GMRAIRPORT,GODFRYPHLP,GODREJCP,GODREJPROP,GRASIM,GVT&D,HAL,HAVELLS,HCLTECH,HDFCAMC,HDFCBANK,HDFCLIFE,HEROMOTOCO,HINDALCO,HINDPETRO,HINDUNILVR,HINDZINC,HYUNDAI,ICICIBANK,ICICIGI,ICICIPRULI,IDEA,IDFCFIRSTB,IEX,INDHOTEL,INDIANB,INDIGO,INDUSINDBK,INDUSTOWER,INFY,INOXWIND,IOC,IREDA,IRFC,ITC,JINDALSTEL,JIOFIN,JSWENERGY,JSWSTEEL,JUBLFOOD,KALYANKJIL,KAYNES,KEI,KFINTECH,KOTAKBANK,KPITTECH,LAURUSLABS,LICHSGFIN,LICI,LODHA,LT,LTF,LTIM,LTM,LUPIN,M&M,MAHABANK,MANAPPURAM,MANKIND,MARICO,MARUTI,MAXHEALTH,MAZDOCK,MCX,MFSL,MOTHERSON,MOTILALOFS,MPHASIS,MUTHOOTFIN,NAM-INDIA,NATIONALUM,NAUKRI,NBCC,NESTLEIND,NHPC,NMDC,NTPC,NYKAA,OBEROIRLTY,OFSS,OIL,ONGC,PAGEIND,PATANJALI,PAYTM,PERSISTENT,PETRONET,PFC,PGEL,PHOENIXLTD,PIDILITIND,PIIND,PNB,PNBHOUSING,POLICYBZR,POLYCAB,POWERGRID,POWERINDIA,PREMIERENE,PRESTIGE,RADICO,RBLBANK,RECLTD,RELIANCE,RVNL,SAGILITY,SAIL,SBICARD,SBILIFE,SBIN,SHREECEM,SHRIRAMFIN,SIEMENS,SOLARINDS,SONACOMS,SRF,SUNPHARMA,SUPREMEIND,SUZLON,SWIGGY,TATACONSUM,TATAELXSI,TATAPOWER,TATASTEEL,TCS,TECHM,TIINDIA,TITAN,TMPV,TORNTPHARM,TRENT,TVSMOTOR,ULTRACEMCO,UNIONBANK,UNITDSPR,UNOMINDA,UPL,VBL,VEDL,VMM,VOLTAS,WAAREEENER,WIPRO,YESBANK,ZYDUSLIFE").split(","));
    const SECTOR_SYMBOL_GROUPS = {
      "BANKS": "HDFCBANK,INDUSINDBK,KOTAKBANK,PNB,SBIN,YESBANK",
      "FINANCIALS": "ANGELONE,BAJAJHFL,BSE,CAMS,CDSL,HDFCLIFE,ICICIGI,ICICIPRULI,IFCI,IREDA,LICI,MANAPPURAM,MCX,NIVABUPA,PAYTM,POLICYBZR,SAMMAANCAP,SBILIFE,STARHEALTH",
      "PHARMA": "CIPLA,DIVISLAB,DRREDDY,GLENMARK,GRANULES,LUPIN,SUNPHARMA",
      "IT & TELECOM": "AFFLE,BHARTIARTL,DLINKINDIA,HAPPSTMNDS,IDEA,INDIAMART,INDUSTOWER,INFY,NAUKRI,NELCO,TATACOMM,TCS,TECHM,TEJASNET,WIPRO",
      "AUTO & MOBILITY": "ARE&M,EICHERMOT,EXIDEIND,HEROMOTOCO,MARUTI,OLAELEC,TATAMOTORS,TVSMOTOR",
      "CONSUMER": "DMART,GODREJCP,HINDUNILVR,INDHOTEL,ITC,NYKAA,STOVEKRAFT,TATACONSUM,TITAN,TRENT,TRIDENT,ZOMATO",
      "ENERGY & POWER": "GENSOL,HINDPETRO,IEX,NTPC,POWERGRID,PREMIERENE,RELIANCE,RTNINDIA,SJVN,TATAPOWER,WAAREEENER",
      "METALS & MINING": "COALINDIA,GRAPHITE,HEG,HINDALCO,HINDZINC,JSWSTEEL,NMDC,SAIL,TATASTEEL,VEDL",
      "CHEMICALS": "BALAMINES,CLEAN,DEEPAKNTR,FACT,LXCHEM,PIDILITIND,RALLIS,SRF,TATACHEM,TATVA,UPL,YASHO",
      "DEFENCE": "BDL,BEL,GRSE,HAL,IDEAFORGE,MAZDOCK",
      "INDUSTRIALS & INFRA": "ACC,AZAD,GMRAIRPORT,GRASIM,HAVELLS,INDIGO,IRCTC,KAYNES,LT,NBCC,NCC,POLYCAB,RVNL,TITAGARH,ULTRACEMCO",
      "MEDIA & OTHER": "BALRAMCHIN,ZEEL"
    };
    const SECTOR_BY_SYMBOL = new Map(
      Object.entries(SECTOR_SYMBOL_GROUPS).flatMap(([sector, symbols]) => (
        symbols.split(",").map((symbol) => [symbol, sector])
      ))
    );
    let refreshTimer = null;
    let lastSyncStartedAt = 0;
    let currentDashboard = null;
    let currentMacro = null;
    let currentMarketStatus = null;
    let lastSuccessfulSyncAt = 0;
    let selectedSymbol = null;
    let detailRequestSeq = 0;
    let historyRequestSeq = 0;
    let historySyncInFlight = false;
    const historyAttemptAt = new Map();
    const historySyncedSymbols = new Set();
    let customStocks = loadCustomStocks();
    let hiddenStocks = loadHiddenStocks();
    let intelRequestSeq = 0;
    let latestMatrixRows = [];
    let latestNewsActions = [];
    let latestIntelNews = [];
    let currentMatrixRows = [];
    let activeMatrixFilter = "all";
    let activeAlertFilter = "all";
    let hasCompletedFirstSync = false;
    let hasRunWebDiscovery = false;
    let discoveryInFlight = false;
    let liveSyncInFlight = false;
    let latestDiscoverySuggestions = [];
    let collectingSequence = 0;
    let nativeRequestSequence = 0;
    const collectingRequests = new Set();
    const nativePending = new Map();
    let customStockListExpanded = false;

    const matrixRows = document.getElementById("matrixRows");
    const intelList = document.getElementById("intelList");
    const alertsList = document.getElementById("alertsList");
    const eventsList = document.getElementById("eventsList");
    const tabs = document.querySelectorAll("[data-tab]");
    const views = document.querySelectorAll("[data-view]");
    const matrixFilterButtons = document.querySelectorAll("[data-matrix-filter]");
    const keyState = document.getElementById("keyState");
    const engineStatus = document.getElementById("engineStatus");
    const intelStatus = document.getElementById("intelStatus");
    const intelRefreshButton = document.getElementById("intelRefresh");
    const webDiscoveryButton = document.getElementById("webDiscoveryButton");
    const webDiscoveryStatus = document.getElementById("webDiscoveryStatus");
    const webDiscoveryList = document.getElementById("webDiscoveryList");
    const collectingOverlay = document.getElementById("collectingOverlay");
    const collectingTitle = document.getElementById("collectingTitle");
    const collectingStep = document.getElementById("collectingStep");
    const stockInput = document.getElementById("stockInput");
    const stockInputClear = document.getElementById("stockInputClear");
    const stockSearchButton = document.getElementById("stockSearchButton");
    const customStockChips = document.getElementById("customStockChips");
    const customStockSummary = document.getElementById("customStockSummary");
    const customStockManageButton = document.getElementById("customStockManageButton");
    const stockAddStatus = document.getElementById("stockAddStatus");
    const hiddenStockStatus = document.getElementById("hiddenStockStatus");
    const restoreHiddenStocks = document.getElementById("restoreHiddenStocks");

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }[char]));
    }

    const escapeAttr = escapeHtml;

    function safeExternalUrl(value) {
      try {
        const url = new URL(String(value || ""));
        return url.protocol === "https:" || url.protocol === "http:" ? url.href : "#";
      } catch {
        return "#";
      }
    }

    function showCollecting(title, detail) {
      const token = "collect-" + (++collectingSequence);
      collectingRequests.add(token);
      collectingTitle.textContent = title || "COLLECTING MARKET INTELLIGENCE";
      collectingStep.textContent = detail || "Quotes, technicals, and fresh market context are being synchronized.";
      collectingOverlay.classList.add("active");
      collectingOverlay.setAttribute("aria-hidden", "false");
      setTimeout(() => hideCollecting(token), 70000);
      return token;
    }

    function hideCollecting(token) {
      collectingRequests.delete(token);
      if (collectingRequests.size) return;
      collectingOverlay.classList.remove("active");
      collectingOverlay.setAttribute("aria-hidden", "true");
    }

    function loadCustomStocks() {
      try {
        const parsed = JSON.parse(localStorage.getItem(CUSTOM_STOCKS_KEY) || "[]");
        return Array.isArray(parsed) ? parsed.map(normalizeCustomSymbol).filter(Boolean) : [];
      } catch {
        return [];
      }
    }

    function saveCustomStocks() {
      localStorage.setItem(CUSTOM_STOCKS_KEY, JSON.stringify(customStocks));
    }

    function loadHiddenStocks() {
      try {
        const parsed = JSON.parse(localStorage.getItem(HIDDEN_STOCKS_KEY) || "[]");
        return Array.isArray(parsed) ? parsed.map(normalizeCustomSymbol).filter(Boolean) : [];
      } catch {
        return [];
      }
    }

    function saveHiddenStocks() {
      localStorage.setItem(HIDDEN_STOCKS_KEY, JSON.stringify(hiddenStocks));
    }

    function loadLastSuccessfulSnapshot() {
      try {
        const parsed = JSON.parse(localStorage.getItem(LAST_SUCCESSFUL_SNAPSHOT_KEY) || "null");
        if (!parsed || parsed.version !== SNAPSHOT_VERSION || !parsed.dashboard) return null;
        return parsed;
      } catch {
        return null;
      }
    }

    function saveLastSuccessfulSnapshot() {
      if (!currentDashboard) return;
      const snapshot = {
        version: SNAPSHOT_VERSION,
        savedAt: lastSuccessfulSyncAt || Date.now(),
        dashboard: currentDashboard,
        macro: currentMacro,
        marketStatus: currentMarketStatus,
        newsActions: latestNewsActions,
        intelNews: latestIntelNews
      };
      try {
        localStorage.setItem(LAST_SUCCESSFUL_SNAPSHOT_KEY, JSON.stringify(snapshot));
      } catch (error) {
        console.warn("Unable to save the latest market snapshot:", error);
      }
    }

    function restoreLastSuccessfulSnapshot() {
      const snapshot = loadLastSuccessfulSnapshot();
      if (!snapshot) return false;
      currentDashboard = snapshot.dashboard;
      currentMacro = snapshot.macro || null;
      currentMarketStatus = snapshot.marketStatus || null;
      latestNewsActions = Array.isArray(snapshot.newsActions) ? snapshot.newsActions : [];
      latestIntelNews = Array.isArray(snapshot.intelNews)
        ? snapshot.intelNews
        : (Array.isArray(currentDashboard.latest_news) ? currentDashboard.latest_news : []);
      currentDashboard.latest_news = latestIntelNews;
      lastSuccessfulSyncAt = Number(snapshot.savedAt) || 0;
      hasCompletedFirstSync = true;
      renderDashboard(currentDashboard, currentMarketStatus, {
        fromCache: true,
        savedAt: lastSuccessfulSyncAt
      });
      if (currentMacro) renderMacro(currentMacro);
      return true;
    }

    function normalizeCustomSymbol(value) {
      return String(value || "")
        .trim()
        .toUpperCase()
        .replace(/\.NS$/, "")
        .replace(/[^A-Z0-9&.-]/g, "");
    }

    function customStockListViewModel(stocks, expanded) {
      const count = Array.isArray(stocks) ? stocks.length : 0;
      const isExpanded = Boolean(count && expanded);
      return {
        count,
        isExpanded,
        summary: count
          ? count + " custom stock" + (count === 1 ? "" : "s") + " active"
          : "No custom stocks added",
        buttonLabel: isExpanded ? "Hide list" : "Manage",
        buttonAriaLabel: isExpanded
          ? "Hide custom stock list"
          : "Manage " + count + " custom stock" + (count === 1 ? "" : "s")
      };
    }

    function knownMatrixSymbols() {
      const rows = Array.isArray(currentMatrixRows) && currentMatrixRows.length
        ? currentMatrixRows
        : currentDashboard?.top_predictions;
      if (!Array.isArray(rows)) return new Set();
      return new Set(rows.map((item) => normalizeCustomSymbol(item.symbol)));
    }

    function renderCustomStockChips() {
      const viewModel = customStockListViewModel(customStocks, customStockListExpanded);
      customStockListExpanded = viewModel.isExpanded;
      customStockSummary.textContent = viewModel.summary;
      customStockManageButton.hidden = viewModel.count === 0;
      customStockManageButton.textContent = viewModel.buttonLabel;
      customStockManageButton.setAttribute("aria-expanded", String(viewModel.isExpanded));
      customStockManageButton.setAttribute("aria-label", viewModel.buttonAriaLabel);
      customStockChips.hidden = !viewModel.isExpanded;
      customStockChips.replaceChildren();
      if (!viewModel.isExpanded) return;

      customStocks.forEach((symbol) => {
        const chip = document.createElement("span");
        chip.className = "stock-chip";
        chip.append(document.createTextNode(symbol));
        const removeButton = document.createElement("button");
        removeButton.type = "button";
        removeButton.textContent = "×";
        removeButton.dataset.removeStock = symbol;
        removeButton.setAttribute("aria-label", "Remove " + symbol);
        removeButton.addEventListener("click", () => {
          const removalIndex = customStocks.indexOf(symbol);
          removeCustomStock(symbol, removalIndex);
        });
        chip.append(removeButton);
        customStockChips.append(chip);
      });
    }

    function toggleCustomStockList() {
      customStockListExpanded = !customStockListExpanded;
      renderCustomStockChips();
    }

    function collapseCustomStockList() {
      customStockListExpanded = false;
      renderCustomStockChips();
    }

    function updateStockInputClearButton() {
      stockInputClear.hidden = !stockInput.value;
    }

    function clearStockInput() {
      stockInput.value = "";
      updateStockInputClearButton();
      stockInput.focus();
    }

    function addDiscoveryToWatchlist(value, refresh = true) {
      const symbol = normalizeCustomSymbol(value);
      if (!symbol) return false;
      hiddenStocks = hiddenStocks.filter((item) => item !== symbol);
      saveHiddenStocks();
      renderHiddenStockControl();
      if (customStocks.includes(symbol)) {
        return false;
      }
      customStocks = [...customStocks, symbol];
      saveCustomStocks();
      collapseCustomStockList();
      renderDiscoverySuggestions(latestDiscoverySuggestions);
      stockAddStatus.textContent = symbol + " added to Watchlist from web discovery.";
      if (refresh) {
        refreshLiveData().catch((error) => console.error("Watchlist refresh error:", error));
      }
      return true;
    }

    function renderDiscoverySuggestions(suggestions) {
      latestDiscoverySuggestions = Array.isArray(suggestions) ? suggestions : [];
      if (!latestDiscoverySuggestions.length) {
        webDiscoveryList.innerHTML = '<p class="body-copy">No reliable new NSE symbol match was found in the latest scan.</p>';
        return;
      }

      webDiscoveryList.innerHTML = latestDiscoverySuggestions.map((item) => {
        const symbol = normalizeCustomSymbol(item.symbol);
        const added = customStocks.includes(symbol);
        const confidence = Number(item.confidence);
        const confidenceText = Number.isFinite(confidence) ? Math.round(confidence) + "% MATCH" : "NSE MATCH";
        const sourceLink = item.url
          ? '<a class="news-source-link" href="' + escapeAttr(safeExternalUrl(item.url)) + '">SOURCE</a>'
          : '<span>' + escapeHtml(item.source || "WEB") + '</span>';
        return '<div class="discovery-row"><div><div class="source-row"><span><span class="discovery-symbol">'
          + escapeHtml(symbol) + '</span> · ' + escapeHtml(item.company || "NSE Equity") + '</span><span>' + escapeHtml(confidenceText) + '</span></div>'
          + '<p class="discovery-headline">' + escapeHtml(item.headline || item.reason || "Fresh market headline") + '</p>'
          + '<div class="source-row" style="margin-top:7px"><span>' + escapeHtml(item.source || "Google News") + '</span>' + sourceLink + '</div></div>'
          + '<button class="mini-action" type="button" ' + (added ? 'disabled' : 'onclick="addDiscoveryToWatchlist(\'' + escapeAttr(symbol) + '\', true)"') + '>'
          + (added ? "Added" : "Add") + '</button></div>';
      }).join("");
    }

    function scanWebForWatchlist(autoAdd = true) {
      if (discoveryInFlight) return;
      discoveryInFlight = true;
      const collectingToken = showCollecting(
        "SCANNING NEWS FOR NEW STOCKS",
        "Fresh Indian market headlines are being matched to verified NSE equity symbols."
      );
      webDiscoveryStatus.textContent = "SCANNING";
      if (webDiscoveryButton) {
        webDiscoveryButton.disabled = true;
        webDiscoveryButton.textContent = "Scanning";
      }

      setTimeout(async () => {
        let addedCount = 0;
        try {
          const payload = await callNativeAsync("discoverNewsStocksJson");
          const suggestions = Array.isArray(payload.suggestions) ? payload.suggestions : [];
          renderDiscoverySuggestions(suggestions);
          if (autoAdd) {
            suggestions
              .filter((item) => Number(item.confidence || 0) >= 75)
              .slice(0, 3)
              .forEach((item) => {
                if (addDiscoveryToWatchlist(item.symbol, false)) addedCount += 1;
              });
          }
          renderDiscoverySuggestions(suggestions);
          webDiscoveryStatus.textContent = addedCount
            ? addedCount + " ADDED TO WATCHLIST"
            : suggestions.length + " CANDIDATES";
          if (addedCount) {
            refreshLiveData().catch((error) => console.error("Discovery refresh error:", error));
          }
        } catch (error) {
          webDiscoveryStatus.textContent = "UNAVAILABLE";
          webDiscoveryList.innerHTML = '<p class="body-copy">' + escapeHtml(error.message || "Web discovery is unavailable right now.") + '</p>';
        } finally {
          discoveryInFlight = false;
          hideCollecting(collectingToken);
          if (webDiscoveryButton) {
            webDiscoveryButton.disabled = false;
            webDiscoveryButton.textContent = "Scan Web";
          }
        }
      }, 80);
    }

    function renderHiddenStockControl() {
      const count = hiddenStocks.length;
      if (!hiddenStockStatus || !restoreHiddenStocks) return;
      hiddenStockStatus.hidden = count === 0;
      restoreHiddenStocks.hidden = count === 0;
      hiddenStockStatus.textContent = count
        ? count + " script" + (count === 1 ? "" : "s") + " hidden from Matrix"
        : "";
    }

    function isHiddenMatrixRow(item) {
      return hiddenStocks.includes(normalizeCustomSymbol(item?.symbol));
    }

    function activeMatrixRows() {
      return currentMatrixRows.filter((item) => !isHiddenMatrixRow(item));
    }

    function baseWatchlistSymbolSet() {
      const explicitBaseSymbols = Array.isArray(currentDashboard?.base_watchlist_symbols)
        ? currentDashboard.base_watchlist_symbols
        : [];
      if (explicitBaseSymbols.length) {
        return new Set(explicitBaseSymbols.map(normalizeCustomSymbol).filter(Boolean));
      }

      const dashboardCustomSymbols = new Set(
        (Array.isArray(currentDashboard?.custom_symbols) ? currentDashboard.custom_symbols : [])
          .map(normalizeCustomSymbol)
          .filter(Boolean)
      );
      const dashboardSymbols = Array.isArray(currentDashboard?.watchlist_symbols)
        ? currentDashboard.watchlist_symbols
        : [];
      return new Set(
        dashboardSymbols
          .map(normalizeCustomSymbol)
          .filter((symbol) => symbol && !dashboardCustomSymbols.has(symbol))
      );
    }

    function closeWatchlistRows() {
      const rowsBySymbol = new Map();
      const symbols = [];
      const seen = new Set();
      const rememberSymbol = (value) => {
        const symbol = normalizeCustomSymbol(value);
        if (!symbol || seen.has(symbol) || hiddenStocks.includes(symbol)) return;
        seen.add(symbol);
        symbols.push(symbol);
      };
      const rememberRow = (row) => {
        const symbol = normalizeCustomSymbol(row?.symbol);
        if (!symbol || hiddenStocks.includes(symbol)) return;
        rememberSymbol(symbol);
        rowsBySymbol.set(symbol, Object.assign({}, rowsBySymbol.get(symbol) || {}, row, {symbol}));
      };

      const dashboardSymbols = Array.isArray(currentDashboard?.watchlist_symbols)
        ? currentDashboard.watchlist_symbols
        : [];
      const baseSymbols = [...baseWatchlistSymbolSet()];
      const activeSymbols = new Set(
        baseSymbols.concat(customStocks).map(normalizeCustomSymbol).filter(Boolean)
      );
      const quoteRows = Array.isArray(currentDashboard?.watchlist_quotes)
        ? currentDashboard.watchlist_quotes
        : [];
      const activeDashboardSymbols = activeSymbols.size ? [...activeSymbols] : dashboardSymbols;
      activeDashboardSymbols.forEach(rememberSymbol);
      quoteRows.forEach((row) => {
        if (!activeSymbols.size || activeSymbols.has(normalizeCustomSymbol(row?.symbol))) rememberRow(row);
      });
      currentMatrixRows.forEach((row) => {
        if (!activeSymbols.size || activeSymbols.has(normalizeCustomSymbol(row?.symbol))) rememberRow(row);
      });
      customStocks.forEach(rememberSymbol);

      return symbols.map((symbol) => rowsBySymbol.get(symbol) || {symbol});
    }

    function sectorForSymbol(value) {
      return SECTOR_BY_SYMBOL.get(normalizeCustomSymbol(value)) || "";
    }

    function buildSectorFlow(rows, options = {}) {
      const input = Array.isArray(rows) ? rows : [];
      const sectors = new Map();
      const now = Number(options.now || Date.now());
      const sessionDate = (value) => new Intl.DateTimeFormat("en-CA", {
        timeZone: "Asia/Kolkata",
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
      }).format(new Date(value));
      const currentSessionDate = sessionDate(now);
      let classifiedCount = 0;
      let flowCount = 0;
      let staleFlowCount = 0;
      let advancers = 0;
      let decliners = 0;
      let unchanged = 0;
      let latestQuoteAt = 0;

      input.forEach((row) => {
        const symbol = normalizeCustomSymbol(row?.symbol);
        const sector = String(row?.sector || sectorForSymbol(symbol)).trim();
        const price = numberOrNull(row?.ltp);
        const changePercent = numberOrNull(row?.change_percent);
        if (!symbol || !sector || price === null || price <= 0 || changePercent === null) return;
        classifiedCount += 1;
        if (changePercent > 0.05) advancers += 1;
        else if (changePercent < -0.05) decliners += 1;
        else unchanged += 1;

        const quoteAt = Number(row?.quote_epoch || 0) > 0
          ? Number(row.quote_epoch) * 1000
          : new Date(row?.quote_timestamp || 0).getTime();

        const sessionVolume = numberOrNull(row?.session_volume ?? row?.volume);
        const suppliedTurnover = numberOrNull(row?.turnover_estimate);
        const turnover = suppliedTurnover !== null && suppliedTurnover > 0
          ? suppliedTurnover
          : (sessionVolume !== null && sessionVolume > 0 ? price * sessionVolume : null);
        if (turnover === null || turnover <= 0) return;
        if (!Number.isFinite(quoteAt) || quoteAt <= 0) {
          staleFlowCount += 1;
          return;
        }
        if (options.marketOpen && sessionDate(quoteAt) !== currentSessionDate) {
          staleFlowCount += 1;
          return;
        }
        flowCount += 1;
        latestQuoteAt = Math.max(latestQuoteAt, quoteAt);

        const direction = changePercent > 0.05 ? 1 : (changePercent < -0.05 ? -1 : 0);
        const entry = sectors.get(sector) || {
          sector,
          inflow: 0,
          outflow: 0,
          net: 0,
          advancers: 0,
          decliners: 0,
          unchanged: 0,
          stockCount: 0,
          grossTurnover: 0,
          weightedChangeTotal: 0,
          weightedChange: 0,
          inflowLeader: null,
          outflowLeader: null,
          leader: null
        };
        if (direction > 0) {
          entry.inflow += turnover;
          entry.advancers += 1;
          if (!entry.inflowLeader || turnover > entry.inflowLeader.turnover) {
            entry.inflowLeader = {symbol, changePercent, turnover};
          }
        } else if (direction < 0) {
          entry.outflow += turnover;
          entry.decliners += 1;
          if (!entry.outflowLeader || turnover > entry.outflowLeader.turnover) {
            entry.outflowLeader = {symbol, changePercent, turnover};
          }
        } else {
          entry.unchanged += 1;
        }
        entry.net = entry.inflow - entry.outflow;
        entry.stockCount += 1;
        entry.grossTurnover += turnover;
        entry.weightedChangeTotal += changePercent * turnover;
        entry.weightedChange = entry.grossTurnover > 0
          ? entry.weightedChangeTotal / entry.grossTurnover
          : 0;
        sectors.set(sector, entry);
      });

      const allSectors = [...sectors.values()];
      allSectors.forEach((item) => {
        item.leader = item.net < 0 ? item.outflowLeader : item.inflowLeader;
      });
      const inflowSectors = allSectors.filter((item) => item.net > 0).sort((a, b) => b.net - a.net);
      const outflowSectors = allSectors.filter((item) => item.net < 0).sort((a, b) => a.net - b.net);
      const focus = [...inflowSectors.slice(0, 3), ...outflowSectors.slice(0, 3)];
      if (focus.length < 6) {
        allSectors
          .filter((item) => !focus.includes(item))
          .sort((a, b) => Math.abs(b.net) - Math.abs(a.net))
          .slice(0, 6 - focus.length)
          .forEach((item) => focus.push(item));
      }
      const inflow = allSectors.reduce((sum, item) => sum + item.inflow, 0);
      const outflow = allSectors.reduce((sum, item) => sum + item.outflow, 0);

      return {
        sectors: focus,
        allSectors: allSectors.slice().sort((a, b) => b.grossTurnover - a.grossTurnover),
        inflowSectors,
        outflowSectors,
        inflow,
        outflow,
        net: inflow - outflow,
        advancers,
        decliners,
        unchanged,
        totalCount: input.length,
        classifiedCount,
        flowCount,
        staleFlowCount,
        latestQuoteAt
      };
    }

    function formatSectorFlowCrores(value, showSign = false) {
      const numeric = numberOrNull(value);
      if (numeric === null) return "--";
      const crores = Math.abs(numeric) / 10000000;
      const digits = crores >= 100 ? 0 : (crores >= 10 ? 1 : 2);
      const amount = new Intl.NumberFormat("en-IN", {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits
      }).format(crores);
      const sign = numeric < 0 ? "−" : (showSign && numeric > 0 ? "+" : "");
      return sign + "₹" + amount + " cr";
    }

    function buildSectorTreemap(items, width = 100, height = 100) {
      const source = (Array.isArray(items) ? items : [])
        .filter((item) => Number(item?.grossTurnover) > 0)
        .slice()
        .sort((a, b) => Number(b.grossTurnover) - Number(a.grossTurnover));
      const output = [];
      const totalOf = (rows) => rows.reduce((sum, item) => sum + Number(item.grossTurnover || 0), 0);
      const split = (rows, x, y, w, h) => {
        if (!rows.length || w <= 0 || h <= 0) return;
        if (rows.length === 1) {
          output.push({item: rows[0], x, y, width: w, height: h});
          return;
        }
        const total = totalOf(rows);
        let running = 0;
        let splitIndex = 1;
        let bestDistance = Number.POSITIVE_INFINITY;
        for (let index = 1; index < rows.length; index += 1) {
          running += Number(rows[index - 1].grossTurnover || 0);
          const distance = Math.abs(total / 2 - running);
          if (distance < bestDistance) {
            bestDistance = distance;
            splitIndex = index;
          }
        }
        const leading = rows.slice(0, splitIndex);
        const trailing = rows.slice(splitIndex);
        const ratio = total > 0 ? totalOf(leading) / total : 0.5;
        if (w >= h) {
          const leadingWidth = w * ratio;
          split(leading, x, y, leadingWidth, h);
          split(trailing, x + leadingWidth, y, w - leadingWidth, h);
        } else {
          const leadingHeight = h * ratio;
          split(leading, x, y, w, leadingHeight);
          split(trailing, x, y + leadingHeight, w, h - leadingHeight);
        }
      };
      split(source, 0, 0, Number(width) || 100, Number(height) || 100);
      return output;
    }

    function renderSectorMap(result) {
      const grid = document.getElementById("sectorMapGrid");
      if (!grid) return;
      grid.replaceChildren();
      const sectors = Array.isArray(result?.allSectors) ? result.allSectors : [];
      if (!result?.flowCount || !sectors.length) {
        const empty = document.createElement("div");
        empty.className = "sector-flow-empty";
        empty.textContent = "Sector map will appear when turnover and price-change coverage are available.";
        grid.append(empty);
        return;
      }
      buildSectorTreemap(sectors).forEach((rect) => {
        const item = rect.item;
        const tile = document.createElement("div");
        const compact = rect.width < 23 || rect.height < 20;
        tile.className = "sector-map-tile" + (compact ? " compact" : "");
        tile.setAttribute("role", "listitem");
        tile.style.left = rect.x + "%";
        tile.style.top = rect.y + "%";
        tile.style.width = rect.width + "%";
        tile.style.height = rect.height + "%";
        const move = Number(item.weightedChange || 0);
        const intensity = 0.14 + Math.min(1, Math.abs(move) / 4) * 0.5;
        tile.style.background = move > 0.05
          ? "rgba(0, 184, 126, " + intensity + ")"
          : move < -0.05
            ? "rgba(231, 59, 62, " + intensity + ")"
            : "rgba(125, 116, 255, 0.18)";
        const name = document.createElement("strong");
        name.textContent = item.sector;
        const change = document.createElement("span");
        change.textContent = fmtDelta(move);
        const detail = document.createElement("small");
        detail.textContent = formatSectorFlowCrores(item.grossTurnover) + " · " + item.advancers + "↑ " + item.decliners + "↓";
        tile.setAttribute("aria-label", item.sector + ", weighted move " + fmtDelta(move)
          + ", turnover " + formatSectorFlowCrores(item.grossTurnover)
          + ", " + item.advancers + " advancing and " + item.decliners + " declining stocks");
        tile.append(name, change, detail);
        grid.append(tile);
      });
    }

    function renderSectorFlow(rows, marketStatus, options = {}) {
      const result = buildSectorFlow(rows, {
        marketOpen: Boolean(marketStatus?.is_open && !options.fromCache)
      });
      const session = document.getElementById("sectorFlowSession");
      const summary = document.getElementById("sectorFlowSummary");
      const list = document.getElementById("sectorFlowList");
      const inflowValue = document.getElementById("sectorFlowIn");
      const outflowValue = document.getElementById("sectorFlowOut");
      const netValue = document.getElementById("sectorFlowNet");
      const breadthValue = document.getElementById("sectorFlowBreadth");
      const coverage = document.getElementById("sectorFlowCoverage");
      const freshness = document.getElementById("sectorFlowFreshness");
      if (!session || !summary || !list) return result;

      session.textContent = options.fromCache
        ? "SAVED"
        : (marketStatus?.is_open ? (result.flowCount ? "OPEN TRADE" : "AWAITING LIVE") : "LAST SESSION");
      inflowValue.textContent = result.flowCount ? formatSectorFlowCrores(result.inflow) : "--";
      outflowValue.textContent = result.flowCount ? formatSectorFlowCrores(result.outflow) : "--";
      netValue.textContent = result.flowCount ? formatSectorFlowCrores(result.net, true) : "--";
      netValue.className = result.net < 0 ? "red" : (result.net > 0 ? "teal" : "");
      breadthValue.textContent = result.classifiedCount
        ? result.advancers + " : " + result.decliners + (result.unchanged ? " · " + result.unchanged + " FLAT" : "")
        : "--";
      coverage.textContent = "FLOW COVERAGE " + result.flowCount + "/" + result.totalCount;
      freshness.textContent = result.latestQuoteAt ? "UPDATED " + relativeAge(result.latestQuoteAt) : "UPDATED --";
      renderSectorMap(result);

      list.replaceChildren();
      if (!result.flowCount || !result.sectors.length) {
        summary.textContent = result.staleFlowCount && marketStatus?.is_open
          ? "Waiting for current-session volume; older flow estimates are excluded while the market is open."
          : result.classifiedCount
            ? "Price breadth is available, but session-volume coverage is still insufficient for a sector-flow estimate."
          : "Waiting for classified watchlist quotes before calculating sector rotation.";
        const empty = document.createElement("div");
        empty.className = "sector-flow-empty";
        empty.textContent = "Sector flow will appear after the next successful quote batch supplies current price, change, and session volume.";
        list.append(empty);
        return result;
      }

      const arriving = result.inflowSectors.slice(0, 2).map((item) => item.sector);
      const leaving = result.outflowSectors.slice(0, 2).map((item) => item.sector);
      if (arriving.length && leaving.length) {
        summary.textContent = "Estimated rotation into " + arriving.join(" & ") + "; out of " + leaving.join(" & ") + ".";
      } else if (arriving.length) {
        summary.textContent = "Estimated buying pressure is broad, led by " + arriving.join(" & ") + ".";
      } else if (leaving.length) {
        summary.textContent = "Estimated selling pressure is broad, led by " + leaving.join(" & ") + ".";
      } else {
        summary.textContent = "Directional turnover is balanced across the classified watchlist.";
      }

      const maxAbsNet = Math.max(1, ...result.sectors.map((item) => Math.abs(item.net)));
      result.sectors.forEach((item) => {
        const row = document.createElement("article");
        row.className = "sector-flow-row";
        row.setAttribute("role", "listitem");

        const head = document.createElement("div");
        head.className = "sector-flow-row-head";
        const name = document.createElement("span");
        name.className = "sector-flow-name";
        name.textContent = item.sector;
        const value = document.createElement("span");
        value.className = "sector-flow-value " + (item.net < 0 ? "red" : (item.net > 0 ? "teal" : "muted"));
        value.textContent = formatSectorFlowCrores(item.net, true);
        head.append(name, value);

        const track = document.createElement("div");
        track.className = "sector-flow-track";
        track.setAttribute("aria-hidden", "true");
        const bar = document.createElement("span");
        bar.className = "sector-flow-bar " + (item.net < 0 ? "outflow" : "inflow");
        bar.style.setProperty("--flow-size", Math.max(2, Math.round((Math.abs(item.net) / maxAbsNet) * 50)) + "%");
        track.append(bar);

        const foot = document.createElement("div");
        foot.className = "sector-flow-row-foot";
        const meta = document.createElement("span");
        meta.className = "sector-flow-meta";
        const direction = item.net > 0 ? "INFLOW" : (item.net < 0 ? "OUTFLOW" : "BALANCED");
        meta.textContent = direction + " · " + item.advancers + " UP / " + item.decliners + " DOWN";
        foot.append(meta);
        if (item.leader?.symbol) {
          const leader = document.createElement("button");
          leader.className = "sector-flow-leader";
          leader.type = "button";
          leader.textContent = item.leader.symbol + " " + fmtDelta(item.leader.changePercent) + " → LENS";
          leader.setAttribute("aria-label", "Open " + item.leader.symbol + " stock details");
          leader.addEventListener("click", () => openStockDetail(item.leader.symbol));
          foot.append(leader);
        }

        row.append(head, track, foot);
        list.append(row);
      });
      return result;
    }

    function isLiveMatrixRow(row) {
      return Boolean(row && !row.mock && (row.quote_source || row.quote_timestamp || row.quote_time || row.change !== undefined));
    }

    function isFoStock(row) {
      const symbol = normalizeCustomSymbol(typeof row === "string" ? row : row?.symbol);
      return Boolean(symbol && ((row && typeof row === "object" && row.is_fo === true) || FO_SYMBOLS.has(symbol)));
    }

    function rsiValue(row) {
      return numberOrNull(row?.rsi ?? row?.rsi_index ?? row?.rsi14);
    }

    function hasRsiPriority(row) {
      const rsi = rsiValue(row);
      if (typeof row?.rsi_priority === "boolean") return row.rsi_priority;
      return rsi !== null && rsi < 70;
    }

    function compareMatrixRows(left, right) {
      const unavailableDiff = Number(Boolean(left?.technical_unavailable)) - Number(Boolean(right?.technical_unavailable));
      if (unavailableDiff !== 0) return unavailableDiff;
      const staleDiff = Number(Boolean(left?.technical_stale)) - Number(Boolean(right?.technical_stale));
      if (staleDiff !== 0) return staleDiff;
      const leftPriority = hasRsiPriority(left);
      const rightPriority = hasRsiPriority(right);
      if (leftPriority !== rightPriority) return rightPriority ? 1 : -1;

      const afDiff = Number(right.psar_af || 0) - Number(left.psar_af || 0);
      if (afDiff !== 0) return afDiff;
      return Number(right.confluence_score || 0) - Number(left.confluence_score || 0);
    }

    function relativeAge(value) {
      const timestamp = typeof value === "number" ? value : new Date(value || 0).getTime();
      if (!Number.isFinite(timestamp) || timestamp <= 0) return "TIME UNKNOWN";
      const seconds = Math.max(0, Math.round((Date.now() - timestamp) / 1000));
      if (seconds < 10) return "JUST NOW";
      if (seconds < 60) return seconds + "S AGO";
      const minutes = Math.floor(seconds / 60);
      if (minutes < 60) return minutes + "M AGO";
      const hours = Math.floor(minutes / 60);
      if (hours < 24) return hours + "H AGO";
      return Math.floor(hours / 24) + "D AGO";
    }

    function mergeTechnicalRows(predictions, data, options = {}) {
      const incoming = Array.isArray(predictions) ? predictions : [];
      const activeSymbols = (Array.isArray(data?.watchlist_symbols) ? data.watchlist_symbols : [])
        .map(normalizeCustomSymbol)
        .filter(Boolean);
      const previousBySymbol = new Map(
        currentMatrixRows.map((row) => [normalizeCustomSymbol(row?.symbol), row])
      );
      const quoteBySymbol = new Map(
        (Array.isArray(data?.watchlist_quotes) ? data.watchlist_quotes : [])
          .map((row) => [normalizeCustomSymbol(row?.symbol), row])
          .filter(([symbol]) => Boolean(symbol))
      );
      const rows = [];
      const included = new Set();
      const updatedAt = data?.technical_updated_at || new Date().toISOString();
      const mergeQuoteTuple = (base, quote) => {
        const previous = base && typeof base === "object" ? base : {};
        const incomingQuote = quote && typeof quote === "object" ? quote : {};
        const merged = Object.assign({}, previous, incomingQuote);
        const hasQuoteResponse = Object.keys(incomingQuote).some((key) => key !== "symbol");
        const incomingVolume = Number(incomingQuote.session_volume);
        const hasSessionVolume = Number.isFinite(incomingVolume) && incomingVolume > 0;
        if (hasQuoteResponse && !hasSessionVolume) {
          delete merged.session_volume;
          delete merged.turnover_estimate;
        }
        return merged;
      };

      incoming.forEach((row) => {
        const symbol = normalizeCustomSymbol(row?.symbol);
        if (!symbol || included.has(symbol)) return;
        const quote = quoteBySymbol.get(symbol) || {};
        rows.push(Object.assign(mergeQuoteTuple(row, quote), {
          symbol,
          technical_stale: Boolean(options.fromCache),
          technical_unavailable: Boolean(row?.technical_unavailable),
          technical_updated_at: row.technical_updated_at || updatedAt
        }));
        included.add(symbol);
      });

      activeSymbols.forEach((symbol) => {
        if (included.has(symbol)) return;
        const previous = previousBySymbol.get(symbol);
        const quote = quoteBySymbol.get(symbol) || {};
        rows.push(Object.assign(mergeQuoteTuple(previous, quote), {
          symbol,
          technical_stale: true,
          technical_unavailable: !previous || Boolean(previous?.technical_unavailable),
          technical_updated_at: previous?.technical_updated_at || null
        }));
        included.add(symbol);
      });

      return {
        rows,
        freshCount: options.fromCache ? 0 : incoming.length,
        totalCount: activeSymbols.length || rows.length,
        retainedCount: Math.max(0, rows.length - (options.fromCache ? 0 : incoming.length))
      };
    }

    function mergePartialAlerts(incoming, previous, completedSymbols = []) {
      const output = [];
      const seen = new Set();
      const completed = new Set((Array.isArray(completedSymbols) ? completedSymbols : []).map(normalizeCustomSymbol));
      const fresh = Array.isArray(incoming) ? incoming : [];
      const retained = (Array.isArray(previous) ? previous : []).filter((alert) => {
        const category = String(alert?.category || "technical").toLowerCase();
        if (category !== "technical") return true;
        const symbol = normalizeCustomSymbol(alert?.symbol || String(alert?.title || "").split(/\s+/)[0]);
        return !symbol || !completed.has(symbol);
      });
      [...fresh, ...retained].forEach((alert) => {
          const key = [alert?.category || "technical", alert?.symbol || "", alert?.title || "", alert?.event_id || ""].join("|");
          if (seen.has(key)) return;
          seen.add(key);
          output.push(alert);
        });
      return output;
    }

    function numberOrNull(value) {
      const number = Number(value);
      return Number.isFinite(number) ? number : null;
    }

    function roundClose(value) {
      return Math.round(Number(value) * 100) / 100;
    }

    function loadDailyCloseBook() {
      try {
        const parsed = JSON.parse(localStorage.getItem(DAILY_CLOSES_KEY) || "{}");
        if (!parsed || typeof parsed !== "object") throw new Error("Invalid close book");
        return {
          version: 1,
          stocks: parsed.stocks && typeof parsed.stocks === "object" ? parsed.stocks : {},
          history_synced_at: parsed.history_synced_at && typeof parsed.history_synced_at === "object"
            ? parsed.history_synced_at
            : {},
          updated_at: parsed.updated_at || null
        };
      } catch {
        return {version: 1, stocks: {}, history_synced_at: {}, updated_at: null};
      }
    }

    function saveDailyCloseBook(book) {
      try {
        localStorage.setItem(DAILY_CLOSES_KEY, JSON.stringify(book));
      } catch (error) {
        console.warn("Unable to save local daily close history:", error);
      }
    }

    function sourcePriority(source) {
      const text = String(source || "");
      if (text.includes("yahoo_adjusted_daily_close")) return 4;
      if (text.includes("post_close")) return 3;
      if (text.includes("quote_close")) return 2;
      if (text.includes("derived")) return 1;
      return 0;
    }

    function upsertDailyClose(book, symbol, record) {
      if (!symbol || !record || !record.date || !Number.isFinite(record.close)) return false;
      const list = Array.isArray(book.stocks[symbol]) ? book.stocks[symbol] : [];
      const nextRecord = Object.assign({}, record, {close: roundClose(record.close)});
      const index = list.findIndex((item) => item && item.date === nextRecord.date);
      let changed = false;

      if (index >= 0) {
        const current = list[index] || {};
        const closeChanged = Math.abs(Number(current.close || 0) - nextRecord.close) >= 0.005;
        const nextPriority = sourcePriority(nextRecord.source);
        const currentPriority = sourcePriority(current.source);
        const mayReplace = nextPriority > currentPriority || (nextPriority === currentPriority && closeChanged);
        if (mayReplace) {
          list[index] = Object.assign({}, current, nextRecord);
          changed = true;
        }
      } else {
        list.push(nextRecord);
        changed = true;
      }

      list.sort((left, right) => String(left.date).localeCompare(String(right.date)));
      book.stocks[symbol] = list.slice(-CLOSE_HISTORY_LIMIT);
      return changed;
    }

    function getIstParts(value = new Date()) {
      const date = value instanceof Date ? value : new Date(value);
      if (Number.isNaN(date.getTime())) return null;

      try {
        const parts = new Intl.DateTimeFormat("en-CA", {
          timeZone: "Asia/Kolkata",
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hourCycle: "h23"
        }).formatToParts(date).reduce((acc, part) => {
          acc[part.type] = part.value;
          return acc;
        }, {});
        const hour = Number(parts.hour === "24" ? "0" : parts.hour);
        const minute = Number(parts.minute || 0);
        return {
          date: parts.year + "-" + parts.month + "-" + parts.day,
          minutes: hour * 60 + minute,
          time: String(parts.hour).padStart(2, "0") + ":" + String(parts.minute).padStart(2, "0") + ":" + String(parts.second || "00").padStart(2, "0")
        };
      } catch {
        const shifted = new Date(date.getTime() + 330 * 60 * 1000);
        const year = shifted.getUTCFullYear();
        const month = String(shifted.getUTCMonth() + 1).padStart(2, "0");
        const day = String(shifted.getUTCDate()).padStart(2, "0");
        const hour = shifted.getUTCHours();
        const minute = shifted.getUTCMinutes();
        const second = shifted.getUTCSeconds();
        return {
          date: year + "-" + month + "-" + day,
          minutes: hour * 60 + minute,
          time: String(hour).padStart(2, "0") + ":" + String(minute).padStart(2, "0") + ":" + String(second).padStart(2, "0")
        };
      }
    }

    function utcDateFromYmd(value) {
      const parts = String(value || "").split("-").map(Number);
      if (parts.length !== 3 || parts.some((item) => !Number.isFinite(item))) return null;
      return new Date(Date.UTC(parts[0], parts[1] - 1, parts[2]));
    }

    function ymdFromUtcDate(date) {
      return date.toISOString().slice(0, 10);
    }

    function isWeekday(value) {
      const date = utcDateFromYmd(value);
      if (!date) return false;
      const day = date.getUTCDay();
      return day >= 1 && day <= 5;
    }

    function previousTradingDate(value) {
      const date = utcDateFromYmd(value);
      if (!date) return null;
      do {
        date.setUTCDate(date.getUTCDate() - 1);
      } while (date.getUTCDay() === 0 || date.getUTCDay() === 6);
      return ymdFromUtcDate(date);
    }

    function rowQuoteDate(row) {
      const timestamp = row && row.quote_timestamp ? new Date(row.quote_timestamp) : null;
      if (!timestamp || Number.isNaN(timestamp.getTime())) return null;
      return getIstParts(timestamp);
    }

    function resolveCompletedCloseDate(row, marketStatus) {
      const quoteParts = rowQuoteDate(row);
      const nowParts = getIstParts(new Date());
      if (!quoteParts || !nowParts || !marketStatus || marketStatus.is_open !== false) return null;
      if (!isWeekday(quoteParts.date) || quoteParts.minutes < 15 * 60 + 30) return null;
      if (quoteParts.date > nowParts.date) return null;
      return quoteParts.date;
    }

    function inferPreviousClose(row) {
      const ltp = numberOrNull(row?.ltp);
      if (ltp === null || ltp <= 0) return null;

      const change = numberOrNull(row?.change);
      if (change !== null) {
        const previous = ltp - change;
        return previous > 0 ? roundClose(previous) : null;
      }

      const pct = numberOrNull(row?.change_percent ?? row?.changePercent);
      if (pct !== null && pct > -99.9) {
        const previous = ltp / (1 + pct / 100);
        return previous > 0 ? roundClose(previous) : null;
      }
      return null;
    }

    function persistMatrixDailyCloses(rows, marketStatus) {
      const matrixRows = Array.isArray(rows)
        ? rows.filter((item) => !isHiddenMatrixRow(item) && isLiveMatrixRow(item))
        : [];
      if (!matrixRows.length) return;

      const book = loadDailyCloseBook();
      const capturedAt = new Date().toISOString();
      let changed = false;

      matrixRows.forEach((row) => {
        const symbol = normalizeCustomSymbol(row?.symbol);
        if (!symbol) return;

        const ltp = numberOrNull(row?.ltp);
        const closeDate = resolveCompletedCloseDate(row, marketStatus);
        if (closeDate && ltp !== null && ltp > 0) {
          changed = upsertDailyClose(book, symbol, {
            date: closeDate,
            close: ltp,
            source: "post_close_quote",
            captured_at: capturedAt,
            quote_timestamp: row.quote_timestamp || "",
            quote_time: row.quote_time || ""
          }) || changed;
        }

      });

      if (changed) {
        book.updated_at = capturedAt;
        saveDailyCloseBook(book);
      }
    }

    function validCloseHistory(book, symbol) {
      const list = book && book.stocks ? book.stocks[symbol] : null;
      if (!Array.isArray(list)) return [];
      return list
        .map((item) => ({
          date: String(item.date || ""),
          close: numberOrNull(item.close),
          source: item.source || ""
        }))
        .filter((item) => item.date && item.close !== null && item.close > 0 && item.source !== "derived_previous_close")
        .sort((left, right) => left.date.localeCompare(right.date));
    }

    function consecutiveFallingMoves(history) {
      let streak = 0;
      for (let i = history.length - 1; i > 0; i -= 1) {
        const current = history[i];
        const previous = history[i - 1];
        const yahooSequence = String(current.source).includes("yahoo_adjusted_daily_close")
          && String(previous.source).includes("yahoo_adjusted_daily_close");
        // Yahoo's daily series already contains the exchange-session sequence,
        // including holiday gaps. Locally captured closes stay conservative.
        if (!yahooSequence && previousTradingDate(current.date) !== previous.date) break;
        if (Number(history[i].close) < Number(history[i - 1].close)) {
          streak += 1;
        } else {
          break;
        }
      }
      return streak;
    }

    function mergeRemoteDailyCloseHistory(payload) {
      const histories = Array.isArray(payload?.histories) ? payload.histories : [];
      if (!histories.length) return 0;
      const book = loadDailyCloseBook();
      let changed = false;
      let mergedSymbols = 0;
      histories.forEach((history) => {
        const symbol = normalizeCustomSymbol(history?.symbol);
        const closes = Array.isArray(history?.closes) ? history.closes : [];
        if (!symbol || !closes.length) return;
        closes.forEach((record) => {
          changed = upsertDailyClose(book, symbol, {
            date: String(record?.date || ""),
            close: Number(record?.close),
            source: "yahoo_adjusted_daily_close",
            captured_at: history.updated_at || payload.updated_at || new Date().toISOString()
          }) || changed;
        });
        book.history_synced_at[symbol] = history.updated_at || payload.updated_at || new Date().toISOString();
        historySyncedSymbols.add(symbol);
        mergedSymbols += 1;
      });
      if (changed) {
        book.updated_at = payload.updated_at || new Date().toISOString();
      }
      if (changed || mergedSymbols) {
        saveDailyCloseBook(book);
      }
      return mergedSymbols;
    }

    async function refreshDailyCloseHistory(rows) {
      if (historySyncInFlight) return;
      const now = Date.now();
      const symbols = [];
      const seen = new Set();
      const book = loadDailyCloseBook();
      (Array.isArray(rows) ? rows : []).forEach((row) => {
        const symbol = normalizeCustomSymbol(row?.symbol);
        const lastAttempt = Number(historyAttemptAt.get(symbol) || 0);
        const lastHistorySync = new Date(book.history_synced_at?.[symbol] || 0).getTime();
        const historyIsFresh = Number.isFinite(lastHistorySync) && lastHistorySync > 0
          && now - lastHistorySync < 6 * 60 * 60 * 1000;
        if (!symbol || seen.has(symbol) || historyIsFresh || historySyncedSymbols.has(symbol) || now - lastAttempt < 300000) return;
        seen.add(symbol);
        symbols.push(symbol);
        historyAttemptAt.set(symbol, now);
      });
      if (!symbols.length) return;

      historySyncInFlight = true;
      const requestId = ++historyRequestSeq;
      const historyStatus = document.getElementById("closeHistoryStatus");
      if (historyStatus) historyStatus.textContent = "RECOVERING " + symbols.length + " CLOSE HISTORIES";
      try {
        const payload = await callNativeAsync("getDailyCloseHistoryJsonForSymbols", JSON.stringify(symbols));
        if (requestId !== historyRequestSeq) return;
        mergeRemoteDailyCloseHistory(payload);
        const summary = buildFallingCloseSynthesis(closeWatchlistRows());
        if (historyStatus) {
          historyStatus.textContent = "CLOSE HISTORY " + summary.trackedCount + "/" + summary.watchlistCount;
        }
        renderAlerts(currentDashboard?.alerts || []);
      } catch (error) {
        if (requestId !== historyRequestSeq) return;
        if (historyStatus) historyStatus.textContent = "CLOSE HISTORY UPDATE DELAYED";
        console.error("Daily close history refresh error:", error);
      } finally {
        if (requestId === historyRequestSeq) historySyncInFlight = false;
      }
    }

    function liveClosePoint(row, history) {
      const price = numberOrNull(row?.ltp);
      if (price === null || price <= 0 || !history.length) return null;

      const quoteParts = rowQuoteDate(row);
      const liveDate = quoteParts?.date || getIstParts(new Date())?.date || "LIVE";
      const latestStored = history[history.length - 1];
      if (latestStored && latestStored.date === liveDate) return null;

      return {
        date: liveDate,
        close: roundClose(price),
        source: "live_current_price",
        live: true,
        quoteTime: row?.quote_time || quoteParts?.time || ""
      };
    }

    function buildFallingCloseSynthesis(rows) {
      const book = loadDailyCloseBook();
      const rowBySymbol = new Map();
      const watchlistSymbols = [];
      const seenSymbols = new Set();
      (Array.isArray(rows) ? rows : []).forEach((row) => {
        const symbol = normalizeCustomSymbol(row?.symbol);
        if (!symbol || hiddenStocks.includes(symbol)) return;
        if (!seenSymbols.has(symbol)) {
          seenSymbols.add(symbol);
          watchlistSymbols.push(symbol);
        }
        if (isLiveMatrixRow(row)) rowBySymbol.set(symbol, row);
      });

      const stocks = [];
      let trackedCount = 0;
      watchlistSymbols.forEach((symbol) => {
        const history = validCloseHistory(book, symbol);
        if (history.length > 0) trackedCount += 1;
        const livePoint = liveClosePoint(rowBySymbol.get(symbol), history);
        const comparisonHistory = livePoint ? history.concat(livePoint) : history;
        const streak = consecutiveFallingMoves(comparisonHistory);
        if (streak < FALLING_STREAK_MIN) return;

        const latest = comparisonHistory[comparisonHistory.length - 1];
        const latestStored = history[history.length - 1];
        const base = comparisonHistory[Math.max(0, comparisonHistory.length - streak - 1)];
        const drop = latest.close - base.close;
        const dropPercent = base.close > 0 ? (drop / base.close) * 100 : 0;
        stocks.push({
          symbol,
          streak,
          liveLeg: Boolean(latest.live),
          quoteTime: latest.quoteTime || "",
          latestDate: latest.date,
          startDate: base.date,
          latestClose: latestStored?.close || latest.close,
          latestCloseDate: latestStored?.date || latest.date,
          currentPrice: numberOrNull(rowBySymbol.get(symbol)?.ltp),
          currentDate: latest.live ? latest.date : null,
          drop,
          dropPercent,
          history: comparisonHistory.slice(Math.max(0, comparisonHistory.length - streak - 1))
        });
      });

      stocks.sort((left, right) => {
        if (right.streak !== left.streak) return right.streak - left.streak;
        return left.dropPercent - right.dropPercent;
      });

      return {
        stocks,
        watchlistCount: watchlistSymbols.length,
        trackedCount,
        updatedAt: book.updated_at || null
      };
    }

    function compactDate(value) {
      if (!value) return "--";
      const parts = String(value).split("-");
      if (parts.length !== 3) return value;
      return parts[2] + "/" + parts[1];
    }

    function signedMoney(value) {
      const number = Number(value || 0);
      return (number >= 0 ? "+" : "") + fmtNum(number, 2);
    }

    function renderCloseSynthesisCard(summary) {
      const falling = summary.stocks || [];
      const historyAge = summary.updatedAt ? "UPDATED " + relativeAge(summary.updatedAt) : "HISTORY BUILDING";
      if (falling.length) {
        const lead = falling[0];
        const body = falling.length + " watchlist stock" + (falling.length === 1 ? " is" : "s are")
          + " falling across stored closes plus live CMP. Worst current streak: "
          + lead.symbol + " at " + lead.streak + (lead.liveLeg ? " down moves including current price." : " down closes.");
        const rows = falling.map((item) => {
          const streakText = item.streak + (item.liveLeg ? " down moves" : " down closes");
          const currentPriceText = item.currentPrice !== null ? '₹' + fmtNum(item.currentPrice, 2) : "--";
          const closePriceText = item.latestClose ? '₹' + fmtNum(item.latestClose, 2) : "--";
          const liveBadge = item.liveLeg ? '<span class="badge yellow">LIVE CMP</span> ' : "";
          return '<button class="falling-row" type="button" data-close-symbol="' + escapeAttr(item.symbol)
            + '" aria-label="Open ' + escapeAttr(item.symbol) + ' stock details"><div class="falling-head"><div><div class="falling-symbol">' + escapeHtml(item.symbol)
            + '<span class="falling-open">OPEN LENS ↗</span>'
            + '</div><div class="falling-meta">' + liveBadge + streakText + ' | '
            + escapeHtml(compactDate(item.startDate)) + ' to ' + escapeHtml(compactDate(item.latestDate))
            + '</div></div><div class="falling-drop">'
            + item.dropPercent.toFixed(2) + '%<div class="falling-meta">' + signedMoney(item.drop) + '</div></div></div>'
            + '<div class="falling-prices"><div class="falling-price"><span>Current price</span><strong>'
            + currentPriceText + '</strong></div><div class="falling-price"><span>Last close · '
            + escapeHtml(compactDate(item.latestCloseDate)) + '</span><strong>' + closePriceText + '</strong></div></div></button>';
        }).join("");
        return '<article class="alert-card critical close-synthesis"><div class="alert-top"><span class="badge red">CLOSE TREND</span><span>' + escapeHtml(historyAge) + '</span></div><h3 class="alert-title">MULTI-DAY CLOSE WEAKNESS</h3><div class="alert-body"><div>'
          + escapeHtml(body) + '</div>' + rows + '</div><div class="source-row"><span>LOCAL CLOSE LEDGER + CMP</span><span>'
          + summary.trackedCount + '/' + summary.watchlistCount + ' WATCHLIST TRACKED</span></div></article>';
      }

      const status = summary.trackedCount
        ? "No watchlist stock is falling across stored closes plus current CMP right now."
        : (summary.watchlistCount ? "Local close history will begin after the app captures completed watchlist closes." : "Waiting for live watchlist rows before starting the local close ledger.");
      return '<article class="alert-card info close-synthesis"><div class="alert-top"><span class="badge gray">CLOSE TREND</span><span>' + escapeHtml(historyAge) + '</span></div><h3 class="alert-title">MULTI-DAY CLOSE WATCH</h3><div class="alert-body">'
        + escapeHtml(status) + '</div><div class="source-row"><span>LOCAL CLOSE LEDGER + CMP</span><span>'
        + summary.trackedCount + '/' + summary.watchlistCount + ' WATCHLIST TRACKED</span></div></article>';
    }

    function upsertMatrixRow(row) {
      if (!row || !row.symbol) return;
      const symbol = normalizeCustomSymbol(row.symbol);
      const nextRows = currentMatrixRows.filter((item) => normalizeCustomSymbol(item.symbol) !== symbol);
      nextRows.unshift(row);
      currentMatrixRows = nextRows;
      if (currentDashboard && Array.isArray(currentDashboard.top_predictions)) {
        currentDashboard.top_predictions = nextRows;
      }
      renderMatrix(currentMatrixRows);
      persistMatrixDailyCloses(currentMatrixRows, currentMarketStatus);
      if (currentDashboard) {
        renderAlerts(currentDashboard.alerts || []);
      }
      refreshIntelFromMatrix(currentMatrixRows, false);
    }

    function setStockSearchBusy(isBusy) {
      if (!stockSearchButton) return;
      stockSearchButton.disabled = isBusy;
      stockSearchButton.textContent = isBusy ? "Searching" : "Search";
    }

    function addCustomStock(value) {
      const symbol = normalizeCustomSymbol(value);
      if (!symbol) {
        stockAddStatus.textContent = "Enter a valid NSE symbol.";
        return;
      }

      setStockSearchBusy(true);
      const collectingToken = showCollecting(
        "SEARCHING NSE MARKET DATA",
        "Resolving " + symbol + " and calculating its latest technical state."
      );
      stockAddStatus.textContent = "Searching " + symbol + " on Yahoo Finance...";
      setTimeout(async () => {
        try {
          const result = await callNativeAsync("searchStockJson", symbol);
          const row = result.stock || {};
          if (!row.symbol) {
            throw new Error("No live quote found for " + symbol + ".");
          }

          hiddenStocks = hiddenStocks.filter((item) => item !== symbol);
          saveHiddenStocks();
          renderHiddenStockControl();

          if (!customStocks.includes(symbol)) {
            customStocks = [...customStocks, symbol];
            saveCustomStocks();
          }

          stockInput.value = "";
          updateStockInputClearButton();
          collapseCustomStockList();
          upsertMatrixRow(row);
          if (customStocks.includes(symbol)) {
            setMatrixFilter("watchlist");
          } else {
            setMatrixFilter("all");
          }
          stockAddStatus.textContent = symbol + " found. Matrix updated from Yahoo Finance.";
        } catch (error) {
          stockAddStatus.textContent = error.message || "Stock search failed. Try symbol like ABB or ABB.NS.";
        } finally {
          setStockSearchBusy(false);
          hideCollecting(collectingToken);
        }
      }, 80);
    }

    function removeCustomStock(symbol, preferredFocusIndex = -1) {
      const normalized = normalizeCustomSymbol(symbol);
      customStocks = customStocks.filter((item) => item !== normalized);
      saveCustomStocks();
      renderCustomStockChips();
      if (preferredFocusIndex >= 0) {
        const remainingRemoveButtons = customStockChips.querySelectorAll("[data-remove-stock]");
        const nextRemoveButton = remainingRemoveButtons[Math.min(preferredFocusIndex, remainingRemoveButtons.length - 1)];
        if (nextRemoveButton) nextRemoveButton.focus();
        else stockInput.focus();
      }
      const baseSymbols = baseWatchlistSymbolSet();
      if (!baseSymbols.has(normalized)) {
        currentMatrixRows = currentMatrixRows.filter((item) => normalizeCustomSymbol(item?.symbol) !== normalized);
        if (currentDashboard) {
          ["top_predictions", "watchlist_quotes"].forEach((key) => {
            if (Array.isArray(currentDashboard[key])) {
              currentDashboard[key] = currentDashboard[key].filter((item) => normalizeCustomSymbol(item?.symbol) !== normalized);
            }
          });
          if (Array.isArray(currentDashboard.watchlist_symbols)) {
            currentDashboard.watchlist_symbols = currentDashboard.watchlist_symbols
              .filter((item) => normalizeCustomSymbol(item) !== normalized);
          }
        }
      }
      if (currentDashboard && Array.isArray(currentDashboard.custom_symbols)) {
        currentDashboard.custom_symbols = currentDashboard.custom_symbols
          .filter((item) => normalizeCustomSymbol(item) !== normalized);
      }
      renderMatrix(currentMatrixRows);
      renderAlerts(currentDashboard?.alerts || []);
      stockAddStatus.textContent = normalized + " removed. Refreshing Matrix...";
      refreshLiveData();
    }

    function deleteMatrixStock(symbol) {
      const normalized = normalizeCustomSymbol(symbol);
      if (!normalized) return;
      if (!hiddenStocks.includes(normalized)) {
        hiddenStocks = [...hiddenStocks, normalized];
        saveHiddenStocks();
      }
      if (customStocks.includes(normalized)) {
        customStocks = customStocks.filter((item) => item !== normalized);
        saveCustomStocks();
        renderCustomStockChips();
      }
      renderHiddenStockControl();
      renderMatrix(currentMatrixRows);
      refreshIntelFromMatrix(activeMatrixRows(), false);
      stockAddStatus.textContent = normalized + " hidden from Matrix.";
    }

    function restoreHiddenMatrixStocks() {
      hiddenStocks = [];
      saveHiddenStocks();
      renderHiddenStockControl();
      renderMatrix(currentMatrixRows);
      refreshIntelFromMatrix(activeMatrixRows(), false);
      stockAddStatus.textContent = "All hidden scripts restored.";
    }

    function fmtNum(value, decimals = 2) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
      return Number(value).toLocaleString("en-IN", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
      });
    }

    function fmtDelta(value) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
      const number = Number(value);
      return (number >= 0 ? "+" : "") + number.toFixed(2) + "%";
    }

    function formatQuoteTime(value) {
      if (!value) return "--";
      const date = new Date(value);
      if (!Number.isNaN(date.getTime())) {
        return date.toLocaleTimeString("en-IN", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit"
        });
      }
      return String(value).slice(0, 8);
    }

    function formatNewsTime(value) {
      if (!value) return "LIVE";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) {
        return String(value).slice(0, 24);
      }
      return date.toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit"
      });
    }

    function badgeClass(value) {
      const text = String(value || "").toLowerCase();
      if (text.includes("bear") || text.includes("sell") || text.includes("negative")) return "red";
      if (text.includes("neutral")) return "gray";
      return "teal";
    }

    window.StockAsync = {
      resolve(requestId, raw) {
        const pending = nativePending.get(requestId);
        if (!pending) return;
        nativePending.delete(requestId);
        clearTimeout(pending.timer);
        try {
          const body = JSON.parse(raw || "{}");
          if (body.error) throw new Error(body.error);
          pending.resolve(body);
        } catch (error) {
          pending.reject(error);
        }
      }
    };

    function callNativeAsync(method, ...args) {
      if (!window.StockBridge || typeof window.StockBridge.requestJson !== "function") {
        return Promise.reject(new Error("Native market engine unavailable"));
      }
      const requestId = "native-" + (++nativeRequestSequence) + "-" + Date.now();
      const timeoutMs = method === "getDashboardJsonForSymbols"
        ? 70000
        : (method === "getDailyCloseHistoryJsonForSymbols"
          ? 70000
          : (method === "getStockDetailJson" ? 60000 : 45000));
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
          nativePending.delete(requestId);
          if (typeof window.StockBridge.cancelRequest === "function") {
            window.StockBridge.cancelRequest(requestId);
          }
          reject(new Error("Market data request timed out"));
        }, timeoutMs);
        nativePending.set(requestId, {resolve, reject, timer});
        try {
          window.StockBridge.requestJson(requestId, method, JSON.stringify(args));
        } catch (error) {
          clearTimeout(timer);
          nativePending.delete(requestId);
          reject(error);
        }
      });
    }

    async function apiFetch(path) {
      if (path === "/api/dashboard") {
        return callNativeAsync("getDashboardJsonForSymbols", JSON.stringify(customStocks));
      }

      const routes = {
        "/api/macro": "getMacroJson",
        "/api/market-status": "getMarketStatusJson"
      };
      const method = routes[path];
      if (!method) {
        throw new Error("Unsupported app data route: " + path);
      }
      return callNativeAsync(method);
    }

    function setStatus(text, isLive = false) {
      keyState.textContent = text;
      engineStatus.textContent = text;
      engineStatus.className = isLive ? "teal" : "red";
    }

    async function refreshLiveData() {
      if (liveSyncInFlight) return null;
      liveSyncInFlight = true;
      const requestedCustomStocksKey = JSON.stringify(customStocks);
      let watchlistChangedDuringSync = false;
      const collectingToken = !hasCompletedFirstSync
        ? showCollecting(
            "COLLECTING MARKET INTELLIGENCE",
            "Synchronizing live quotes, 5-minute index candles, RSI, and market context."
          )
        : null;
      if (collectingToken) {
        await new Promise((resolve) => setTimeout(resolve, 60));
      }
      setStatus(currentDashboard ? "SYNCING · SAVED DATA VISIBLE" : "SYNCING", true);
      try {
        const [dashboardResult, macroResult, marketResult] = await Promise.allSettled([
          apiFetch("/api/dashboard"),
          apiFetch("/api/macro"),
          apiFetch("/api/market-status")
        ]);

        if (marketResult.status === "fulfilled") {
          currentMarketStatus = marketResult.value;
        }

        const dashboardAccepted = dashboardResult.status === "fulfilled"
          && requestedCustomStocksKey === JSON.stringify(customStocks);
        watchlistChangedDuringSync = dashboardResult.status === "fulfilled" && !dashboardAccepted;

        if (dashboardAccepted) {
          lastSuccessfulSyncAt = Date.now();
          const previousDashboard = currentDashboard;
          currentDashboard = dashboardResult.value;
          renderDashboard(currentDashboard, currentMarketStatus, {previousDashboard});
        }

        if (macroResult.status === "fulfilled") {
          currentMacro = macroResult.value;
          renderMacro(currentMacro);
        }

        if (marketResult.status === "fulfilled") {
          if (dashboardAccepted) {
            keyState.textContent = currentMarketStatus.is_open ? "MARKET OPEN" : "MARKET CLOSED";
          }
          const hasLiveRows = dashboardAccepted
            && Array.isArray(dashboardResult.value?.top_predictions)
            && dashboardResult.value.top_predictions.length > 0;
          if (dashboardAccepted) {
            engineStatus.textContent = hasLiveRows ? "ONLINE" : "DATA UNAVAILABLE";
            engineStatus.className = hasLiveRows ? "teal" : "red";
          }
        }

        if (dashboardAccepted) {
          saveLastSuccessfulSnapshot();
          return true;
        }
        setStatus(currentDashboard ? "UPDATE DELAYED" : "OFFLINE", false);
        return false;
      } finally {
        liveSyncInFlight = false;
        hasCompletedFirstSync = true;
        if (collectingToken) hideCollecting(collectingToken);
        if (watchlistChangedDuringSync) {
          setTimeout(() => refreshLiveData().catch((error) => console.error("Watchlist refresh error:", error)), 0);
        }
      }
    }

    function renderDashboard(data, marketStatus = currentMarketStatus, options = {}) {
      const predictions = Array.isArray(data.top_predictions) ? data.top_predictions : [];
      const dashboardNews = Array.isArray(data.latest_news) ? data.latest_news : [];
      if (dashboardNews.length) latestIntelNews = dashboardNews;
      const news = latestIntelNews;
      const incomingAlerts = Array.isArray(data.alerts) ? data.alerts : [];
      const previousAlerts = Array.isArray(options.previousDashboard?.alerts)
        ? options.previousDashboard.alerts
        : [];
      const alerts = data.technical_complete === false
        ? mergePartialAlerts(incomingAlerts, previousAlerts, predictions.map((row) => row?.symbol))
        : incomingAlerts;
      const events = Array.isArray(data.upcoming_events) ? data.upcoming_events : [];
      const summary = data.market_summary || {};
      const nifty = data.nifty || {};
      const niftyAvailable = nifty.available !== false && Number(nifty.ltp) > 0;
      const quoteTimestamp = data.quote_timestamp || nifty.quote_timestamp || "";
      const quoteLabel = nifty.quote_time || data.quote_updated || formatQuoteTime(quoteTimestamp);

      document.getElementById("niftyLtp").textContent = niftyAvailable ? fmtNum(nifty.ltp, 2) : "--";
      document.getElementById("niftyTrend").textContent = niftyAvailable ? String(nifty.trend || "LIVE").toUpperCase() : "UNAVAILABLE";
      document.getElementById("niftyChange").textContent = "5M CANDLE - " + (niftyAvailable ? (quoteLabel || "--") : "NO VALID DATA");
      const niftyPreviousClose = niftyAvailable ? inferPreviousClose(nifty) : null;
      const niftyPointChange = numberOrNull(nifty.change);
      const niftyPercentChange = numberOrNull(nifty.change_percent);
      const niftyMoveClass = Number(niftyPointChange || 0) < 0 ? "red" : "teal";
      document.getElementById("niftyPreviousClose").textContent = niftyPreviousClose !== null
        ? fmtNum(niftyPreviousClose, 2)
        : "--";
      const niftySessionMove = document.getElementById("niftySessionMove");
      niftySessionMove.textContent = niftyPointChange !== null && niftyPercentChange !== null
        ? (niftyPointChange >= 0 ? "+" : "") + fmtNum(niftyPointChange, 2) + " / " + fmtDelta(niftyPercentChange)
        : "--";
      niftySessionMove.className = niftyMoveClass;
      const niftyTrend = niftyAvailable ? String(nifty.trend || "").toUpperCase() : "";
      const psarPosition = niftyTrend === "BULL" ? "below the latest candle" : "above or inside the latest candle";
      document.getElementById("niftySummary").textContent = niftyAvailable
        ? "NIFTY is " + niftyTrend + " because the latest 5-minute PSAR point is " + psarPosition + "."
        : "A valid 5-minute NIFTY candle series is unavailable. No shorter interval has been substituted.";
      document.getElementById("niftyBar").style.setProperty("--value", niftyAvailable
        ? Math.min(100, Math.max(8, Math.abs(Number(nifty.velocity || 0)) * 900 + 48)) + "%"
        : "0%");
      document.getElementById("niftyVelocityCard").textContent = fmtNum(nifty.velocity, 4);
      document.getElementById("niftyAfCard").textContent = "AF " + fmtNum(nifty.psar_af, 2);
      document.getElementById("niftyAcCard").textContent = fmtNum(nifty.ac, 4);
      document.getElementById("niftyTrendCard").textContent = niftyTrend || "--";
      document.getElementById("niftyPsarCard").textContent = niftyTrend === "BULL" ? "BELOW" : (niftyTrend === "BEAR" ? "ABOVE" : "--");
      document.getElementById("niftyPsarPoint").textContent = "P: " + fmtNum(nifty.psar_value, 2);

      const bullish = Number(summary.bullish || 0);
      const bearish = Number(summary.bearish || 0);
      const breadthTotal = bullish + bearish;
      const bullishPct = breadthTotal > 0 ? Math.round((bullish / breadthTotal) * 100) : null;
      document.getElementById("macroBiasValue").textContent = bullishPct === null ? "--" : bullishPct + "%";
      document.getElementById("macroBiasLabel").textContent = bullishPct === null
        ? "INSUFFICIENT DATA"
        : (bullishPct >= 55 ? "BULLISH" : bullishPct <= 45 ? "BEARISH" : "NEUTRAL");

      document.getElementById("kpiNews").textContent = news.length;
      document.getElementById("kpiAlerts").textContent = alerts.length;
      document.getElementById("kpiBullish").textContent = bullish || "--";
      document.getElementById("kpiBearish").textContent = bearish || "--";
      const quoteSyncAt = new Date(data.quote_timestamp || 0).getTime();
      const displayedSyncAt = Number(options.savedAt) || (Number.isFinite(quoteSyncAt) && quoteSyncAt > 0 ? quoteSyncAt : Date.now());
      document.getElementById("lastSync").textContent = (options.fromCache ? "SAVED " : "UPDATED ")
        + relativeAge(displayedSyncAt);
      stockAddStatus.textContent = customStocks.length ? "" : "Enter symbol like ABB or ABB.NS";

      const technicalCoverage = mergeTechnicalRows(predictions, data, options);
      const rowsForMatrix = technicalCoverage.rows;
      currentMatrixRows = rowsForMatrix;
      data.top_predictions = rowsForMatrix;
      data.alerts = alerts;
      data.latest_news = latestIntelNews;
      const matrixCoverageStatus = document.getElementById("matrixCoverageStatus");
      if (matrixCoverageStatus) {
        const retained = technicalCoverage.retainedCount
          ? " · " + technicalCoverage.retainedCount + " SAVED"
          : "";
        const technicalAge = data.technical_updated_at
          ? " · UPDATED " + relativeAge(data.technical_updated_at)
          : "";
        matrixCoverageStatus.textContent = "TECHNICAL " + technicalCoverage.freshCount + "/"
          + technicalCoverage.totalCount + " AVAILABLE" + technicalAge + retained;
      }
      renderMatrix(rowsForMatrix);
      const closeRows = closeWatchlistRows();
      renderSectorFlow(closeRows, marketStatus, options);
      if (closeRows.length) {
        persistMatrixDailyCloses(closeRows, marketStatus);
      }
      const closeSummary = buildFallingCloseSynthesis(closeRows);
      const closeHistoryStatus = document.getElementById("closeHistoryStatus");
      if (closeHistoryStatus) {
        closeHistoryStatus.textContent = "CLOSE HISTORY " + closeSummary.trackedCount + "/" + closeSummary.watchlistCount;
      }
      renderIntel(news, {stale: Boolean(options.fromCache), emptyState: "saved"});
      if (!options.fromCache) refreshIntelFromMatrix(activeMatrixRows(), false);
      renderEvents(events);
      renderAlerts(alerts);
      if (!options.fromCache && closeRows.length) {
        setTimeout(() => refreshDailyCloseHistory(closeRows), 650);
      }
      if (!options.fromCache && !hasRunWebDiscovery) {
        hasRunWebDiscovery = true;
        setTimeout(() => scanWebForWatchlist(true), 250);
      }
    }

    function mergeIntelItems(incoming, previous, completedSymbols, keyForItem) {
      const completed = new Set((Array.isArray(completedSymbols) ? completedSymbols : []).map(normalizeCustomSymbol));
      const output = [];
      const seen = new Set();
      const previousSymbols = new Set((Array.isArray(previous) ? previous : []).map((item) => normalizeCustomSymbol(item?.symbol)).filter(Boolean));
      const append = (item) => {
        const key = keyForItem(item);
        if (!key || seen.has(key)) return;
        seen.add(key);
        output.push(item);
      };
      (Array.isArray(incoming) ? incoming : []).forEach((item) => {
        const symbol = normalizeCustomSymbol(item?.symbol);
        if (!symbol || completed.has(symbol) || !previousSymbols.has(symbol)) append(item);
      });
      (Array.isArray(previous) ? previous : []).forEach((item) => {
        const symbol = normalizeCustomSymbol(item?.symbol);
        if (symbol && completed.has(symbol)) return;
        append(Object.assign({}, item, {stale: true}));
      });
      return output.slice(0, 20);
    }

    function refreshIntelFromMatrix(predictions, forceRefresh = false) {
      const rows = Array.isArray(predictions)
        ? predictions.filter((row) => !row?.technical_unavailable)
        : [];
      latestMatrixRows = rows;
      if (!rows.length) {
        renderIntel(latestIntelNews, {stale: true, emptyState: "waiting"});
        renderAlerts(currentDashboard?.alerts || []);
        intelStatus.textContent = "Waiting for Matrix scan";
        return;
      }

      const requestId = ++intelRequestSeq;
      const method = forceRefresh ? "refreshIntelJsonForRows" : "getIntelJsonForRows";
      const collectingToken = forceRefresh
        ? showCollecting(
            "ANALYZING NEWS CATALYSTS",
            "Fresh headlines are being scored against price action, RSI, and trend confirmation."
          )
        : null;
      intelStatus.textContent = "Searching news for " + Math.min(rows.length, 10) + " Matrix stocks...";
      document.getElementById("kpiNews").textContent = "--";
      if (intelRefreshButton) {
        intelRefreshButton.disabled = true;
        intelRefreshButton.textContent = "Syncing";
      }
      setTimeout(async () => {
        try {
          const payload = await callNativeAsync(method, JSON.stringify(rows));
          if (requestId !== intelRequestSeq) return;
          const latest = Array.isArray(payload.latest_news) ? payload.latest_news : [];
          const incomingActions = Array.isArray(payload.news_actions) ? payload.news_actions : [];
          const status = String(payload.news_status || "complete").toLowerCase();
          const completedSymbols = Array.isArray(payload.completed_symbols) ? payload.completed_symbols : [];
          if (status === "failed") {
            renderIntel(latestIntelNews, {stale: true, emptyState: "failed"});
            renderAlerts(currentDashboard?.alerts || []);
            document.getElementById("kpiNews").textContent = latestIntelNews.length;
            intelStatus.textContent = latestIntelNews.length
              ? "Update delayed · showing saved news"
              : "News sources unavailable";
            return;
          }

          if (status === "partial") {
            latestIntelNews = mergeIntelItems(
              latest,
              latestIntelNews,
              completedSymbols,
              (item) => String(item?.url || item?.title || "").toLowerCase()
            );
            latestNewsActions = mergeIntelItems(
              incomingActions,
              latestNewsActions,
              completedSymbols,
              (item) => normalizeCustomSymbol(item?.symbol)
            );
          } else {
            latestIntelNews = latest;
            latestNewsActions = incomingActions;
          }
          if (currentDashboard) currentDashboard.latest_news = latestIntelNews;
          renderIntel(latestIntelNews, {stale: false, emptyState: "complete"});
          renderMatrix(currentMatrixRows.length ? currentMatrixRows : rows);
          renderAlerts(currentDashboard?.alerts || []);
          document.getElementById("kpiNews").textContent = latestIntelNews.length;
          const updateTime = payload.updated_at ? new Date(payload.updated_at).toLocaleTimeString() : new Date().toLocaleTimeString();
          intelStatus.textContent = status === "partial"
            ? "Partial update " + updateTime + " | saved coverage retained"
            : "Updated " + updateTime + " | " + latestIntelNews.length + " articles";
          saveLastSuccessfulSnapshot();
        } catch (error) {
          if (requestId !== intelRequestSeq) return;
          renderIntel(latestIntelNews, {stale: true, emptyState: "failed"});
          document.getElementById("kpiNews").textContent = latestIntelNews.length;
          intelStatus.textContent = latestIntelNews.length
            ? "Update delayed · showing saved news"
            : "News search unavailable";
        } finally {
          if (collectingToken) hideCollecting(collectingToken);
          if (requestId === intelRequestSeq && intelRefreshButton) {
            intelRefreshButton.disabled = false;
            intelRefreshButton.textContent = "Refresh";
          }
        }
      }, 80);
    }

    function indiaVixRegime(value) {
      const numeric = numberOrNull(value);
      if (numeric === null || numeric <= 0) return {label: "UNAVAILABLE", tone: "muted"};
      if (numeric < 12) return {label: "CALM", tone: "teal"};
      if (numeric < 18) return {label: "NORMAL", tone: "teal"};
      if (numeric < 25) return {label: "ELEVATED", tone: "yellow"};
      return {label: "HIGH", tone: "red"};
    }

    function renderMacro(data) {
      const usd = data.usd_inr || {};
      const crude = data.crude || {};
      const vix = data.india_vix || {};
      document.getElementById("usdInrValue").textContent = usd.value ? fmtNum(usd.value, 4) : "--";
      document.getElementById("usdInrDelta").textContent = fmtDelta(usd.change_percent);
      document.getElementById("usdInrDelta").className = "metric-side " + (Number(usd.change_percent || 0) < 0 ? "red" : "teal");
      document.getElementById("usdInrSource").textContent = usd.quote_time ? "QUOTE " + usd.quote_time : (usd.symbol || usd.source || "LIVE");
      const crudePrefix = crude.currency === "USD" ? "$" : (crude.currency === "INR" ? "₹" : "");
      document.getElementById("crudeValue").textContent = crude.value ? crudePrefix + fmtNum(crude.value, 2) : "--";
      document.getElementById("crudeDelta").textContent = fmtDelta(crude.change_percent);
      document.getElementById("crudeDelta").className = "metric-side " + (Number(crude.change_percent || 0) < 0 ? "red" : "teal");
      document.getElementById("crudeSource").textContent = crude.quote_time
        ? "WTI 1M LIVE | " + crude.quote_time
        : (crude.symbol || crude.source || "LIVE");
      const vixValue = numberOrNull(vix.value);
      const vixRegime = indiaVixRegime(vixValue);
      const vixRegimeElement = document.getElementById("vixRegime");
      document.getElementById("vixValue").textContent = vixValue === null ? "--" : fmtNum(vixValue, 2);
      document.getElementById("vixDelta").textContent = fmtDelta(vix.change_percent);
      document.getElementById("vixDelta").className = "metric-side " + (Number(vix.change_percent || 0) < 0 ? "teal" : "red");
      vixRegimeElement.textContent = vixRegime.label;
      vixRegimeElement.className = "tiny-chip vix-regime " + vixRegime.tone;
      const vixPosition = vixValue === null ? 0 : Math.max(0, Math.min(100, ((vixValue - 8) / 32) * 100));
      const vixMarker = document.getElementById("vixMarker");
      vixMarker.hidden = vixValue === null;
      vixMarker.style.setProperty("--vix-position", vixPosition + "%");
      document.getElementById("vixContext").textContent = vixValue === null
        ? "India VIX is unavailable from the latest macro quote batch."
        : "Approximate one-day index move: ±" + fmtNum(vixValue / Math.sqrt(252), 2) + "% · " + vixRegime.label + " volatility regime.";
      document.getElementById("vixSource").textContent = vix.available === false
        ? "DATA UNAVAILABLE"
        : vix.quote_time
        ? "NSE INDIA VIX | " + vix.quote_time
        : (vix.symbol || vix.source || "WAITING");
    }

    function matrixTrend(item) {
      return String(item.psar_trend || item.prediction || "neutral").toLowerCase();
    }

    function matchesMatrixFilter(item) {
      if (isHiddenMatrixRow(item)) {
        return false;
      }
      const trend = matrixTrend(item);
      if (activeMatrixFilter === "bullish") {
        return trend.includes("bull");
      }
      if (activeMatrixFilter === "bearish") {
        return trend.includes("bear");
      }
      if (activeMatrixFilter === "watchlist") {
        return customStocks.includes(normalizeCustomSymbol(item.symbol));
      }
      return true;
    }

    function setMatrixFilter(filter) {
      activeMatrixFilter = filter || "all";
      matrixFilterButtons.forEach((button) => {
        button.classList.toggle("active", button.dataset.matrixFilter === activeMatrixFilter);
      });
      renderMatrix(currentMatrixRows);
    }

    function newsActionForSymbol(symbol) {
      const normalized = normalizeCustomSymbol(symbol);
      return latestNewsActions.find((item) => normalizeCustomSymbol(item?.symbol) === normalized) || null;
    }

    function renderMatrix(predictions) {
      const ranked = predictions.slice().sort(compareMatrixRows);
      const visibleRows = ranked.filter(matchesMatrixFilter);
      if (!visibleRows.length) {
        matrixRows.innerHTML = '<tr><td colspan="8" class="muted">No stocks match this Matrix filter.</td></tr>';
        return;
      }
      matrixRows.innerHTML = visibleRows.map((item) => {
        const symbol = String(item.symbol || "-");
        const normalizedSymbol = normalizeCustomSymbol(symbol);
        const isFo = isFoStock(item);
        const newsAction = newsActionForSymbol(symbol);
        const newsPriority = String(newsAction?.priority || "").toLowerCase();
        const changeValue = numberOrNull(item.change_percent ?? item.changePercent);
        const changeText = changeValue === null ? "--" : (changeValue >= 0 ? "+" : "") + changeValue.toFixed(2) + "%";
        const changeClass = changeValue !== null && changeValue < 0 ? "red" : "teal";
        const rsi = rsiValue(item);
        const rsiPriority = hasRsiPriority(item);
        const rsiText = rsi === null ? "--" : rsi.toFixed(1);
        const rsiClass = rsi === null ? "" : (rsiPriority ? "priority" : "hot");
        const rsiLabel = rsi === null ? "WAIT" : (rsiPriority ? "PRIO" : "70+");
        const afValue = Number(item.psar_af || 0);
        const afText = afValue ? afValue.toFixed(2) : "--";
        const afWidth = Math.min(48, Math.max(5, afValue * 240));
        const scoreValue = Number(item.confluence_score || 0);
        const scoreText = item.technical_unavailable
          ? "--"
          : (scoreValue >= 0 ? "+" : "") + scoreValue.toFixed(2);
        const direction = item.technical_unavailable ? "muted" : (scoreValue < 0 ? "red" : "teal");
        const trend = item.technical_unavailable
          ? "NO DATA"
          : String(item.psar_trend || item.prediction || "neutral").replaceAll("_", " ").toUpperCase();
        const tech = item.technical_unavailable
          ? "NO DATA"
          : String(item.signal_strength || "NEUTRAL").replaceAll("_", " ");
        const trendBadge = badgeClass(trend);
        const badge = badgeClass(trend + " " + tech);
        const foBadge = isFo ? '<span class="fo-badge">F&O</span>' : "";
        const newsBadge = newsAction
          ? '<span class="news-symbol-badge" title="' + escapeAttr((newsAction.action || "News action") + " | heuristic score " + (newsAction.setup_score || "--") + "/100") + '">NEWS</span>'
          : "";
        const qualityBadge = item.technical_unavailable
          ? '<span class="data-quality-badge">NO TECH</span>'
          : (item.technical_stale ? '<span class="data-quality-badge">SAVED TECH</span>' : "");
        const quoteFreshness = item.quote_timestamp
          ? "QUOTE " + relativeAge(item.quote_timestamp)
          : "QUOTE TIME UNKNOWN";
        const rowClass = "matrix-row"
          + (isFo ? " fo-row" : "")
          + (item.technical_stale ? " stale-technical" : "")
          + (newsPriority === "high" ? " news-priority" : (newsPriority === "medium" ? " news-watch" : ""));
        return '<tr class="' + rowClass + '" data-symbol="' + escapeAttr(normalizedSymbol || symbol) + '"><td><button class="row-open-button" type="button" data-open-symbol="' + escapeAttr(normalizedSymbol || symbol) + '" aria-label="Open ' + escapeAttr(symbol) + ' stock details"><span class="symbol-cell">' + escapeHtml(symbol) + foBadge + newsBadge + qualityBadge + '</span></button></td><td class="right"><span class="cmp-cell"><span class="cmp-value">' + fmtNum(item.ltp, 2) + '</span><span class="cmp-change ' + changeClass + '">' + changeText + '</span><span class="cmp-freshness">' + escapeHtml(quoteFreshness) + '</span></span></td><td class="right"><span class="rsi-stack"><span class="rsi-pill ' + rsiClass + '">' + rsiText + '</span><span class="rsi-label">' + rsiLabel + '</span></span></td><td class="right teal">' + afText + '<span class="score"><span style="--w:' + afWidth + '%"></span></span></td><td><span class="badge ' + trendBadge + '">' + escapeHtml(trend) + '</span></td><td><span class="badge ' + badge + '">' + escapeHtml(tech) + '</span></td><td class="right ' + direction + '">' + scoreText + '</td><td class="right"><button class="row-delete-button" type="button" data-delete-symbol="' + escapeAttr(symbol) + '" aria-label="Delete ' + escapeAttr(symbol) + ' from Matrix" title="Delete from Matrix">x</button></td></tr>';
      }).join("");

      matrixRows.querySelectorAll("[data-symbol]").forEach((row) => {
        row.addEventListener("click", (event) => {
          if (event.target.closest("button")) return;
          openStockDetail(row.dataset.symbol);
        });
      });

      matrixRows.querySelectorAll("[data-open-symbol]").forEach((button) => {
        button.addEventListener("click", () => openStockDetail(button.dataset.openSymbol));
      });

      matrixRows.querySelectorAll("[data-delete-symbol]").forEach((button) => {
        button.addEventListener("click", (event) => {
          event.stopPropagation();
          deleteMatrixStock(button.dataset.deleteSymbol);
        });
      });
    }

    function openView(target) {
      tabs.forEach((item) => item.classList.toggle("active", item.dataset.tab === target));
      views.forEach((view) => view.classList.toggle("active", view.dataset.view === target));
      window.scrollTo({top: 0, behavior: "smooth"});
    }

    window.handleNativeBack = function handleNativeBack() {
      const activeView = document.querySelector(".view.active")?.dataset.view || "home";
      if (activeView === "home") return false;
      openView(activeView === "detail" ? "matrix" : "home");
      return true;
    };

    function setDetailLoading(symbol) {
      selectedSymbol = symbol;
      document.getElementById("detailSymbol").textContent = symbol || "SELECT";
      document.getElementById("detailSubtitle").textContent = "Searching news, 52-week range, and revenue history...";
      document.getElementById("detailSource").textContent = "Loading";
      document.getElementById("detailLtp").textContent = "--";
      document.getElementById("detailAf").textContent = "--";
      document.getElementById("detailHigh").textContent = "--";
      document.getElementById("detailLow").textContent = "--";
      document.getElementById("detailHighDate").textContent = "--";
      document.getElementById("detailLowDate").textContent = "--";
      document.getElementById("revenueChart").innerHTML = '<div class="body-copy">Loading revenue chart...</div>';
      document.getElementById("detailNews").innerHTML = '<div class="body-copy">Searching recent articles...</div>';
    }

    function openStockDetail(symbol) {
      const normalized = normalizeCustomSymbol(symbol);
      if (!normalized || normalized === "-") return;
      const requestId = ++detailRequestSeq;
      setDetailLoading(normalized);
      openView("detail");
      const collectingToken = showCollecting(
        "LOADING STOCK LENS",
        "Collecting the latest quote, revenue history, range, and recent headlines for " + normalized + "."
      );
      setTimeout(async () => {
        try {
          const detail = await callNativeAsync("getStockDetailJson", normalized);
          if (requestId !== detailRequestSeq || selectedSymbol !== normalized) return;
          renderStockDetail(detail);
        } catch (error) {
          if (requestId !== detailRequestSeq || selectedSymbol !== normalized) return;
          document.getElementById("detailSubtitle").textContent = error.message || "Unable to load stock detail.";
          document.getElementById("revenueChart").innerHTML = '<div class="body-copy">Revenue data unavailable.</div>';
          document.getElementById("detailNews").innerHTML = '<div class="body-copy">News search unavailable.</div>';
        } finally {
          hideCollecting(collectingToken);
        }
      }, 80);
    }

    function renderStockDetail(detail) {
      const quote = detail.quote || {};
      const range = detail.range_52w || {};
      const revenue = Array.isArray(detail.revenue) ? detail.revenue : [];
      const news = Array.isArray(detail.news) ? detail.news : [];
      const trend = String(quote.psar_trend || quote.prediction || "--").toUpperCase();

      selectedSymbol = detail.symbol;
      document.getElementById("detailSymbol").textContent = detail.symbol || "SELECT";
      document.getElementById("detailSource").textContent = detail.yahoo_symbol || "Yahoo Finance";
      document.getElementById("detailSubtitle").textContent = trend === "--"
        ? "Detail loaded from Yahoo Finance and Google News."
        : "Trend " + trend + " | PSAR AF " + fmtNum(quote.psar_af, 2) + " | Score " + fmtNum(quote.confluence_score, 2);
      document.getElementById("detailLtp").textContent = quote.ltp ? "₹" + fmtNum(quote.ltp, 2) : "--";
      document.getElementById("detailAf").textContent = fmtNum(quote.psar_af, 2);
      document.getElementById("detailHigh").textContent = range.high ? "₹" + fmtNum(range.high, 2) : "--";
      document.getElementById("detailLow").textContent = range.low ? "₹" + fmtNum(range.low, 2) : "--";
      document.getElementById("detailHighDate").textContent = range.high_date || "--";
      document.getElementById("detailLowDate").textContent = range.low_date || "--";
      renderRevenueChart(revenue);
      renderDetailNews(news);
    }

    function renderRevenueChart(revenue) {
      const container = document.getElementById("revenueChart");
      if (!revenue.length) {
        container.innerHTML = '<div class="body-copy">Revenue data unavailable for this symbol.</div>';
        return;
      }
      const max = Math.max(...revenue.map((item) => Number(item.value || 0)), 1);
      document.getElementById("revenueTitle").textContent = (revenue[0].period_label || "Revenue") + " Revenue";
      container.innerHTML = revenue.map((item) => {
        const width = Math.max(4, Math.min(100, (Number(item.value || 0) / max) * 100));
        return '<div class="revenue-row"><span>' + escapeHtml(item.label || item.date || "--") + '</span><div class="revenue-track"><span style="--w:' + width.toFixed(1) + '%"></span></div><span class="right teal">' + escapeHtml(item.formatted || "--") + '</span></div>';
      }).join("");
    }

    function renderDetailNews(news) {
      const container = document.getElementById("detailNews");
      if (!news.length) {
        container.innerHTML = '<div class="body-copy">No recent articles found.</div>';
        return;
      }
      container.innerHTML = news.map((item) => {
        const url = safeExternalUrl(item.original_url || item.url || item.google_news_url);
        const time = formatNewsTime(item.published_at);
        const summary = item.summary || "Open the original article for the full report.";
        return '<a class="news-link-card" href="' + escapeAttr(url) + '"><div class="source-row"><span>' + escapeHtml(item.source || "News") + '</span><span>' + escapeHtml(time) + '</span></div><h3 class="intel-title">' + escapeHtml(item.title || "Untitled article") + '</h3><p class="body-copy">' + escapeHtml(summary) + '</p><div><span class="badge gray">OPEN ARTICLE</span></div></a>';
      }).join("");
    }

    function renderIntel(news, options = {}) {
      if (!news.length) {
        const failed = options.emptyState === "failed";
        const waiting = options.emptyState === "waiting" || options.emptyState === "saved";
        const title = failed ? "NEWS SEARCH UNAVAILABLE" : (waiting ? "WAITING FOR MATRIX NEWS" : "NO FRESH ARTICLES FOUND");
        const copy = failed
          ? "Saved headlines will remain visible after a successful update."
          : (waiting ? "Google News will sync when ranked Matrix stocks are available." : "The completed scan found no recent matching articles.");
        intelList.innerHTML = '<article class="intel-card"><h3 class="intel-title">' + title + '</h3><p class="body-copy">' + copy + '</p></article>';
        return;
      }
      intelList.innerHTML = news.slice(0, 20).map((item, index) => {
        const sentiment = item.sentiment || item.sentiment_label || "neutral";
        const badge = badgeClass(sentiment);
        const symbols = Array.isArray(item.affected_sectors) ? item.affected_sectors.slice(0, 2).join(", ") : (item.symbol || "MARKET");
        const symbol = item.symbol || symbols || "MARKET";
        const image = index === 0 ? '<div class="intel-image"></div>' : "";
        const time = formatNewsTime(item.published_at);
        const url = safeExternalUrl(item.original_url || item.url || item.google_news_url);
        const summary = item.summary || "Open the original article for the full report.";
        const source = symbol + " / " + (item.source || "News");
        const stale = Boolean(options.stale || item.stale);
        const staleBadge = stale ? ' <span class="badge gray">SAVED</span>' : "";
        return '<a class="intel-card" href="' + escapeAttr(url) + '">' + image + '<div class="source-row"><span>' + escapeHtml(source) + staleBadge + '</span><span>' + escapeHtml(time) + '</span></div><h3 class="intel-title">' + escapeHtml(item.title || "Untitled signal") + '</h3><p class="body-copy intel-summary">' + escapeHtml(summary) + '</p><div class="intel-link-row"><span><span class="badge ' + badge + '">' + escapeHtml(sentiment.replaceAll("_", " ")) + '</span> <span class="badge gray">' + escapeHtml(symbols || "MARKET") + '</span></span><span class="badge gray">OPEN ARTICLE</span></div></a>';
      }).join("");
    }

    function formatEventDate(value) {
      if (!value) return "--";
      const date = new Date(value + "T00:00:00+05:30");
      if (Number.isNaN(date.getTime())) return value;
      return date.toLocaleDateString("en-IN", {day: "2-digit", month: "short"});
    }

    function eventCountdown(days) {
      const count = Number(days);
      if (Number.isNaN(count)) return "--";
      if (count === 0) return "TODAY";
      if (count === 1) return "T-1";
      return "T-" + count;
    }

    function renderEvents(events) {
      if (!eventsList) return;
      if (!events.length) {
        eventsList.innerHTML = '<article class="event-card"><div class="event-copy"><div class="source-row"><span>EVENT WATCH</span><span>CALENDAR</span></div><h3 class="event-title">NO UPCOMING MARKET EVENTS</h3><p class="event-note">Major macro and policy events will appear here.</p></div><div class="event-countdown">--</div></article>';
        return;
      }

      eventsList.innerHTML = events.slice(0, 6).map((event) => {
        const impact = String(event.impact || "medium").toLowerCase();
        const badge = impact === "high" ? "red" : "teal";
        return '<article class="event-card ' + escapeAttr(impact) + '"><div class="event-copy"><div class="source-row"><span><span class="badge ' + badge + '">' + escapeHtml(event.category || "Market") + '</span></span><span>' + escapeHtml(formatEventDate(event.date)) + '</span></div><h3 class="event-title">' + escapeHtml(event.title || "Market event") + '</h3><p class="event-note">' + escapeHtml(event.note || "") + '</p></div><div class="event-countdown">' + escapeHtml(eventCountdown(event.days_until)) + '</div></article>';
      }).join("");
    }

    function renderNewsActionCards(actions) {
      const rows = Array.isArray(actions) ? actions : [];
      return rows.slice(0, 8).map((item) => {
        const priority = String(item.priority || "low").toLowerCase();
        const direction = String(item.direction || "neutral").toLowerCase();
        const cls = priority === "high" ? "critical" : priority === "medium" ? "warn" : "info";
        const badge = priority === "high" ? "red" : priority === "medium" ? "teal" : "gray";
        const setupScore = Number(item.setup_score ?? item.setup_probability);
        const setupScoreText = Number.isFinite(setupScore) ? Math.round(setupScore) + "/100" : "--";
        const impactText = fmtDelta(item.impact_min_percent) + " to " + fmtDelta(item.impact_max_percent);
        const currentPrice = Number(item.current_price);
        const priceText = Number.isFinite(currentPrice) && currentPrice > 0 ? "CMP ₹" + fmtNum(currentPrice, 2) : "CMP --";
        const moveText = "DAY " + fmtDelta(item.change_percent);
        const related = Array.isArray(item.related_symbols) && item.related_symbols.length
          ? "RELATED " + item.related_symbols.join(", ")
          : "MATRIX STOCK";
        const sourceUrl = item.url ? safeExternalUrl(item.url) : "";
        const sourceLink = sourceUrl
          ? '<a class="news-source-link" href="' + escapeAttr(sourceUrl) + '">OPEN SOURCE</a>'
          : '<span>' + escapeHtml(item.source || "Google News") + '</span>';
        const directionClass = direction === "bearish" ? "red" : direction === "bullish" ? "teal" : "muted";
        const savedBadge = item.stale ? ' <span class="badge gray">SAVED</span>' : "";
        const entryLow = Number(item.stock_entry_low);
        const entryHigh = Number(item.stock_entry_high);
        const stopLoss = Number(item.stock_stop_loss);
        const targetOne = Number(item.stock_target_1);
        const targetTwo = Number(item.stock_target_2);
        const targetRunner = Number(item.stock_target_runner);
        const hasTradePlan = [entryLow, entryHigh, stopLoss, targetOne, targetTwo, targetRunner].every(Number.isFinite);
        const tradePlan = hasTradePlan
          ? '<div class="trade-plan"><div class="trade-plan-head"><span>STOCK PLAN · ' + escapeHtml(item.stock_side || "WATCH") + '</span><span>MODEL ZONES</span></div>'
            + '<div class="trade-levels">'
            + '<div class="trade-level"><span>Entry zone</span><strong class="trade-range">₹' + fmtNum(entryLow, 2) + '<br>₹' + fmtNum(entryHigh, 2) + '</strong></div>'
            + '<div class="trade-level"><span>Stop</span><strong class="red">₹' + fmtNum(stopLoss, 2) + '</strong></div>'
            + '<div class="trade-level"><span>T1 · 35%</span><strong>₹' + fmtNum(targetOne, 2) + '</strong></div>'
            + '<div class="trade-level"><span>T2 · 35%</span><strong>₹' + fmtNum(targetTwo, 2) + '</strong></div>'
            + '<div class="trade-level"><span>Runner · 30%</span><strong class="' + directionClass + '">₹' + fmtNum(targetRunner, 2) + '</strong></div>'
            + '</div><p class="trade-condition"><span class="trade-note-label">ENTRY TRIGGER</span>' + escapeHtml(item.entry_condition || "Wait for price confirmation.")
            + '<br><br><span class="trade-note-label">PROFIT BOOKING</span>' + escapeHtml(item.profit_booking || "Scale out as targets are reached.") + '</p></div>'
          : '';
        const optionTargetOne = Number(item.option_target_1_percent);
        const optionTargetTwo = Number(item.option_target_2_percent);
        const optionRunner = Number(item.option_target_runner_percent);
        const optionStop = Number(item.option_stop_percent);
        const optionPlan = isFoStock(item.symbol) && item.option_side && item.option_side !== "NO TRADE"
          ? '<div class="trade-plan option-plan"><div class="option-plan-head"><span>F&amp;O PLAN</span><strong>' + escapeHtml(item.option_side) + '</strong></div>'
            + '<div class="trade-levels">'
            + '<div class="trade-level"><span>Contract</span><strong>ATM / ITM</strong></div>'
            + '<div class="trade-level"><span>Premium stop</span><strong class="red">' + (Number.isFinite(optionStop) ? optionStop : -25) + '%</strong></div>'
            + '<div class="trade-level"><span>T1 · 40%</span><strong>+' + (Number.isFinite(optionTargetOne) ? optionTargetOne : 20) + '%</strong></div>'
            + '<div class="trade-level"><span>T2 · 35%</span><strong>+' + (Number.isFinite(optionTargetTwo) ? optionTargetTwo : 40) + '%</strong></div>'
            + '<div class="trade-level"><span>Runner · 25%</span><strong class="teal">+' + (Number.isFinite(optionRunner) ? optionRunner : 65) + '%</strong></div>'
            + '</div><p class="option-plan-note"><span class="trade-note-label">CONTRACT FILTER</span>' + escapeHtml(item.option_contract || "Use the nearest monthly liquid ATM or ITM contract.")
            + '<br><br>' + escapeHtml(item.option_risk_note || "Premium targets are measured from the actual fill and require live liquidity checks.") + '</p></div>'
          : '';
        return '<article class="alert-card ' + cls + ' news-action-card">'
          + '<div class="alert-top"><span><span class="badge ' + badge + '">NEWS ' + escapeHtml(priority.toUpperCase()) + '</span>' + savedBadge + '</span><span>' + escapeHtml(formatNewsTime(item.published_at)) + '</span></div>'
          + '<h3 class="alert-title">' + escapeHtml(item.symbol || "STOCK") + ' · ' + escapeHtml(item.action || "WATCH") + '</h3>'
          + '<div class="news-action-metrics">'
          + '<div class="news-action-metric"><span>Heuristic score</span><strong>' + setupScoreText + '</strong></div>'
          + '<div class="news-action-metric"><span>Model impact</span><strong class="' + directionClass + '">' + impactText + '</strong></div>'
          + '<div class="news-action-metric"><span>Horizon</span><strong>' + escapeHtml(item.time_horizon || "1-3 sessions") + '</strong></div>'
          + '</div>'
          + '<p class="news-action-headline"><span class="badge gray">' + escapeHtml(item.catalyst || "News") + '</span> ' + priceText + ' · ' + moveText + '<br>' + escapeHtml(item.headline || "Catalyst detected") + '</p>'
          + tradePlan
          + optionPlan
          + '<p class="news-action-strategy"><strong>STRATEGY:</strong> ' + escapeHtml(item.strategy || "Wait for price confirmation.") + '</p>'
          + '<div class="source-row"><span>' + escapeHtml(related) + '</span>' + sourceLink + '</div>'
          + '<p class="news-action-risk">' + escapeHtml(item.risk_note || "Heuristic estimate; confirm price and volume.") + '</p>'
          + '</article>';
      }).join("");
    }

    function setAlertFilter(filter) {
      activeAlertFilter = filter || "all";
      document.querySelectorAll("[data-alert-filter]").forEach((button) => {
        button.classList.toggle("active", button.dataset.alertFilter === activeAlertFilter);
      });
      renderAlerts(currentDashboard?.alerts || []);
    }

    function setAlertsMarkup(markup) {
      alertsList.innerHTML = markup;
      alertsList.querySelectorAll("[data-close-symbol]").forEach((button) => {
        button.addEventListener("click", () => openStockDetail(button.dataset.closeSymbol));
      });
    }

    function renderAlerts(alerts) {
      const apiAlerts = Array.isArray(alerts) ? alerts : [];
      const closeSynthesis = buildFallingCloseSynthesis(closeWatchlistRows());
      const showNews = activeAlertFilter === "all" || activeAlertFilter === "news";
      const showTechnical = activeAlertFilter === "all" || activeAlertFilter === "technical";
      const showClose = activeAlertFilter === "all" || activeAlertFilter === "close";
      const closeCard = showClose ? renderCloseSynthesisCard(closeSynthesis) : "";
      const newsActionCards = showNews ? renderNewsActionCards(latestNewsActions) : "";
      const localAlertCount = closeSynthesis.stocks.length;
      const kpiAlerts = document.getElementById("kpiAlerts");
      if (kpiAlerts) {
        kpiAlerts.textContent = apiAlerts.length + localAlertCount + latestNewsActions.length;
      }

      if (!apiAlerts.length || !showTechnical) {
        const filteredContent = newsActionCards + closeCard;
        setAlertsMarkup(filteredContent || '<article class="alert-card info"><h3 class="alert-title">NO ALERTS IN THIS CHANNEL</h3><div class="alert-body">No current signals match this filter.</div></article>');
        return;
      }
      const appAlertCards = apiAlerts.slice(0, 10).map((alert) => {
        const severity = String(alert.severity || "medium").toLowerCase();
        const cls = severity === "high" ? "critical" : severity === "medium" ? "warn" : "info";
        const badge = severity === "high" ? "red" : severity === "medium" ? "teal" : "gray";
        const label = severity === "high" ? "BREAKING" : severity === "medium" ? "ACTIONABLE" : "INFO";
        const time = alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"}) : "LIVE";
        return '<article class="alert-card ' + cls + '"><div class="alert-top"><span class="badge ' + badge + '">' + label + '</span><span>' + time + '</span></div><h3 class="alert-title">' + escapeHtml(alert.title || "Market alert") + '</h3><div class="alert-body">' + escapeHtml(alert.message || "") + '</div><div class="source-row"><span>SEVERITY <span class="' + badge + '">' + escapeHtml(severity.toUpperCase()) + '</span></span><span>APP ENGINE</span></div></article>';
      }).join("");
      setAlertsMarkup(newsActionCards + closeCard + appAlertCards);
    }

    function startLiveSync() {
      const scheduleNextSync = (delay) => {
        clearTimeout(refreshTimer);
        if (document.hidden) return;
        refreshTimer = setTimeout(syncOnce, delay);
      };

      const syncOnce = async () => {
        const now = Date.now();
        if (now - lastSyncStartedAt < 2000) return;
        lastSyncStartedAt = now;
        let succeeded = false;
        try {
          const outcome = await refreshLiveData();
          if (outcome === null) return;
          succeeded = outcome;
        } catch (error) {
          console.error("Live data sync error:", error);
          setStatus(currentDashboard ? "UPDATE DELAYED" : "OFFLINE", false);
        } finally {
          const nextDelay = succeeded
            ? (currentMarketStatus?.is_open ? MARKET_OPEN_REFRESH_MS : MARKET_CLOSED_REFRESH_MS)
            : SYNC_RETRY_MS;
          scheduleNextSync(nextDelay);
        }
      };

      setStatus("SYNCING", true);
      syncOnce();
      document.addEventListener("visibilitychange", () => {
        if (document.hidden) {
          clearTimeout(refreshTimer);
          refreshTimer = null;
          return;
        }
        syncOnce();
      });
    }

    document.getElementById("addStockForm").addEventListener("submit", (event) => {
      event.preventDefault();
      addCustomStock(stockInput.value);
    });

    stockInput.addEventListener("input", () => {
      const normalized = normalizeCustomSymbol(stockInput.value);
      if (stockInput.value !== normalized) {
        stockInput.value = normalized;
      }
      updateStockInputClearButton();
    });

    renderCustomStockChips();
    renderHiddenStockControl();
    restoreLastSuccessfulSnapshot();
    startLiveSync();
  </script>
</body>
</html>`;

fs.mkdirSync(outputDir, {recursive: true});
fs.writeFileSync(outputPath, html);
console.log(`Wrote ${path.relative(repoRoot, outputPath)}`);
