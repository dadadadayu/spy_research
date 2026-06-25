from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Allow running from repo root without package installation edge cases.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from spy_research.config import RAW_SPY_1M_CSV, PROCESSED_DIR
from spy_research.data.loaders import load_raw_spy_1m
from spy_research.data.sessions import filter_regular_trading_hours
from spy_research.features.resample import build_standard_timeframes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build processed SPY bars from raw 1-minute CSV.")
    parser.add_argument(
        "--include-extended",
        action="store_true",
        help="Keep premarket/after-hours bars. Default is regular trading hours only.",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Also write CSV copies for manual inspection.",
    )
    parser.add_argument(
        "--no-parquet",
        action="store_true",
        help="Skip Parquet output. Useful only if pyarrow is not installed yet.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    bars_1m = load_raw_spy_1m(RAW_SPY_1M_CSV)

    if args.include_extended:
        cleaned = bars_1m
        rth_anchor = False
        session_label = "extended"
    else:
        cleaned = filter_regular_trading_hours(bars_1m)
        rth_anchor = True
        session_label = "rth"

    frames = build_standard_timeframes(cleaned, rth_anchor=rth_anchor)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    for name, df in frames.items():
        if not args.no_parquet:
            parquet_path = PROCESSED_DIR / f"spy_{name}_{session_label}.parquet"
            try:
                df.to_parquet(parquet_path, index=False)
                print(f"Wrote {parquet_path} ({len(df):,} rows)")
            except ImportError as exc:
                raise SystemExit(
                    "Parquet output requires pyarrow. Run `uv sync` first, "
                    "or use `--csv --no-parquet` for temporary CSV-only output."
                ) from exc

        if args.csv:
            csv_path = PROCESSED_DIR / f"spy_{name}_{session_label}.csv"
            df.to_csv(csv_path, index=False)
            print(f"Wrote {csv_path} ({len(df):,} rows)")


if __name__ == "__main__":
    main()
