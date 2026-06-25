# Data Validation Report

Generated from the uploaded `spy_research.zip`.

## Raw data

`data/raw/SPY_1min_firstratedata.csv`

| Check | Result |
|---|---:|
| Rows | 207,824 |
| Columns | timestamp, open, high, low, close, volume |
| Timestamp range | 2022-09-30 04:00:00 to 2023-09-29 19:48:00 |
| Unique trading dates | 251 |
| Missing values | 0 |
| Duplicate timestamps | 0 |
| Timestamp parse failures | 0 |
| Monotonic timestamps | yes |
| Basic OHLC violations | 0 |
| Earliest intraday time | 04:00 |
| Latest intraday time | 20:00 |

The raw file looks usable.

## Session note

The raw file includes extended hours. For the first deterministic SPY signal layer, the safest default is to build a regular-session dataset first:

```text
09:30 <= timestamp < 16:00
```

The scripts therefore default to RTH-only processing. Extended hours can be included with `--include-extended`.

## RTH check

| Check | Result |
|---|---:|
| RTH rows | 97,744 |
| Non-RTH rows | 110,080 |
| RTH dates | 251 |
| Dates with fewer than 390 RTH one-minute bars | 3 |

Short/incomplete RTH dates:

| Date | RTH bars | Note |
|---|---:|---|
| 2022-11-25 | 330 | expected market half-day |
| 2023-06-05 | 386 | likely missing a few one-minute bars |
| 2023-07-03 | 308 | expected market half-day |

## Uploaded processed/sample files

Your uploaded zip had this folder:

```text
data/procesed/
```

That folder name has a typo. It contained:

```text
SPY_1min_sample.csv
SPY_5min_sample.csv
SPY_30min_sample.csv
SPY_1hour_sample.csv
SPY_1day_sample.csv
_readme_documentation.txt
```

Those files cover `2026-03-09` to `2026-03-23`, while your raw file covers `2022-09-30` to `2023-09-29`.

Conclusion: these are vendor sample files, not processed outputs derived from your raw CSV. I moved them to:

```text
data/vendor_sample/
```

Project-generated processed files should be created under:

```text
data/processed/
```
