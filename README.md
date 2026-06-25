# SPY Research

A narrow, modular quant research project focused on SPY intraday signal detection first.

## Current scope

This project is intentionally limited to:

1. SPY underlying data only
2. 1-minute raw OHLCV data
3. cleaned/resampled 1m, 5m, 30m, and 1h bars
4. deterministic signal prototypes
5. underlying-price backtests only

Do **not** add options, broker APIs, live execution, broad universes, or ML until the signal layer is validated.

## Environment

This repo is managed with `uv`.

Recommended Windows location:

```powershell
C:\Users\sanshida\Desktop\spy_research
```

Set up:

```powershell
cd $HOME\Desktop\spy_research

# This zip intentionally does not include .venv, .git, or uv.lock.
# Recreate the lock/environment locally:
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
Remove-Item -Force uv.lock -ErrorAction SilentlyContinue

uv python install
uv sync --extra dev
```

Check imports:

```powershell
uv run python -c "import pandas, numpy, pyarrow, matplotlib; print('core imports ok')"
```

Start JupyterLab:

```powershell
uv run jupyter lab
```

## Data layout

```text
data/
  raw/
    SPY_1min_firstratedata.csv
  vendor_sample/
    SPY_*_sample.csv
    _readme_documentation.txt
  processed/
    generated project outputs go here
```

Important: your uploaded folder had `data/procesed/` with one `s`. I moved those files to `data/vendor_sample/` because they are vendor-provided 2026 sample files, not processed outputs derived from the 2022-2023 raw file.

## Validate data

```powershell
uv run python scripts\validate_data.py
```

This writes a report to:

```text
outputs/reports/data_validation_summary.csv
```

## Build processed bars from raw

Default behavior keeps regular trading hours only, 09:30-16:00 US Eastern timestamps, because it is the cleanest starting point for Stage 1.

```powershell
uv run python scripts\build_processed_data.py
```

Outputs:

```text
data/processed/spy_1m.parquet
data/processed/spy_5m.parquet
data/processed/spy_30m.parquet
data/processed/spy_1h.parquet
```

To include premarket and after-hours bars:

```powershell
uv run python scripts\build_processed_data.py --include-extended
```

To also write CSV copies for manual inspection:

```powershell
uv run python scripts\build_processed_data.py --csv
```

## Research discipline

Keep every candidate setup separated into:

- hypothesis
- features
- label
- decision rule
- evaluation
- implementation complexity

A stopped-out trade that later becomes a winner is not evidence to redesign the whole system. First test whether it indicates stop width, early entry, re-entry, or normal path shape for that setup.
