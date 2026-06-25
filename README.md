# SPY Research

A serious, profit-oriented SPY intraday quant research project for a solo retail developer.

The strategy is to narrow the battlefield: SPY first, intraday direction first, underlying signal first, options later, execution last. The project also serves as a serious ML / deep-learning learning path, but advanced models must be introduced in the right research order.

## Current focus

Current phase:

```text
Phase 2: Baseline intraday behavior study
```

Current near-term goal:

```text
Generate session-level SPY behavior summaries before building the first serious signal candidate.
```

This project is currently focused on:

- SPY only.
- 1-minute OHLCV raw data.
- Regular trading hours processed data.
- 1m / 5m / 30m / 1h bars.
- Baseline intraday behavior research.
- Deterministic signal prototypes.
- Underlying-only backtests.

ML, deep learning, options mapping, and execution are planned future layers, not abandoned goals.

## Repo layout

```text
spy_research/
├─ AGENTS.md
├─ PROJECT_PLAN.md
├─ README.md
├─ pyproject.toml
├─ uv.lock
├─ .python-version
│
├─ data/
│  ├─ raw/
│  └─ processed/
│
├─ scripts/
├─ src/spy_research/
├─ notebooks/
├─ outputs/
├─ tests/
└─ docs/
```

## Environment

This repo uses `uv`.

Set up or refresh the environment:

```powershell
uv sync
```

Run the main checks:

```powershell
uv run python scripts\validate_data.py
uv run python scripts\build_processed_data.py
uv run pytest
```

Start JupyterLab:

```powershell
uv run jupyter lab
```

When adding Python packages:

```powershell
uv add <package>
```

Commit both:

```text
pyproject.toml
uv.lock
```

Do not commit `.venv/`.

## Data

For the current SPY-only dataset, raw and processed data files are small enough to track in Git so the repo can move between Mac, Windows, home, and work.

Current important files:

```text
data/raw/SPY_1min_firstratedata.csv
data/processed/spy_1m_rth.parquet
data/processed/spy_5m_rth.parquet
data/processed/spy_30m_rth.parquet
data/processed/spy_1h_rth.parquet
```

If the data later expands into multi-year, multi-symbol, or options-chain data, the project should move to a separate data-management strategy instead of committing everything.

## Documentation map

- `README.md` — short human onboarding and setup.
- `AGENTS.md` — Codex / AI-agent operating rules.
- `PROJECT_PLAN.md` — roadmap, current phase, and progress log.
- `docs/DATA_VALIDATION_REPORT.md` — historical data-validation snapshot.

## Next milestone

Build the baseline intraday behavior study.

First target output:

```text
outputs/reports/session_summary.csv
```

Useful columns:

- date,
- session open/high/low/close,
- full-day range,
- first 30-minute range,
- first 60-minute range,
- gap from previous close,
- close location inside daily range,
- time of high,
- time of low.
