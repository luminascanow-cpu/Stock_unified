---
version: alpha
name: "Confluence Terminal"
description: "A dense mobile market terminal for fast technical, price, and news-impact decisions."
colors:
  primary: "#36ffc4"
  background: "#0b1321"
  background-deep: "#060e1c"
  surface: "#18202e"
  surface-low: "#141c2a"
  border: "#45474c"
  text: "#dbe2f6"
  muted: "#c5c6cc"
  danger: "#e73b3e"
  warning: "#ffd60a"
typography:
  sans:
    fontFamily: "Hanken Grotesk, Avenir Next, system-ui, sans-serif"
  mono:
    fontFamily: "JetBrains Mono, SFMono-Regular, monospace"
rounded:
  DEFAULT: "0.25rem"
  sm: "0.125rem"
  pill: "999px"
spacing:
  page: "1rem"
  panel: "1rem"
  stack: "0.75rem"
components:
  button: { }
  card: { }
  table: { }
  badge: { }
  navigation: { }
---

# Confluence Terminal Design System

## Overview

### Creative North Star

The interface should feel like a compact trading workstation reduced to a phone: precise, high-contrast, data-first, and calm under time pressure.

### Product context and register

- **Audience and primary job:** Indian-market traders scanning technical strength, live moves, and news catalysts.
- **Target market and evidence:** NSE symbols, INR formatting, IST timestamps, F&O marking, and India-focused Google News queries in the app.
- **Locale and language policy:** English UI with `en-IN` numbers and Asia/Kolkata market time.
- **Usage scene:** Repeated, urgent checks on an Android phone; dense information must remain scannable with one hand.
- **Register:** Product dashboard. Utility and signal clarity lead over decoration.
- **Memorable signature:** Teal terminal accents with monospaced numeric readouts and hard left-edge alert severity marks.
- **Restraint:** Tables, strategy alerts, and metrics use flat surfaces, short labels, and stable geometry.
- **Anti-references:** Marketing landing pages, oversized hero typography, soft pastel finance apps, and decorative card stacks.
- **Token ownership/runtime mapping:** This file mirrors the canonical CSS variables in `tools/generate_standalone_asset.mjs`; the generated `app/src/main/assets/index.html` is an output, not a token owner.

## Colors

The dark navy surfaces support prolonged scanning. Teal means live, positive, or confirmed; red means bearish or high-priority risk; yellow is reserved for F&O and caution. Text meaning is always repeated in labels or icons rather than color alone.

## Typography

Body copy uses the sans stack. Tickers, prices, timestamps, badges, controls, and headings use the mono stack. Numeric columns remain tabular and compact; letter spacing remains zero.

## Layout

The app uses a narrow single-column phone layout with a two-column home summary on wider screens. Home technical cards collapse to one column below 520px, and strategy targets wrap into a two-column grid so prices never require horizontal scrolling. The Matrix alone owns horizontal overflow inside its table surface. The native shell applies the Android status-bar inset, the fixed bottom navigation respects bottom safe areas, and async refreshes preserve panel dimensions.

## Elevation & Depth

Hierarchy comes from tonal surfaces, borders, and restrained backdrop blur. Static content does not rely on large shadows. Red and teal edge rules identify actionable states without changing card size.

## Shapes

Panels and cards use 4px or smaller radii. Pills are limited to compact live-status indicators; data cards and buttons remain squared and technical.

## Components

### Foundational visual states

Interactive controls expose default, focus, pressed, disabled, and busy states. Live refresh retains the previous usable data on transient failures and labels timestamps so stale market sessions are visible.

### Buttons and actions

Primary actions use teal fill or teal borders. Destructive Matrix actions use red and remain spatially separate from row navigation. Busy labels keep button dimensions stable.

### Navigation and data display

Bottom tabs retain stable icon and label geometry. Matrix rows may combine F&O, RSI, and news badges; news priority wins the row-edge color while every badge remains textual.
Multi-day close weakness scans the complete active watchlist, including symbols added by in-app discovery. Each weakness row is a full-width terminal control that opens the existing stock Lens and exposes hover, press, and keyboard-focus states.
Matrix and close-ledger status use compact textual coverage labels. Partial scans keep prior technical rows in place and add `SAVED TECH` or `NO TECH` badges; quote age is shown beside CMP so stale and missing data never rely on color alone.
Matrix custom-stock management stays compact: the saved active count remains visible, while removable ticker chips appear only through an explicit `Manage` disclosure and collapse after a successful add.

### Forms and overlays

The ticker input uses app-owned validation text. The app does not use browser alert, confirm, or prompt dialogs. Market collection uses a bounded app-owned status overlay with a stable technical scan animation, descriptive live text, and a reduced-motion state.
Daily Kite reauthentication uses the same terminal language: a stable Home status card owns checking, connected, login-required, server-setup, and offline states. An app-owned modal may request the daily Zerodha login once per India calendar day; it contains no credential fields, traps focus, supports Escape/Later, and keeps Yahoo Finance explicitly available as the non-blocking fallback.

### Iconography

The current terminal glyph set is compact and monochrome. Every navigation glyph has a visible text label; unfamiliar actions retain tooltips or accessible labels.

### Motion

Motion is brief and communicates entry, live status, or press feedback. Reduced-motion settings should disable nonessential transforms and pulsing.

### Content and data visualization

Copy is concise and operational. Percentages include signs; market time uses IST; strategy alerts separate catalyst, uncalibrated heuristic score, expected range, entry, stop, staged exits, confirmation, invalidation, and risk language. F&O plans distinguish stock price targets from option-premium percentage exits and never imply a live strike or premium without option-chain data.
Sector flow uses flat terminal rows with a fixed centerline: teal extends right for estimated inflow and red extends left for estimated outflow. The sector map uses tile area for estimated turnover and colour intensity for turnover-weighted percentage change. Every view repeats direction, values, breadth, coverage, freshness, and session state in text; no visualization implies exchange order-book or institutional-flow data. India VIX uses the same macro-card owner as USD/INR and crude, with textual value, change, regime, approximate one-day move, and quote time.

### Web discovery

Fresh headline matches appear as flat rows in Intel. Each row shows the verified NSE symbol, company, match confidence, source headline, and explicit Watchlist state. Strong matches may be added automatically, while every addition remains removable from Matrix.

## Do's and Don'ts

- **Do:** Keep current price, timestamp, and the reason for an alert visible together.
- **Do:** Show previous close and current price as separate labeled numeric fields.
- **Do:** Label model estimates as heuristic and require price/volume confirmation.
- **Don't:** Present probability as a guaranteed return or hide risk behind color alone.
- **Don't:** Add promotional hero sections, decorative nested cards, or ambiguous signal labels.
