from __future__ import annotations

from pathlib import Path
import sys

# Allow running from repo root without package installation edge cases.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd

from spy_research.config import RAW_SPY_1M_CSV, REPORTS_DIR, VENDOR_SAMPLE_DIR
from spy_research.data.loaders import load_ohlcv_csv
from spy_research.data.validation import validate_ohlcv, summaries_to_frame
from spy_research.data.sessions import filter_regular_trading_hours


def main() -> None:
    summaries = []

    raw = load_ohlcv_csv(RAW_SPY_1M_CSV)
    summaries.append(validate_ohlcv(raw, name="raw/SPY_1min_firstratedata.csv"))

    rth = filter_regular_trading_hours(raw)
    summaries.append(validate_ohlcv(rth, name="raw/SPY_1min_firstratedata.csv RTH-only"))

    for path in sorted(VENDOR_SAMPLE_DIR.glob("*.csv")):
        df = load_ohlcv_csv(path)
        summaries.append(validate_ohlcv(df, name=f"vendor_sample/{path.name}"))

    report = summaries_to_frame(summaries)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / "data_validation_summary.csv"
    report.to_csv(out_path, index=False)

    print(report.to_string(index=False))
    print()
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
