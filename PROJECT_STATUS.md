# Project Status

## What exists now

- `uv` Python project scaffold
- `.python-version` pinned to `3.12.13`
- `pyproject.toml` restricted to Python `>=3.12,<3.13`
- raw SPY 1-minute CSV under `data/raw/`
- vendor sample files moved from typo folder `data/procesed/` to `data/vendor_sample/`
- scripts for validation and processed-bar generation
- starter notebooks
- modular `src/spy_research` package

## Data findings from uploaded zip

Raw file:

- `data/raw/SPY_1min_firstratedata.csv`
- 207,824 rows
- columns: `timestamp, open, high, low, close, volume`
- timestamp range: `2022-09-30 04:00:00` to `2023-09-29 19:48:00`
- 251 trading dates
- no missing values
- no duplicate timestamps
- timestamps are monotonic increasing
- no basic OHLC consistency violations found
- includes extended hours: earliest 04:00, latest 20:00

Regular trading hours subset:

- 97,744 rows
- normal full sessions have 390 one-minute bars
- 3 dates are shorter/incomplete:
  - 2022-11-25: 330 bars, expected half-day behavior
  - 2023-06-05: 386 bars, likely missing a few one-minute bars
  - 2023-07-03: 308 bars, expected half-day behavior

Vendor sample files:

- original folder was misspelled `data/procesed/`
- these files are from 2026-03-09 to 2026-03-23
- they are not derived from the raw 2022-2023 file
- they should not be treated as our project's processed output

## Next recommended step

Run:

```powershell
uv run python scripts\validate_data.py
uv run python scripts\build_processed_data.py
```

Then open:

```text
notebooks/00_data_check.ipynb
```
