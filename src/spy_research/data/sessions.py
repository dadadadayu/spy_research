from __future__ import annotations

import pandas as pd

from spy_research.config import RTH_START, RTH_END


def filter_regular_trading_hours(
    df: pd.DataFrame,
    *,
    start: str = RTH_START,
    end: str = RTH_END,
    timestamp_col: str = "timestamp",
) -> pd.DataFrame:
    """Keep regular trading hours only: start <= timestamp < end.

    The FirstRateData readme says timestamps are US Eastern. We keep them naive
    for now and treat them as Eastern exchange timestamps.
    """
    out = df.copy()
    out[timestamp_col] = pd.to_datetime(out[timestamp_col], errors="raise")

    start_time = pd.to_datetime(start).time()
    end_time = pd.to_datetime(end).time()
    times = out[timestamp_col].dt.time

    mask = (times >= start_time) & (times < end_time)
    return out.loc[mask].reset_index(drop=True)


def add_session_date(df: pd.DataFrame, timestamp_col: str = "timestamp") -> pd.DataFrame:
    """Add a `session_date` column based on the timestamp date."""
    out = df.copy()
    out[timestamp_col] = pd.to_datetime(out[timestamp_col], errors="raise")
    out["session_date"] = out[timestamp_col].dt.date
    return out
