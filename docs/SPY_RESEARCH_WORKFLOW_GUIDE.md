# SPY Research Workflow Guide

## Purpose

This document explains how the SPY research project currently works end-to-end:

```text
raw 1m OHLCV data
    ↓
processed timeframe bars
    ↓
feature tables
    ↓
chart viewer overlays
    ↓
Phase 2 behavior study
    ↓
Phase 3 deterministic signal research
```

The goal is to make the system understandable enough that when new raw 1-minute SPY data arrives, you know exactly what to rebuild, which scripts to run, what files should appear, and what each feature means when you inspect it visually.

This project is intentionally narrow:

```text
SPY first
intraday direction first
underlying first
options later
execution last
```

The current feature layer is not trying to be a giant indicator library. It is trying to create a clean intraday market-state table from OHLCV data.

---

# 1. Current high-level workflow

Your current understanding is correct.

## Step 1 — Start with raw 1-minute data

Current raw data location:

```text
data/raw/SPY_1min_firstratedata.csv
```

This file contains the base OHLCV data:

```text
timestamp
open
high
low
close
volume
```

The raw file is the source of truth.

---

## Step 2 — Build processed bars

Script:

```text
scripts/build_processed_data.py
```

Purpose:

This script reads the raw 1-minute file and creates clean regular-trading-hours bars in multiple timeframes.

Output folder:

```text
data/processed/
```

Expected outputs:

```text
data/processed/spy_1m_rth.parquet
data/processed/spy_5m_rth.parquet
data/processed/spy_30m_rth.parquet
data/processed/spy_1h_rth.parquet
```

If you run the script with CSV output enabled, it may also create:

```text
data/processed/spy_1m_rth.csv
data/processed/spy_5m_rth.csv
data/processed/spy_30m_rth.csv
data/processed/spy_1h_rth.csv
```

### What `.parquet` is for

Parquet is the real research data format.

Use Parquet for:

```text
Python research
feature building
backtests
ML datasets
chart backend
```

Why:

- faster than CSV,
- preserves datatypes better,
- smaller,
- better for repeated research workflows.

### What `.csv` is for

CSV is mostly for you.

Use CSV for:

```text
manual inspection
quick debugging
opening in Excel
checking output visually
```

CSV is not the preferred internal research format.

---

## Step 3 — Build feature tables

Script:

```text
scripts/build_features.py
```

Purpose:

This script reads one processed timeframe file and creates a new feature table that keeps OHLCV and adds derived intraday features.

Example command:

```powershell
uv run python scripts\build_features.py --timeframe 5m --csv
```

Input:

```text
data/processed/spy_5m_rth.parquet
```

Output:

```text
data/features/spy_5m_rth_features.parquet
data/features/spy_5m_rth_features.csv
```

To build all available feature timeframes:

```powershell
uv run python scripts\build_features.py --timeframe 1m --csv
uv run python scripts\build_features.py --timeframe 5m --csv
uv run python scripts\build_features.py --timeframe 30m --csv
uv run python scripts\build_features.py --timeframe 1h --csv
```

Expected output folder:

```text
data/features/
```

Expected files:

```text
spy_1m_rth_features.parquet
spy_1m_rth_features.csv

spy_5m_rth_features.parquet
spy_5m_rth_features.csv

spy_30m_rth_features.parquet
spy_30m_rth_features.csv

spy_1h_rth_features.parquet
spy_1h_rth_features.csv
```

---

## Step 4 — Chart viewer reads the feature tables

Backend file:

```text
apps/chart_viewer/backend/main.py
```

Frontend files:

```text
apps/chart_viewer/frontend/src/main.ts
apps/chart_viewer/frontend/src/style.css
```

The backend endpoint:

```text
/api/feature-bars
```

tries to load feature data first.

For example:

```text
data/features/spy_5m_rth_features.parquet
```

If the feature file exists, the chart viewer receives:

```text
OHLCV + derived feature columns
```

Then the frontend can draw overlays like:

```text
VWAP
previous day high / low / close
OR30 high / low
OR60 high / low
volume
selected-bar feature values
```

If the feature file does not exist for a timeframe, the backend falls back to plain processed OHLCV data from:

```text
data/processed/
```

That is why only 5m had overlays before you generated all timeframe feature tables.

---

# 2. Why the code is split between `scripts/` and `src/spy_research/`

This is important.

The files in `scripts/` are command-line entry points.

The files in `src/spy_research/` are reusable project modules.

Think of it like this:

```text
scripts/
    = buttons you press

src/spy_research/
    = engine parts those buttons use
```

The script should stay thin. The real logic should live inside `src/spy_research/`.

That way:

- scripts can call the logic,
- tests can call the same logic,
- notebooks can call the same logic,
- future backtests can call the same logic,
- the chart backend can reuse the same conventions later if needed.

---

# 3. What each major folder is for

## `data/raw/`

Source vendor data.

Example:

```text
data/raw/SPY_1min_firstratedata.csv
```

This should remain as close to the original vendor file as possible.

Do not casually edit raw files.

---

## `data/processed/`

Cleaned and resampled OHLCV bars.

Example:

```text
data/processed/spy_5m_rth.parquet
```

These files are derived from raw data.

They answer:

```text
What did SPY do on each timeframe?
```

They do not answer:

```text
Where was price relative to VWAP?
Did price break the opening range?
How far was price from previous day high?
```

Those questions belong to the feature tables.

---

## `data/features/`

Feature-enriched OHLCV tables.

Example:

```text
data/features/spy_5m_rth_features.parquet
```

These files include:

```text
OHLCV
time/session features
previous day levels
opening range levels
running session structure
VWAP
ATR/range features
volume features
```

They answer:

```text
What was the market state at this bar?
```

This folder is the bridge between raw price data and research decisions.

---

## `scripts/`

Command-line workflow tools.

Current important scripts:

```text
scripts/validate_data.py
scripts/build_processed_data.py
scripts/build_features.py
```

### `scripts/validate_data.py`

Purpose:

Checks that the raw data is sane before you build research outputs.

Typical checks:

```text
missing values
duplicate timestamps
OHLC violations
timestamp range
basic session coverage
```

You run this when:

```text
you first add raw data
you replace raw data
you extend the dataset
something feels wrong downstream
```

### `scripts/build_processed_data.py`

Purpose:

Turns raw 1-minute OHLCV into processed RTH bars.

Input:

```text
data/raw/
```

Output:

```text
data/processed/
```

You run this when:

```text
you add new raw data
you change processing rules
you need to regenerate processed bars
```

### `scripts/build_features.py`

Purpose:

Turns processed bars into feature tables.

Input:

```text
data/processed/
```

Output:

```text
data/features/
```

You run this when:

```text
processed data changes
feature logic changes
you need a missing timeframe feature table
```

---

## `src/spy_research/`

Reusable Python package code.

This is where the real project logic should live.

The current pattern is:

```text
scripts call src modules
tests call src modules
future notebooks call src modules
future backtests call src modules
```

### `src/spy_research/config.py`

Purpose:

Stores common paths and configuration constants.

Examples:

```text
DATA_DIR
RAW_DIR
PROCESSED_DIR
FEATURES_DIR
```

Why it exists:

So scripts do not hardcode paths everywhere.

---

## `src/spy_research/features/`

This folder contains feature-building modules.

The feature script:

```text
scripts/build_features.py
```

uses these modules to create the output feature table.

Current feature modules are conceptually split like this:

```text
schema.py
time.py
levels.py
vwap.py
volatility.py
volume.py
build.py
```

### `features/schema.py`

Purpose:

Defines the expected feature column groups and names.

Think of it as:

```text
the feature vocabulary
```

This helps keep names consistent.

Bad:

```text
prev_high
pdh
previous_day_high
yesterday_high
```

Good:

```text
prev_day_high
```

### `features/time.py`

Purpose:

Adds time/session fields.

Examples:

```text
session_date
minute_from_open
bar_index_in_session
```

These answer:

```text
Where are we inside the trading day?
```

### `features/levels.py`

Purpose:

Adds price structure levels.

Examples:

```text
session_open
running_session_high
running_session_low
prev_day_high
prev_day_low
prev_day_close
or30_high
or30_low
or60_high
or60_low
```

These answer:

```text
Where is price relative to important session levels?
```

### `features/vwap.py`

Purpose:

Adds session VWAP.

Examples:

```text
vwap
dist_to_vwap_pts
```

These answer:

```text
Is price above or below the session's volume-weighted average price?
```

### `features/volatility.py`

Purpose:

Adds range and volatility features.

Examples:

```text
bar_range_pts
true_range_pts
atr14_pts
```

These answer:

```text
Is this bar/range large or small relative to recent movement?
```

### `features/volume.py`

Purpose:

Adds volume participation features.

Examples:

```text
rolling_volume_20_bars
relative_volume_20
```

These answer:

```text
Is volume expanding or dead compared with recent bars?
```

### `features/build.py`

Purpose:

The orchestration layer for feature building.

It calls the smaller feature modules in the correct order.

Conceptually:

```text
start with processed OHLCV
add time features
add levels
add VWAP
add volatility
add volume
return full feature table
```

This is the main logic that `scripts/build_features.py` should call.

---

## `tests/`

Automated checks.

Purpose:

Make sure important assumptions do not break when you modify code.

Example checks:

```text
row count is preserved
minute_from_open starts correctly
previous day levels do not use current day data
opening range completion behaves correctly
VWAP calculation is sane
ATR does not use future data
```

Tests are especially important in this project because one small leakage bug can make a strategy look profitable when it is not.

---

## `apps/chart_viewer/`

Local research visualization tool.

This is not the core research engine.

It is a microscope.

It helps you visually inspect:

```text
candles
VWAP
previous day levels
opening range levels
volume
selected-bar feature state
```

Current structure:

```text
apps/chart_viewer/backend/
apps/chart_viewer/frontend/
```

### Backend

File:

```text
apps/chart_viewer/backend/main.py
```

Purpose:

Reads local Parquet files and serves JSON to the frontend.

Important endpoints:

```text
/api/health
/api/files
/api/timeframes
/api/bars
/api/feature-bars
/api/debug
```

### Frontend

Files:

```text
apps/chart_viewer/frontend/src/main.ts
apps/chart_viewer/frontend/src/style.css
```

Purpose:

Draws the local browser chart using TradingView Lightweight Charts.

It does not own research logic.

It should display features computed by Python.

---

# 4. Full rebuild workflow when new raw 1-minute data arrives

When you receive new raw SPY 1-minute data, use this order.

## Step 0 — Replace or add raw data

Put the new file in:

```text
data/raw/
```

If it replaces the old file, make sure the filename expected by the script is still correct, or update the script/config to point to the new file.

Current expected raw file:

```text
data/raw/SPY_1min_firstratedata.csv
```

---

## Step 1 — Refresh environment

From repo root:

```powershell
uv sync
```

Usually this is only needed after pulling new dependency changes.

---

## Step 2 — Validate raw data

```powershell
uv run python scripts\validate_data.py
```

Look for problems like:

```text
missing values
duplicate timestamps
bad OHLC rows
unexpected dates
unexpected session coverage
```

If validation fails, do not continue blindly.

---

## Step 3 — Rebuild processed bars

```powershell
uv run python scripts\build_processed_data.py
```

Expected output:

```text
data/processed/spy_1m_rth.parquet
data/processed/spy_5m_rth.parquet
data/processed/spy_30m_rth.parquet
data/processed/spy_1h_rth.parquet
```

---

## Step 4 — Rebuild feature tables

```powershell
uv run python scripts\build_features.py --timeframe 1m --csv
uv run python scripts\build_features.py --timeframe 5m --csv
uv run python scripts\build_features.py --timeframe 30m --csv
uv run python scripts\build_features.py --timeframe 1h --csv
```

Expected output:

```text
data/features/spy_1m_rth_features.parquet
data/features/spy_5m_rth_features.parquet
data/features/spy_30m_rth_features.parquet
data/features/spy_1h_rth_features.parquet
```

---

## Step 5 — Run tests

```powershell
uv run pytest
```

If tests fail, fix them before trusting research output.

---

## Step 6 — Start chart viewer backend

Terminal 1:

```powershell
cd $HOME\Desktop\spy_research
uv run uvicorn apps.chart_viewer.backend.main:app --reload --port 8000
```

Useful backend checks:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/health"
Invoke-RestMethod "http://127.0.0.1:8000/api/files"
Invoke-RestMethod "http://127.0.0.1:8000/api/debug?timeframe=5m"
```

For each timeframe, you want:

```text
features_available: True
duplicate_chart_times_after_normalize: 0
is_time_monotonic_increasing: True
```

---

## Step 7 — Start chart viewer frontend

Terminal 2:

```powershell
cd $HOME\Desktop\spy_research\apps\chart_viewer\frontend
npm run dev
```

Open:

```text
http://localhost:5173
```

Check:

```text
1m shows overlays
5m shows overlays
30m shows overlays
1h shows overlays
```

Remember:

```text
1m and 5m are best for opening-range inspection
30m and 1h are better for context
```

---

# 5. Current feature groups and how to think about them

This section explains what the current feature data points mean when you see them in the CSV, chart viewer, or future research tables.

---

## 5.1 Base OHLCV

Columns:

```text
timestamp
open
high
low
close
volume
```

Meaning:

These are the original bar values.

How to think:

```text
This is what price actually did during this bar.
Everything else is derived from these columns.
```

On the chart:

- candles come from OHLC,
- volume bars come from volume.

---

## 5.2 `session_date`

Meaning:

The trading date this bar belongs to.

How to think:

```text
This groups bars into trading days.
```

Used for:

- daily summaries,
- previous day levels,
- opening range,
- session reset,
- chart session separation later.

---

## 5.3 `minute_from_open`

Meaning:

How many minutes have passed since the regular market open.

RTH open:

```text
09:30 ET
```

Examples:

```text
09:30 → 0
09:35 → 5
10:00 → 30
10:30 → 60
15:55 → 385
```

How to think:

```text
This tells you where you are inside the day.
```

This is extremely important because the same candle behavior can mean different things at different times.

A breakout at 09:45 is not the same as a breakout at 13:15.

---

## 5.4 `bar_index_in_session`

Meaning:

The bar number inside the current RTH session.

For 5m data:

```text
09:30 → 0
09:35 → 1
09:40 → 2
```

How to think:

```text
This is a clean integer version of time-of-day position.
```

Useful for:

- grouping by session,
- finding first N bars,
- opening range logic,
- ML features later.

---

## 5.5 `session_open`

Meaning:

The first open of the RTH session.

How to think:

```text
This is the day's starting anchor.
```

If price is above session open, the day has positive intraday direction from the open.

If price is below session open, the day has negative intraday direction from the open.

Do not overuse this alone. It is an anchor, not a signal.

---

## 5.6 `running_session_high`

Meaning:

The highest price reached so far in the current session up to this bar.

How to think:

```text
This tells you the current high-of-day so far.
```

If price keeps making new running highs, the session may be trending up.

If price cannot revisit the running high and fades back to VWAP, the move may be weakening.

---

## 5.7 `running_session_low`

Meaning:

The lowest price reached so far in the current session up to this bar.

How to think:

```text
This tells you the current low-of-day so far.
```

If price keeps making new running lows, the session may be trending down.

---

## 5.8 `session_range_so_far_pts`

Meaning:

```text
running_session_high - running_session_low
```

How to think:

```text
How much range has the day already produced?
```

Useful questions:

```text
Is the day still compressed?
Has the day already expanded too much?
Is a breakout happening after a tight range?
```

For future signal research, this can help avoid chasing after the day has already made a huge move.

---

## 5.9 `close_location_in_session_range`

Meaning:

Where the close sits inside the current session range so far.

Formula:

```text
(close - running_session_low) / (running_session_high - running_session_low)
```

Interpretation:

```text
near 1.0 → close is near high of day
near 0.5 → close is near middle of day range
near 0.0 → close is near low of day
```

How to think:

```text
This is a simple day-shape variable.
```

If price is near 1.0 and above VWAP, it may be an upside trend/pressure day.

If price is near 0.0 and below VWAP, it may be a downside trend/pressure day.

If it keeps rotating around 0.5, it may be chop.

---

## 5.10 `prev_day_high`

Meaning:

Previous RTH session high.

How to think:

```text
This is yesterday's upper boundary.
```

When price approaches it, watch:

```text
does it reject?
does it break and hold?
does volume expand?
is price above VWAP?
```

A break above previous day high is not automatically bullish. The important question is whether it accepts above that level or fails back below.

---

## 5.11 `prev_day_low`

Meaning:

Previous RTH session low.

How to think:

```text
This is yesterday's lower boundary.
```

When price approaches it, watch:

```text
does it reject?
does it break and hold?
does volume expand?
is price below VWAP?
```

A break below previous day low is not automatically bearish. Acceptance versus rejection matters.

---

## 5.12 `prev_day_close`

Meaning:

Previous RTH session close.

How to think:

```text
This is the reference point for the overnight gap.
```

Important for:

```text
gap up
gap down
gap fill
gap continuation
```

---

## 5.13 `gap_from_prev_close_pts`

Meaning:

```text
session_open - prev_day_close
```

Interpretation:

```text
positive → gap up
negative → gap down
near zero → flat open
```

How to think:

A gap changes the context of the day.

Example thoughts:

```text
Gap up above previous day high:
    potential strength, but also risk of gap fade.

Gap down below previous day low:
    potential weakness, but also risk of reversal.

Small gap:
    opening range and VWAP may matter more than gap context.
```

Do not treat gaps as signals by themselves yet. Treat them as context.

---

## 5.14 `or30_high`

Meaning:

The high of the first 30 minutes of RTH.

On 5m data, this covers:

```text
09:30 through 09:55 bars
```

Known after:

```text
10:00 ET
```

How to think:

```text
This is the first major opening range upper boundary.
```

When price breaks above OR30 high after the range is complete, ask:

```text
Is price above VWAP?
Is volume expanding?
Is the bar strong or weak?
Does it hold above the level or fail back inside?
```

---

## 5.15 `or30_low`

Meaning:

The low of the first 30 minutes of RTH.

Known after:

```text
10:00 ET
```

How to think:

```text
This is the first major opening range lower boundary.
```

When price breaks below OR30 low after the range is complete, ask:

```text
Is price below VWAP?
Is volume expanding?
Is the bar strong or weak?
Does it hold below the level or reclaim back inside?
```

---

## 5.16 `or30_range_pts`

Meaning:

```text
or30_high - or30_low
```

How to think:

```text
How wide was the first 30-minute range?
```

A narrow OR30 can lead to cleaner breakout opportunities.

A very wide OR30 can mean the move already happened and breakout entries may be late.

This is not a fixed truth yet. It is something to study statistically.

---

## 5.17 `or30_complete`

Meaning:

Whether the first 30-minute opening range is complete.

Interpretation:

```text
False before 10:00
True from 10:00 onward
```

How to think:

Do not use OR30 breakout logic before OR30 is complete.

This prevents lookahead leakage.

---

## 5.18 `or60_high`

Meaning:

The high of the first 60 minutes of RTH.

Known after:

```text
10:30 ET
```

How to think:

```text
This is a broader opening structure level.
```

OR60 is slower than OR30. It may be useful for:

```text
morning trend continuation
larger day structure
avoiding noisy early breaks
```

---

## 5.19 `or60_low`

Meaning:

The low of the first 60 minutes of RTH.

Known after:

```text
10:30 ET
```

How to think:

```text
This is the broader morning lower boundary.
```

---

## 5.20 `or60_range_pts`

Meaning:

```text
or60_high - or60_low
```

How to think:

```text
How much range did the first hour produce?
```

A wide OR60 may mean the morning already had major movement.

A narrow OR60 may indicate compression before later expansion.

Again, this should be tested, not assumed.

---

## 5.21 `or60_complete`

Meaning:

Whether the first 60-minute opening range is complete.

Interpretation:

```text
False before 10:30
True from 10:30 onward
```

How to think:

Do not use OR60 breakout logic before OR60 is complete.

---

## 5.22 `vwap`

Meaning:

Session VWAP.

VWAP means:

```text
Volume Weighted Average Price
```

Approximate formula:

```text
cumulative typical price * volume / cumulative volume
```

where typical price is usually:

```text
(high + low + close) / 3
```

How to think:

VWAP is a major intraday anchor.

Simple interpretation:

```text
price above VWAP → buyers have control relative to session average
price below VWAP → sellers have control relative to session average
price chopping around VWAP → balanced / uncertain / mean-reverting behavior
```

For deterministic rules:

- Long breakouts are cleaner above VWAP.
- Short breakdowns are cleaner below VWAP.
- Reclaims of VWAP can matter.
- Failed moves back through VWAP can matter.

VWAP is not magic. Treat it as context and structure.

---

## 5.23 `dist_to_vwap_pts`

Meaning:

```text
close - vwap
```

Interpretation:

```text
positive → close is above VWAP
negative → close is below VWAP
near zero → close is near VWAP
```

How to think:

This is more useful than just asking whether price is above or below VWAP.

Examples:

```text
slightly above VWAP:
    maybe early strength or possible chop.

far above VWAP:
    possible trend strength, but also possible overextension.

below VWAP after failed OR breakout:
    possible failed breakout / reversal context.
```

Later, we may normalize this by ATR:

```text
distance_to_vwap_in_atr_units
```

That will make it easier to compare across volatility regimes.

---

## 5.24 `bar_range_pts`

Meaning:

```text
high - low
```

How to think:

```text
How large was this individual candle?
```

A large range candle near a breakout may indicate expansion.

A tiny range candle near a breakout may indicate weak participation or hesitation.

But bar range alone is not enough. Compare it to ATR or recent range.

---

## 5.25 `true_range_pts`

Meaning:

True range accounts for gaps between bars.

Formula concept:

```text
max(
    high - low,
    abs(high - previous close),
    abs(low - previous close)
)
```

How to think:

This is a better building block for volatility than `high - low` alone.

For intraday RTH bars, gaps between adjacent bars are usually small, but true range is still the standard ATR input.

---

## 5.26 `atr14_pts`

Meaning:

Average true range over the previous 14 bars, based on the current timeframe.

How to think:

```text
Recent average movement size.
```

On 5m data:

```text
14 bars ≈ 70 minutes
```

On 1m data:

```text
14 bars ≈ 14 minutes
```

On 30m data:

```text
14 bars ≈ almost 7 trading hours
```

On 1h data:

```text
14 bars ≈ multiple sessions
```

So ATR meaning changes by timeframe.

Use ATR to normalize:

```text
Is this candle large relative to recent movement?
Is the stop too tight?
Is the target realistic?
Is price extended from VWAP or OR level?
```

---

## 5.27 `rolling_volume_20_bars`

Meaning:

Rolling average volume over the last 20 bars.

How to think:

```text
What is recent typical volume for this timeframe?
```

On 5m data:

```text
20 bars ≈ 100 minutes
```

On 1m data:

```text
20 bars ≈ 20 minutes
```

This is a simple participation baseline.

It is not perfect because volume is very time-of-day dependent. Later, a better version will compare current volume to average volume at the same time of day.

---

## 5.28 `relative_volume_20`

Meaning:

```text
volume / rolling_volume_20_bars
```

Interpretation:

```text
1.0 → normal volume compared with recent bars
1.5 → 50% higher than recent average
2.0 → double recent average
0.5 → half recent average
```

How to think:

When inspecting a breakout:

```text
relative volume > 1:
    some participation

relative volume much > 1:
    possible expansion / urgency

relative volume < 1:
    weak participation
```

But be careful:

At the open, volume is naturally high.

Near lunch, volume is naturally lower.

So this feature is useful but not final. Later we may add:

```text
relative_volume_vs_time_of_day_avg
```

---

# 6. How to think when looking at the chart viewer

When viewing a day, do not ask:

```text
Which indicator says buy?
```

Ask:

```text
What is the market state?
```

A useful visual inspection sequence:

## Step 1 — Where are we in the day?

Look at:

```text
minute_from_open
bar_index_in_session
```

Questions:

```text
Is this the open?
After OR30?
After OR60?
Lunch?
Power hour?
```

---

## Step 2 — What is the session shape?

Look at:

```text
running_session_high
running_session_low
close_location_in_session_range
session_range_so_far_pts
```

Questions:

```text
Is price pressing high of day?
Pressing low of day?
Chopping in the middle?
Has the day already expanded?
```

---

## Step 3 — Where is price relative to yesterday?

Look at:

```text
prev_day_high
prev_day_low
prev_day_close
gap_from_prev_close_pts
```

Questions:

```text
Did we gap up or down?
Are we above yesterday's range?
Inside yesterday's range?
Testing yesterday's high/low?
```

---

## Step 4 — Where is price relative to the opening range?

Look at:

```text
or30_high
or30_low
or60_high
or60_low
or30_complete
or60_complete
```

Questions:

```text
Has the opening range completed?
Is price breaking out?
Is price failing back inside?
Did the breakout have follow-through?
```

---

## Step 5 — Where is price relative to VWAP?

Look at:

```text
vwap
dist_to_vwap_pts
```

Questions:

```text
Is price above VWAP?
Below VWAP?
Chopping around VWAP?
Far extended from VWAP?
```

---

## Step 6 — Is movement expanding?

Look at:

```text
bar_range_pts
true_range_pts
atr14_pts
```

Questions:

```text
Is this a large candle relative to recent movement?
Is volatility expanding or dead?
Would a fixed stop be too tight here?
```

---

## Step 7 — Is volume participating?

Look at:

```text
volume
rolling_volume_20_bars
relative_volume_20
```

Questions:

```text
Is volume confirming the move?
Is the breakout happening on weak volume?
Is there a sudden participation spike?
```

---

# 7. Example mental models for first deterministic setups

## Setup idea A — OR30 breakout continuation

Do not think:

```text
price broke OR30 high, buy.
```

Think:

```text
The opening range is complete.
Price broke above OR30 high.
Price is above VWAP.
The breakout bar has decent range expansion.
Volume is not dead.
The day has not already overexpanded too much.
Higher timeframe context later should not disagree.
```

This becomes a testable rule.

---

## Setup idea B — Failed OR30 breakout

Do not think:

```text
breakout failed, reverse.
```

Think:

```text
Price broke OR30 high.
It could not hold above the level.
It returned back inside the opening range.
It may also lose VWAP.
The failed breakout may trap late longs.
```

This becomes a separate setup, with separate statistics.

---

## Setup idea C — Previous day high continuation

Do not think:

```text
price crossed previous high, buy.
```

Think:

```text
Price is interacting with yesterday's high.
Is this acceptance above the level or rejection?
Is VWAP supportive?
Is volume expanding?
Was there a gap?
Is the opening range aligned with the break?
```

Again, this becomes a testable rule.

---

# 8. What the features are not

The current features are not signals yet.

They do not mean:

```text
buy
sell
take profit
stop out
re-enter
```

They mean:

```text
here is the state of the market at this bar
```

A signal is a rule that uses these state variables.

Example:

```text
If OR30 is complete
and close crosses above OR30 high
and close > VWAP
and relative_volume_20 > 1.2
and bar_range_pts > atr14_pts * 0.8
then candidate long signal
```

That rule still needs a backtest.

The feature table gives us the raw ingredients.

The signal logic is the recipe.

---

# 9. Current rebuild cheat sheet

From repo root:

```powershell
cd $HOME\Desktop\spy_research
```

Validate raw data:

```powershell
uv run python scripts\validate_data.py
```

Build processed bars:

```powershell
uv run python scripts\build_processed_data.py
```

Build all feature tables:

```powershell
uv run python scripts\build_features.py --timeframe 1m --csv
uv run python scripts\build_features.py --timeframe 5m --csv
uv run python scripts\build_features.py --timeframe 30m --csv
uv run python scripts\build_features.py --timeframe 1h --csv
```

Run tests:

```powershell
uv run pytest
```

Start chart backend:

```powershell
uv run uvicorn apps.chart_viewer.backend.main:app --reload --port 8000
```

Start chart frontend:

```powershell
cd apps\chart_viewer\frontend
npm run dev
```

Open:

```text
http://localhost:5173
```

---

# 10. Recommended next workflow improvement

Right now, rebuilding all features requires several commands.

Later, we should add one convenience script, such as:

```text
scripts/rebuild_all.py
```

Possible command:

```powershell
uv run python scripts\rebuild_all.py --csv
```

It would run:

```text
validate raw data
build processed bars
build 1m features
build 5m features
build 30m features
build 1h features
run key sanity checks
```

But it is good that we did not start there.

Keeping the steps separate first made the workflow easier to validate.

---

# 11. Project discipline reminder

The current system now has a clean research pipeline:

```text
raw data
processed bars
feature tables
visual inspection
baseline behavior study
deterministic signal design
underlying backtest
forward test
option mapping
execution rules
```

Do not jump from feature overlays directly to trading.

The next research layer should be:

```text
Phase 2 baseline intraday behavior study
```

The goal is to answer questions like:

```text
How often does SPY break OR30 high?
How often does it continue after breaking OR30 high?
Does VWAP alignment matter?
Does relative volume matter?
Does gap context matter?
What is typical MFE/MAE after these events?
```

Once those statistics exist, Phase 3 deterministic signal design becomes much more grounded.
