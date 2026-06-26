from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Allow running from repo root without package installation edge cases.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from spy_research.config import FEATURES_DIR, PROCESSED_DIR
from spy_research.data.loaders import load_processed_parquet
from spy_research.features.build import build_f1_features

VALID_TIMEFRAMES = {"1m", "5m", "30m", "1h"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build derived SPY feature tables from processed bars.")
    parser.add_argument(
        "--timeframe",
        choices=sorted(VALID_TIMEFRAMES),
        default="5m",
        help="Processed timeframe to build features for. Default: 5m.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Optional explicit input Parquet path. Defaults to data/processed/spy_<timeframe>_rth.parquet.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional explicit output Parquet path. Defaults to data/features/spy_<timeframe>_rth_features.parquet.",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Also write a CSV copy for manual inspection.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = args.input or PROCESSED_DIR / f"spy_{args.timeframe}_rth.parquet"
    output_path = args.output or FEATURES_DIR / f"spy_{args.timeframe}_rth_features.parquet"

    bars = load_processed_parquet(input_path)
    features = build_f1_features(bars)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(output_path, index=False)
    print(f"Wrote {output_path} ({len(features):,} rows, {len(features.columns):,} columns)")

    if args.csv:
        csv_path = output_path.with_suffix(".csv")
        features.to_csv(csv_path, index=False)
        print(f"Wrote {csv_path} ({len(features):,} rows, {len(features.columns):,} columns)")


if __name__ == "__main__":
    main()
