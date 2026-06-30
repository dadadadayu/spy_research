# FEATURE_SPEC.md

## Purpose

This document defines the first feature and indicator schema for the SPY research project.

The goal is not to create a large collection of retail-style indicators. The goal is to derive a clean, staged set of market state variables from OHLCV data that supports:

1. Phase 2 baseline intraday behavior study.
2. Phase 3 deterministic fixed-rule signal design.
3. Later ML / deep-learning event datasets.
4. Chart viewer overlays and signal debugging.

This feature layer should make the project more rigorous, not more cluttered.

## Current source data

Current verified processed example:

```text
spy_5m_rth.parquet
```

Observed schema:

```text
timestamp    datetime64
open         float64
high         float64
low          float64
close        float64
volume       int64
```

Observed row count:

```text
19,569
```

Observed timestamp range:

```text
2022-09-30 09:30:00 to 2023-09-29 15:55:00
```

The current processed files are regular trading hours bars.

Important convention:

```text
RTH session = 09:30 <= timestamp < 16:00
```

## Timestamp and leakage convention

The processed bars are left-labeled.

Example:

```text
timestamp = 09:30
```

means the bar starting at 09:30.

For research, the default assumption is **bar-close decision timing**:

```text
Features derived from a bar's open/high/low/close/volume are only available after that bar completes.
```

Therefore:

- A 5m bar labeled `09:30` is available after the 09:30-09:35 interval completes.
- A signal generated from that bar should be treated as actionable no earlier than the next bar unless the backtest explicitly models bar-close execution.
- Future ML datasets must avoid using features that would not be known at the prediction time.

Recommended future implementation detail:

```text
signal_timestamp = bar timestamp
decision_timestamp = bar timestamp + timeframe duration
```

The first deterministic research can keep this simple, but the convention must stay explicit.

## Feature design principles

Prefer state variables over indicator clutter.

Good features:

- describe time of day,
- describe location relative to important levels,
- describe range expansion / volatility,
- describe trend context,
- describe volume participation,
- are available at prediction time,
- are useful for both rules and later ML.

Avoid early feature bloat:

- many overlapping oscillators,
- many redundant moving averages,
- indicators without a hypothesis,
- features that secretly use future information,
- features that exist only because they are common in retail trading platforms.

## Recommended output locations

Keep raw and processed bars separate from derived feature tables.

Recommended future folders:

```text
data/
  raw/
  processed/
  features/
```

Recommended first feature outputs:

```text
data/features/spy_5m_rth_features.parquet
data/features/spy_30m_rth_features.parquet
data/features/spy_1h_rth_features.parquet
```

Optional CSV copies for inspection:

```text
data/features/spy_5m_rth_features.csv
```

If files remain small, they can be tracked in Git for Mac/Windows portability.

## Research artifact hierarchy

Keep the main research artifacts separated by responsibility.

```text
raw OHLCV
→ processed OHLCV
→ shared feature tables
→ setup/version-specific candidate signals
→ setup/version-specific labeled signals
→ ML event datasets / backtests / reports
```

Strict source-of-truth hierarchy:

```text
data/raw/
    Immutable original market data. Do not overwrite.

data/processed/
    Cleaned/resampled OHLCV bars used by research.

data/features/
    Canonical derived market-state tables. Shared across hypotheses.

outputs/signals/
    Setup/version-specific signal and label artifacts.

outputs/reports/, outputs/backtests/, outputs/ml/
    Analysis, evaluation, and model artifacts derived from the above.
```

Important rule:

```text
Feature tables are shared.
Candidate signal files and labeled signal files are hypothesis/setup-specific.
```

Do not create a separate feature table for every hypothesis by default. If a new hypothesis needs reusable information that is known at decision time, add a clearly named feature to the shared feature table. If a feature is experimental or may change meaning, version it or keep it in a temporary experiment artifact until it is stable.

## Signal and label artifact rules

A setup is a fixed rule recipe. A signal is one timestamp where that recipe fires.

Signal detection should normally:

```text
load shared feature table
loop through all eligible feature rows
apply one fixed setup/version rule
write only candidate signal rows
```

Recommended candidate signal path:

```text
outputs/signals/<setup_name>/<setup_version>/candidate_signals.csv
```

Recommended candidate signal columns:

| Column | Description |
|---|---|
| `signal_time` | Bar timestamp that generated the signal. |
| `decision_time` | Earliest realistic decision/action time. |
| `setup_name` | Stable setup family name, e.g. `or30_breakout_long`. |
| `setup_version` | Version such as `v1`. |
| `side` | `long` or `short`. |
| `entry_reference_price` | Price used for labeling/backtest reference. |
| `timeframe` | Source timeframe, e.g. `5m`. |
| `notes` | Optional human-readable rule/context note. |

Labeling should normally:

```text
load shared feature/bar table
load candidate signal rows
loop through signal rows only
look forward according to the label definition
append future outcome fields
write labeled signal rows
```

Recommended labeled signal path:

```text
outputs/signals/<setup_name>/<setup_version>/labeled_signals.csv
```

Recommended labeled signal columns include all candidate signal columns plus:

| Column | Description |
|---|---|
| `label_name` | Exact label definition name. |
| `label_value` | Binary, categorical, or numeric label result. |
| `lookahead_bars` | Maximum future bars checked. |
| `target_pts` / `target_pct` | Target definition when relevant. |
| `stop_pts` / `stop_pct` | Stop definition when relevant. |
| `hit_target_before_stop` | Common first binary label. |
| `mfe_pts` | Max favorable excursion after signal. |
| `mae_pts` | Max adverse excursion after signal. |
| `bars_to_target` | Bars until target, if hit. |
| `bars_to_stop` | Bars until stop, if hit. |
| `label_status` | `ok`, `insufficient_future_bars`, or another explicit reason. |

Every candidate signal should eventually receive either a valid label or an explicit `label_status` explaining why it could not be labeled.

A label is a future outcome, not the rule that fired. For example:

```text
signal: setup conditions are true now
label: target hit before stop within N bars afterward
```

## ML dataset rule

ML does not require separate feature/signal/label files, but clean research does. The ML training table should be created from the separated artifacts.

Recommended ML event dataset shape:

```text
one row per candidate signal
+ feature snapshot from signal/decision time
+ label columns from future outcome
```

In ML language:

```text
X = feature columns available at prediction time
y = label column created from future outcome
signal rows = the event universe being scored
```

The signal chooses which timestamps become ML examples. The label says whether those examples worked according to the hypothesis.

## Joined debug and chart-viewer tables

For human inspection, chart overlays, and debugging, it is acceptable to join signals and labels back onto bar/feature data.

Example debug shape:

```text
timestamp | OHLCV | features | signal_marker | label/result_marker
```

This joined table is a convenience artifact, not the canonical research source. The canonical artifacts remain:

```text
data/features/<symbol>_<timeframe>_features.parquet
outputs/signals/<setup_name>/<setup_version>/candidate_signals.csv
outputs/signals/<setup_name>/<setup_version>/labeled_signals.csv
```

## Naming conventions

Use snake_case.

Use clear units in names:

```text
*_pts       price points
*_pct       percentage or percent move
*_bars      number of bars
*_atr       value normalized by ATR
```

Use explicit source/context prefixes:

```text
prev_day_*
or30_*
or60_*
session_*
running_*
vwap_*
ema20_5m_*
ema20_30m_*
ctx_30m_*
ctx_1h_*
```

Boolean columns should use:

```text
is_*
has_*
above_*
below_*
```

Avoid ambiguous names like:

```text
trend
range
signal
score
```

Prefer:

```text
ema20_5m_slope_pts
session_range_so_far_pts
or30_breakout_up
candidate_orb_long_v1
```

## Feature groups

### Group A — Base OHLCV schema

These columns come directly from source bars.

| Column | Type | Description | Phase use |
|---|---:|---|---|
| `timestamp` | datetime | Bar timestamp. Current bars are left-labeled. | All phases |
| `open` | float | Bar open. | All phases |
| `high` | float | Bar high. | All phases |
| `low` | float | Bar low. | All phases |
| `close` | float | Bar close. | All phases |
| `volume` | numeric | Bar volume. | All phases |

### Group B — Session and clock features

Purpose:

Time-of-day matters heavily in intraday SPY behavior. These features support Phase 2 session profiling, Phase 3 filters, and later ML.

| Column | Type | Description |
|---|---:|---|
| `session_date` | date/string | Trading session date based on timestamp date. |
| `day_of_week` | int | Monday=0, Friday=4. |
| `time_hhmm` | string | Human-readable time such as `09:35`. |
| `minute_of_day` | int | Minutes since midnight. |
| `minute_from_open` | int | Minutes since 09:30. |
| `bar_index_in_session` | int | 0 for first RTH bar, then increasing. |
| `is_opening_5m` | bool | True for first 5 minutes of RTH. |
| `is_opening_15m` | bool | True for first 15 minutes of RTH. |
| `is_opening_30m` | bool | True for first 30 minutes of RTH. |
| `is_opening_60m` | bool | True for first 60 minutes of RTH. |
| `is_lunch_period` | bool | Approx. 11:30-13:30 ET. |
| `is_power_hour` | bool | Approx. 15:00-16:00 ET. |

First implementation priority:

```text
session_date
minute_from_open
bar_index_in_session
is_opening_30m
is_opening_60m
```

### Group C — Previous session reference levels

Purpose:

Previous day high/low/close are important anchors for intraday SPY. These features support both visual overlays and deterministic setups.

| Column | Type | Description |
|---|---:|---|
| `prev_day_high` | float | Previous RTH session high. |
| `prev_day_low` | float | Previous RTH session low. |
| `prev_day_close` | float | Previous RTH session close. |
| `prev_day_open` | float | Previous RTH session open. |
| `prev_day_range_pts` | float | `prev_day_high - prev_day_low`. |
| `gap_from_prev_close_pts` | float | `session_open - prev_day_close`. |
| `gap_from_prev_close_pct` | float | Gap divided by previous close. |
| `dist_to_prev_day_high_pts` | float | `close - prev_day_high`. |
| `dist_to_prev_day_low_pts` | float | `close - prev_day_low`. |
| `dist_to_prev_day_close_pts` | float | `close - prev_day_close`. |
| `above_prev_day_high` | bool | `close > prev_day_high`. |
| `below_prev_day_low` | bool | `close < prev_day_low`. |

Chart overlays:

```text
prev_day_high
prev_day_low
prev_day_close
```

First deterministic setup support:

- previous day high break and continuation,
- previous day low break and continuation,
- gap continuation / gap fade context.

Leakage note:

Previous day levels are safe if calculated only from completed prior sessions.

### Group D — Opening range features

Purpose:

Opening range features directly support Phase 2 behavior study and Phase 3 opening range breakout / failed breakout / reclaim setups.

Recommended opening windows:

```text
5m
15m
30m
60m
```

First priority windows:

```text
30m
60m
```

For each window, define:

| Column | Type | Description |
|---|---:|---|
| `or30_high` | float | First 30-minute high. |
| `or30_low` | float | First 30-minute low. |
| `or30_range_pts` | float | `or30_high - or30_low`. |
| `or30_mid` | float | Midpoint of OR30. |
| `dist_to_or30_high_pts` | float | `close - or30_high`. |
| `dist_to_or30_low_pts` | float | `close - or30_low`. |
| `above_or30_high` | bool | `close > or30_high`. |
| `below_or30_low` | bool | `close < or30_low`. |
| `or30_breakout_up` | bool | First close crossing above OR30 high. |
| `or30_breakout_down` | bool | First close crossing below OR30 low. |

Same pattern can be created for:

```text
or5_*
or15_*
or60_*
```

Leakage note:

An opening range level is only known after the opening window completes.

Therefore:

- `or30_*` should be considered known from 10:00 onward.
- `or60_*` should be considered known from 10:30 onward.

For bars before the range completes, either use nulls or explicitly mark `or30_complete = false`.

Additional columns:

| Column | Type | Description |
|---|---:|---|
| `or30_complete` | bool | True after the OR30 window is complete. |
| `or60_complete` | bool | True after the OR60 window is complete. |

### Group E — Running intraday structure

Purpose:

Describe the shape of the current session as it unfolds.

| Column | Type | Description |
|---|---:|---|
| `session_open` | float | First RTH open of current session. |
| `running_session_high` | float | Highest high so far in current session. |
| `running_session_low` | float | Lowest low so far in current session. |
| `session_range_so_far_pts` | float | Running high minus running low. |
| `dist_from_session_open_pts` | float | `close - session_open`. |
| `dist_from_running_high_pts` | float | `close - running_session_high`. |
| `dist_from_running_low_pts` | float | `close - running_session_low`. |
| `close_location_in_session_range` | float | `(close - running_low) / (running_high - running_low)`. |
| `new_session_high` | bool | Current bar makes new high of day. |
| `new_session_low` | bool | Current bar makes new low of day. |

Chart usefulness:

- helps inspect trend days vs chop days,
- helps identify whether price is pressing highs/lows,
- helps later MAE/MFE analysis.

### Group F — VWAP features

Purpose:

VWAP is a central intraday anchor for SPY. It is useful for visual inspection, deterministic filters, and later ML.

| Column | Type | Description |
|---|---:|---|
| `vwap` | float | Session VWAP using cumulative price-volume. |
| `dist_to_vwap_pts` | float | `close - vwap`. |
| `dist_to_vwap_pct` | float | Distance divided by VWAP. |
| `above_vwap` | bool | `close > vwap`. |
| `vwap_slope_3_bars_pts` | float | VWAP change over 3 bars. |
| `vwap_slope_6_bars_pts` | float | VWAP change over 6 bars. |

Default VWAP price input:

```text
typical_price = (high + low + close) / 3
vwap = cumulative_sum(typical_price * volume) / cumulative_sum(volume)
```

Leakage note:

VWAP is safe if computed cumulatively within the current session up to the current bar.

Chart overlay:

```text
vwap
```

### Group G — Candle shape / price-action features

Purpose:

These features support breakout confirmation, rejection, failed breakout, and later ML event context.

| Column | Type | Description |
|---|---:|---|
| `bar_range_pts` | float | `high - low`. |
| `bar_body_pts` | float | `close - open`. |
| `abs_bar_body_pts` | float | Absolute candle body. |
| `upper_wick_pts` | float | `high - max(open, close)`. |
| `lower_wick_pts` | float | `min(open, close) - low`. |
| `body_to_range_ratio` | float | `abs_body / bar_range`. |
| `close_location_in_bar` | float | `(close - low) / (high - low)`. |
| `close_near_high` | bool | Close location above threshold, e.g. `>= 0.8`. |
| `close_near_low` | bool | Close location below threshold, e.g. `<= 0.2`. |
| `green_bar` | bool | `close > open`. |
| `red_bar` | bool | `close < open`. |

These are useful but should not be over-interpreted alone.

### Group H — Volatility and range features

Purpose:

Breakouts behave differently in dead conditions versus expanding conditions.

| Column | Type | Description |
|---|---:|---|
| `true_range_pts` | float | Max of high-low, abs(high-prev_close), abs(low-prev_close). |
| `atr14_pts` | float | Rolling average of true range, 14 bars. |
| `atr20_pts` | float | Rolling average of true range, 20 bars. |
| `bar_range_vs_atr14` | float | `bar_range_pts / atr14_pts`. |
| `rolling_range_5_bars_pts` | float | High-low range across last 5 bars. |
| `rolling_range_10_bars_pts` | float | High-low range across last 10 bars. |
| `rolling_range_20_bars_pts` | float | High-low range across last 20 bars. |
| `range_expansion_5_vs_20` | float | Recent range relative to longer rolling range. |

First implementation priority:

```text
true_range_pts
atr14_pts
bar_range_vs_atr14
rolling_range_10_bars_pts
```

### Group I — Trend / context features

Purpose:

Use light trend context, not moving-average clutter.

Start with one EMA length:

```text
20
```

Possible second length later:

```text
50
```

Same-timeframe features:

| Column | Type | Description |
|---|---:|---|
| `ema20` | float | EMA20 on current dataframe. |
| `dist_to_ema20_pts` | float | `close - ema20`. |
| `dist_to_ema20_pct` | float | Distance divided by EMA20. |
| `ema20_slope_3_bars_pts` | float | EMA20 change over 3 bars. |
| `above_ema20` | bool | `close > ema20`. |

Multi-timeframe context naming:

```text
ctx_30m_close
ctx_30m_ema20
ctx_30m_above_ema20
ctx_30m_ema20_slope_3_bars_pts

ctx_1h_close
ctx_1h_ema20
ctx_1h_above_ema20
ctx_1h_ema20_slope_3_bars_pts
```

Important implementation rule:

When joining 30m/1h context onto 5m bars, use an as-of join that only uses completed higher-timeframe bars.

Do not leak the current unfinished 30m/1h candle into 5m decisions.

### Group J — Volume / participation features

Purpose:

Breakouts with participation are different from breakouts without participation.

| Column | Type | Description |
|---|---:|---|
| `volume` | numeric | Existing source column. |
| `rolling_volume_20_bars` | float | Rolling average volume over 20 bars. |
| `relative_volume_20` | float | `volume / rolling_volume_20_bars`. |
| `cumulative_volume_session` | numeric | Running session volume. |
| `volume_zscore_20` | float | Current volume z-score vs rolling 20 bars. |
| `volume_spike_20` | bool | Relative volume above threshold, e.g. `>= 1.5`. |

Later, after more data:

```text
relative_volume_vs_time_of_day_avg
```

This compares current bar volume to the average volume at the same time of day across previous sessions. This is better than a simple rolling volume average but requires more care.

### Group K — Session summary features

Purpose:

Phase 2 needs daily/session-level summaries before designing fixed rules.

Output:

```text
outputs/reports/session_summary.csv
```

Recommended columns:

| Column | Description |
|---|---|
| `session_date` | Date. |
| `session_open` | First RTH open. |
| `session_high` | RTH high. |
| `session_low` | RTH low. |
| `session_close` | Last RTH close. |
| `session_range_pts` | High-low. |
| `session_return_pts` | Close-open. |
| `session_return_pct` | Close/open - 1. |
| `gap_from_prev_close_pts` | Open - previous close. |
| `gap_from_prev_close_pct` | Gap divided by previous close. |
| `or30_high` | First 30-minute high. |
| `or30_low` | First 30-minute low. |
| `or30_range_pts` | First 30-minute range. |
| `or60_high` | First 60-minute high. |
| `or60_low` | First 60-minute low. |
| `or60_range_pts` | First 60-minute range. |
| `time_of_session_high` | Timestamp/time of day high. |
| `time_of_session_low` | Timestamp/time of day low. |
| `close_location_in_day_range` | `(close - low) / (high - low)`. |
| `broke_or30_high` | Whether session broke OR30 high after OR30 complete. |
| `broke_or30_low` | Whether session broke OR30 low after OR30 complete. |
| `first_or30_break_direction` | `up`, `down`, or `none`. |
| `or30_break_up_continuation_pts` | Max favorable movement after OR30 upside break. |
| `or30_break_down_continuation_pts` | Max favorable movement after OR30 downside break. |

These are descriptive analysis features, not trade signals yet.

### Group L — Analysis-only regime labels

Purpose:

Useful for Phase 2 and later ML regime classification, but must be treated carefully.

These can use full-session information for offline analysis:

| Column | Description |
|---|---|
| `trend_day_up_label` | Full-session descriptive label. |
| `trend_day_down_label` | Full-session descriptive label. |
| `chop_day_label` | Full-session descriptive label. |
| `large_gap_day_label` | Descriptive label. |
| `inside_day_label` | Descriptive label. |
| `or30_continuation_day_label` | Descriptive label. |

Warning:

These labels may use future information and are **not live features**.

Use them for analysis, grouping, and ML label research only.

## First deterministic signal support

The first Phase 3 signals should probably be built around a small subset of features:

### Candidate A — OR30 breakout continuation

Hypothesis:

SPY may continue directionally after breaking the first 30-minute range when VWAP, volume, and higher-timeframe context agree.

Required features:

```text
or30_high
or30_low
or30_complete
above_or30_high
below_or30_low
or30_breakout_up
or30_breakout_down
vwap
above_vwap
dist_to_vwap_pts
relative_volume_20
atr14_pts
bar_range_vs_atr14
ctx_30m_above_ema20
ctx_1h_above_ema20
```

Possible long rule skeleton:

```text
after 10:00
close crosses above or30_high
close > vwap
relative_volume_20 >= threshold
bar_range_vs_atr14 >= threshold
30m/1h context not bearish
```

### Candidate B — Failed OR30 breakout reclaim

Hypothesis:

Failed breaks of the opening range may create stronger reversal/reclaim opportunities when price rejects the break and returns through VWAP or the OR level.

Required features:

```text
or30_high
or30_low
or30_breakout_up
or30_breakout_down
dist_to_or30_high_pts
dist_to_or30_low_pts
above_vwap
below_vwap
close_location_in_bar
upper_wick_pts
lower_wick_pts
body_to_range_ratio
```

### Candidate C — Previous day level break

Hypothesis:

Breaks of previous day high/low may continue when aligned with intraday VWAP and range expansion.

Required features:

```text
prev_day_high
prev_day_low
prev_day_close
above_prev_day_high
below_prev_day_low
dist_to_prev_day_high_pts
dist_to_prev_day_low_pts
gap_from_prev_close_pts
vwap
above_vwap
relative_volume_20
atr14_pts
ctx_30m_above_ema20
ctx_1h_above_ema20
```

## Chart viewer feature mapping

The chart viewer should not compute core research features itself. It should display features computed by Python.

Recommended overlay priorities:

### Chart viewer v1

| Overlay | Source feature |
|---|---|
| Volume pane | `volume` |
| Previous day high | `prev_day_high` |
| Previous day low | `prev_day_low` |
| Previous day close | `prev_day_close` |
| OR30 high | `or30_high` |
| OR30 low | `or30_low` |
| VWAP | `vwap` |
| EMA20 | `ema20` |
| Session separator | `session_date` |

### Chart viewer v2

| Overlay | Source feature |
|---|---|
| OR60 high/low | `or60_high`, `or60_low` |
| Signal markers | `outputs/signals/*.csv` |
| Entry/stop/target lines | backtest output |
| Jump to signal timestamp | signal log |
| Selected bar feature panel | feature table row |

### Chart viewer v3

| Overlay | Source feature |
|---|---|
| SPY + option comparison | option mapping output |
| Option bid/ask spread | option data slice |
| Option PnL path | option mapping/backtest output |

## Recommended implementation modules

Add these modules gradually.

```text
src/spy_research/features/time.py
src/spy_research/features/levels.py
src/spy_research/features/vwap.py
src/spy_research/features/volatility.py
src/spy_research/features/trend.py
src/spy_research/features/volume.py
src/spy_research/features/build.py
src/spy_research/features/schema.py
```

Suggested responsibilities:

| Module | Responsibility |
|---|---|
| `time.py` | session date, minute from open, bar index, time flags. |
| `levels.py` | previous day levels, opening ranges, running session structure. |
| `vwap.py` | session VWAP and VWAP distances. |
| `volatility.py` | true range, ATR, rolling ranges, range expansion. |
| `trend.py` | EMA and EMA slope features. |
| `volume.py` | rolling volume, relative volume, volume spikes. |
| `build.py` | high-level feature-building pipeline. |
| `schema.py` | feature column constants and grouped feature lists. |

Recommended script:

```text
scripts/build_features.py
```

Expected usage:

```powershell
uv run python scripts\build_features.py --timeframe 5m
```

Expected output:

```text
data/features/spy_5m_rth_features.parquet
```

## First implementation milestone

Do not implement every feature at once.

### Milestone F1 — Phase 2 feature foundation

Implement:

```text
session_date
minute_from_open
bar_index_in_session
session_open
running_session_high
running_session_low
session_range_so_far_pts
close_location_in_session_range
prev_day_high
prev_day_low
prev_day_close
gap_from_prev_close_pts
or30_high
or30_low
or30_range_pts
or30_complete
or60_high
or60_low
or60_range_pts
or60_complete
vwap
dist_to_vwap_pts
bar_range_pts
true_range_pts
atr14_pts
relative_volume_20
```

Why:

This is enough for:

- baseline intraday behavior study,
- first chart viewer overlays,
- opening range breakout hypothesis,
- previous day level hypothesis,
- later ML event datasets.

### Milestone F2 — Trend/context foundation

Implement:

```text
ema20
dist_to_ema20_pts
ema20_slope_3_bars_pts
above_ema20
ctx_30m_ema20
ctx_30m_above_ema20
ctx_1h_ema20
ctx_1h_above_ema20
```

Why:

This supports higher-timeframe confirmation without adding many indicators.

### Milestone F3 — Signal support features

Implement:

```text
or30_breakout_up
or30_breakout_down
above_prev_day_high
below_prev_day_low
close_near_high
close_near_low
volume_spike_20
bar_range_vs_atr14
```

Why:

These directly support first deterministic fixed-rule signals.

## Testing requirements

Feature code needs tests before it becomes a foundation for signals.

Recommended tests:

```text
tests/test_features_time.py
tests/test_features_levels.py
tests/test_features_vwap.py
tests/test_features_volatility.py
```

Test examples:

- session date is correct,
- minute from open starts at 0,
- previous day levels do not use current day data,
- OR30 values are null/incomplete before 10:00 and complete after,
- VWAP starts correctly from first bar,
- ATR does not use future bars,
- feature output row count matches input row count.

## What not to build yet

Do not prioritize these yet:

```text
RSI
MACD
Stochastic
CCI
ADX
Ichimoku
large indicator libraries
dozens of moving average combinations
```

These are not forbidden forever. They are simply lower priority than structural intraday features.

## Summary

First feature goal:

```text
Build a clean SPY intraday state table, not an indicator pile.
```

Core artifact rule:

```text
Shared feature table = reusable market-state source for hypotheses.
Candidate signals = setup/version-specific moments where fixed rules fire.
Labeled signals = those same moments plus future outcomes.
ML event dataset = feature snapshot at signal time plus label.
```

The best immediate feature families are:

```text
time/session
previous day levels
opening range
running session structure
VWAP
range/volatility
light trend context
volume participation
```

These features directly support:

```text
Phase 2 baseline behavior study
Phase 3 deterministic signal design
future ML event datasets
chart viewer overlays
```
