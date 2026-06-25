from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd


@dataclass(frozen=True)
class DataValidationSummary:
    name: str
    rows: int
    columns: str
    min_timestamp: str
    max_timestamp: str
    unique_dates: int
    missing_values: int
    duplicate_timestamps: int
    timestamp_parse_failures: int
    monotonic_timestamps: bool
    ohlc_high_violations: int
    ohlc_low_violations: int
    min_time: str
    max_time: str


def validate_ohlcv(df: pd.DataFrame, *, name: str) -> DataValidationSummary:
    out = df.copy()
    ts = pd.to_datetime(out["timestamp"], errors="coerce")

    o = pd.to_numeric(out["open"], errors="coerce")
    h = pd.to_numeric(out["high"], errors="coerce")
    l = pd.to_numeric(out["low"], errors="coerce")
    c = pd.to_numeric(out["close"], errors="coerce")

    high_bad = ((h < o) | (h < l) | (h < c)).sum()
    low_bad = ((l > o) | (l > h) | (l > c)).sum()

    return DataValidationSummary(
        name=name,
        rows=len(out),
        columns=", ".join(map(str, out.columns)),
        min_timestamp=str(ts.min()) if ts.notna().any() else "",
        max_timestamp=str(ts.max()) if ts.notna().any() else "",
        unique_dates=int(ts.dt.date.nunique()) if ts.notna().any() else 0,
        missing_values=int(out.isna().sum().sum()),
        duplicate_timestamps=int(ts.duplicated().sum()),
        timestamp_parse_failures=int(ts.isna().sum()),
        monotonic_timestamps=bool(ts.is_monotonic_increasing),
        ohlc_high_violations=int(high_bad),
        ohlc_low_violations=int(low_bad),
        min_time=str(ts.dt.time.min()) if ts.notna().any() else "",
        max_time=str(ts.dt.time.max()) if ts.notna().any() else "",
    )


def summaries_to_frame(summaries: list[DataValidationSummary]) -> pd.DataFrame:
    return pd.DataFrame([asdict(s) for s in summaries])
