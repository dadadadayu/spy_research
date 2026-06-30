# PROJECT_PLAN.md

## Project identity

This is a serious, profit-oriented SPY intraday quant research project for a solo retail developer.

The goal is to find one or a few statistically credible intraday long/short signals that could eventually support real-money SPY options trading.

The project also serves as a deep ML / AI engineering learning path: feature design, labels, leakage, validation, model training, neural networks, and eventually deep learning should be learned and implemented step by step through the research process.

The strategy is to narrow the battlefield:

```text
SPY first
→ intraday direction first
→ underlying signal first
→ options later
→ execution last
```

## Guiding principle

Do not choose between ambition and discipline.

```text
High ambition:
    Real-money relevance, SPY options, ML, neural networks, deep learning.

High discipline:
    Data validation, deterministic baselines, leakage control, time-series validation, reproducible experiments.
```

The project should earn complexity.

## Current status

Last updated: 2026-06-25

Current phase:

```text
Phase 2: Baseline intraday behavior study
```

Completed foundation:

- `uv` Python project scaffold exists.
- `.python-version` is pinned to Python 3.12.x.
- `pyproject.toml` and `uv.lock` define the environment.
- Raw SPY 1-minute CSV exists under `data/raw/`.
- Regular trading hours processed files can be generated.
- 1m / 5m / 30m / 1h processed outputs exist or can be rebuilt.
- Validation and processed-data scripts exist.
- Starter notebooks exist.
- Modular `src/spy_research` package exists.
- Root documentation has been simplified to `README.md`, `AGENTS.md`, `PROJECT_PLAN.md`, and `FEATURE_SPEC.md`.

Important data facts:

- Raw data file: `data/raw/SPY_1min_firstratedata.csv`.
- Raw data rows: 207,824.
- Timestamp range: `2022-09-30 04:00:00` to `2023-09-29 19:48:00`.
- Unique trading dates: 251.
- Missing values: 0.
- Duplicate timestamps: 0.
- Basic OHLC violations found: 0.
- Data includes extended hours.
- Default research dataset should use regular trading hours first.

RTH note:

```text
09:30 <= timestamp < 16:00
```

Known short/incomplete RTH dates:

- 2022-11-25: expected half-day.
- 2023-06-05: likely missing a few one-minute bars.
- 2023-07-03: expected half-day.

## Documentation policy

Root docs should stay minimal and non-overlapping:

```text
README.md
    Human onboarding, setup, quick commands, doc map.

AGENTS.md
    Codex / AI-agent behavior rules and coding/research standards.

PROJECT_PLAN.md
    Project roadmap, current phase, current progress, next milestone.

FEATURE_SPEC.md
    Feature schema, artifact hierarchy, signal/label file rules, chart overlay mapping.
```

Historical or detailed reports should live under:

```text
docs/
outputs/reports/
```

Do not create many overlapping root `.md` files.

## Research artifact rule

The detailed schema and artifact rules live in `FEATURE_SPEC.md`. The high-level rule is:

```text
raw/processed OHLCV = market-data foundation
shared feature tables = reusable market-state data
candidate signals = setup/version-specific rule-fire rows
labeled signals = candidate signals plus future outcomes
ML event datasets = feature snapshots at signal time plus labels
```

Feature tables should be shared across hypotheses whenever possible. Signal and label files should be setup/version-specific so each hypothesis can be evaluated honestly.

## Immediate next milestone

Build the baseline intraday behavior study.

First deliverable:

```text
outputs/reports/session_summary.csv
```

Suggested columns:

- date,
- session open,
- session high,
- session low,
- session close,
- full-day range,
- first 30-minute high,
- first 30-minute low,
- first 30-minute range,
- first 60-minute high,
- first 60-minute low,
- first 60-minute range,
- gap from previous close,
- close location inside daily range,
- time of high,
- time of low.

Second deliverable:

```text
outputs/reports/intraday_profile.csv
```

Possible questions:

- How large is the typical first 30-minute range?
- How large is the typical first 60-minute range?
- How often does SPY continue after breaking morning high/low?
- How often does SPY reverse after breaking morning high/low?
- Which time windows are most directional?
- Which time windows are noisy or mean-reverting?
- Does gap direction matter?
- Does previous day high/low matter?
- Are long and short conditions symmetric?

## Phase 1 — Data foundation

Status: mostly complete.

Goal:

Build trust in the data before building signals.

Work items:

- Validate raw SPY CSV.
- Parse timestamps consistently.
- Confirm OHLCV schema.
- Check duplicate timestamps.
- Check missing values.
- Check OHLC consistency.
- Filter regular trading hours.
- Generate processed 1m, 5m, 30m, and 1h files.
- Confirm resampling correctness.
- Add tests for critical assumptions.

Outputs:

```text
data/processed/spy_1m_rth.parquet
data/processed/spy_5m_rth.parquet
data/processed/spy_30m_rth.parquet
data/processed/spy_1h_rth.parquet
outputs/reports/data_validation_summary.csv
```

Exit criteria:

- Validation script passes.
- Processed files are reproducible.
- Tests pass.
- Data is clean enough for baseline research.

## Phase 2 — Baseline intraday behavior study

Status: current phase.

Goal:

Understand SPY intraday behavior before inventing signals.

Work items:

- Generate session summaries.
- Profile range behavior by time of day.
- Study opening 30-minute and 60-minute ranges.
- Study gap direction.
- Study close location within daily range.
- Study time of high and time of low.
- Identify candidate signal hypotheses from data.

Outputs:

```text
outputs/reports/session_summary.csv
outputs/reports/intraday_profile.csv
notebooks/01_resample_context.ipynb
```

Exit criteria:

- Session-level research outputs are reproducible.
- Observations are written down.
- At least one deterministic signal hypothesis is motivated by data.

## Phase 3 — Deterministic signal prototypes

Goal:

Create first candidate long/short signals using explainable rules.

This phase is not anti-ML. It creates baselines that future ML must beat.

Candidate setup examples:

- Opening range breakout.
- Opening range breakdown.
- Failed breakout and reclaim.
- VWAP reclaim with higher-timeframe context.
- Previous day high/low break and continuation.
- Gap continuation / gap fade with context.

Required framing:

```text
Hypothesis:
Feature:
Label:
Model:
Evaluation:
Decision rule:
Implementation complexity:
Failure modes:
```

Outputs:

```text
outputs/signals/<setup_name>/<setup_version>/candidate_signals.csv
outputs/signals/<setup_name>/<setup_version>/labeled_signals.csv
notebooks/02_signal_prototype.ipynb
src/spy_research/signals/
src/spy_research/labels/
```

Exit criteria:

- Signal output is timestamped.
- Signal uses only information available at signal time.
- Each candidate signal can receive a defined future-outcome label.
- Signal and label artifacts are setup/version-specific.
- Signal can be backtested on SPY underlying.

## Phase 4 — Underlying-only backtest

Goal:

Determine whether the signal has edge on SPY underlying price before using options.

Required metrics:

- trade count,
- win rate,
- average win,
- average loss,
- expectancy,
- profit factor,
- long/short split,
- time-of-day split,
- volatility/regime split,
- MAE,
- MFE,
- bars held.

Outputs:

```text
outputs/backtests/backtest_results.csv
outputs/reports/backtest_summary.csv
notebooks/03_backtest_underlying.ipynb
```

Exit criteria:

- Backtest is reproducible.
- Results are inspectable.
- No options are used yet.
- Weak signals are rejected or revised.

## Phase 5 — Controlled signal refinement

Goal:

Improve signal quality without curve-fitting.

Allowed refinements:

- time-of-day filters,
- volatility filters,
- trend/chop filters,
- higher-timeframe context,
- VWAP distance,
- previous day high/low context,
- gap direction,
- minimum range expansion,
- re-entry as a separate setup.

Outputs:

```text
outputs/experiments/experiment_log.csv
outputs/reports/setup_comparison.csv
```

Exit criteria:

- Each variation has separate stats.
- Re-entry has its own setup name.
- The project can compare versions honestly.

## Phase 6 — Forward signal test without trading

Goal:

Run the signal detector on current/realtime data without placing trades.

Purpose:

- timestamp alignment,
- missing bar detection,
- signal timing,
- runtime stability,
- whether backtest behavior survives live conditions.

Outputs:

```text
outputs/signals/live_forward_signals.csv
outputs/logs/runtime_log.txt
```

Exit criteria:

- Signal bot runs reliably.
- Signals are logged.
- No trades are placed.

## Phase 7 — ML Phase A: dataset and label engineering

Goal:

Prepare for ML correctly before training serious models.

Work items:

- Convert signal logs into event datasets.
- Define target-before-stop labels.
- Define N-bar outcome labels.
- Define time-to-target/time-to-stop labels.
- Build feature snapshots using only information available at prediction time.
- Build time-series splits.
- Add leakage checks.

Outputs:

```text
outputs/ml/event_dataset.csv
outputs/ml/feature_dictionary.md
src/spy_research/ml/
```

Exit criteria:

- Labels are clearly defined.
- Features avoid future leakage.
- Event dataset is reproducible.
- Time-series validation split exists.

## Phase 8 — ML Phase B: classical supervised scoring

Goal:

Use ML to score deterministic candidate setups.

First prediction task:

```text
Given a candidate signal, predict whether target is reached before stop within N bars.
```

Models:

- logistic regression first,
- random forest,
- gradient boosting,
- XGBoost / LightGBM if justified.

Evaluation:

- time-series split,
- walk-forward validation,
- probability calibration,
- precision by probability bucket,
- expectancy by score threshold,
- comparison against deterministic baseline.

Outputs:

```text
outputs/ml/model_scores.csv
outputs/ml/model_evaluation_report.csv
notebooks/04_ml_scoring_baseline.ipynb
```

## Phase 9 — ML Phase C: regime classification

Goal:

Classify market regimes that affect signal quality.

Possible regimes:

- trend vs chop,
- high volatility vs low volatility,
- breakout-friendly vs mean-reverting,
- gap continuation vs gap fade,
- morning expansion vs failed expansion.

Outputs:

```text
outputs/ml/regime_labels.csv
outputs/reports/regime_signal_performance.csv
notebooks/05_regime_classification.ipynb
```

## Phase 10 — ML Phase D: neural network fundamentals

Goal:

Learn neural networks deeply through this project.

Learning sequence:

1. Implement logistic regression manually.
2. Implement a tiny neural network from scratch.
3. Understand forward pass, loss, gradients, and backpropagation.
4. Compare manual implementation to PyTorch.
5. Train a small MLP on engineered event features.
6. Compare against logistic regression and tree models.

Outputs:

```text
notebooks/06_neural_net_from_scratch.ipynb
notebooks/07_pytorch_mlp_signal_scoring.ipynb
src/spy_research/ml/neural/
```

## Phase 11 — ML Phase E: sequence and deep-learning research

Goal:

Explore whether intraday bar sequences contain useful signal information beyond engineered features.

Possible models:

- MLP on engineered features,
- 1D CNN on recent bar windows,
- GRU/LSTM on short intraday sequences,
- small transformer-style model only much later,
- representation learning only if justified.

Outputs:

```text
outputs/ml/deep_model_comparison.csv
notebooks/08_sequence_model_research.ipynb
src/spy_research/ml/deep/
```

Exit criteria:

- Deep learning either adds measurable value or is rejected for this dataset/setup.
- Complexity is justified by results.
- User gains real implementation knowledge.

## Phase 12 — Option mapping

Goal:

Map validated underlying signals to SPY option expressions.

Key rule:

Use the same underlying signal timestamps. Do not invent a new options signal at first.

Compare:

- 0DTE ATM,
- 0DTE slightly OTM,
- 1DTE ATM,
- 1DTE slightly OTM,
- 3DTE ATM,
- 3DTE slightly OTM.

Evaluate:

- spread impact,
- slippage,
- timing sensitivity,
- theta decay,
- liquidity,
- contract selection,
- stop/target behavior.

Data strategy:

Do not collect the full options universe first. Start with targeted option data slices around validated signal timestamps.

## Phase 13 — Execution and risk system

Goal:

Only after signal and option mapping are validated, design execution rules.

Rules to define:

- entry rule,
- stop loss,
- take profit,
- time stop,
- max trades per day,
- max daily loss,
- max daily gain,
- no-trade windows,
- re-entry rules,
- call-it-a-day rules.

Exit criteria:

- Execution logic is separate from signal logic.
- Risk rules are explicit.
- Live trading is not added prematurely.
- Paper/live testing plan is defined before real money.

## Progress log

### 2026-06-25

- Repo documentation consolidated.
- `README.md` reduced to onboarding/setup.
- `AGENTS.md` reduced to AI-agent behavior and standards.
- `PROJECT_PLAN.md` now owns roadmap, current phase, and progress.
- `FEATURE_SPEC.md` owns feature schema, artifact hierarchy, and signal/label file rules.
- Recommendation: move detailed data validation report to `docs/DATA_VALIDATION_REPORT.md`.
- Recommendation: remove root `PROJECT_STATUS.md` after merging status here.
