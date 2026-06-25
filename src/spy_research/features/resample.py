from __future__ import annotations

import pandas as pd


OHLCV_AGG = {
    "open": "first",
    "high": "max",
    "low": "min",
    "close": "last",
    "volume": "sum",
}


def resample_ohlcv(
    df: pd.DataFrame,
    timeframe: str,
    *,
    timestamp_col: str = "timestamp",
    rth_anchor: bool = True,
) -> pd.DataFrame:
    """Resample OHLCV bars.

    For RTH data, `rth_anchor=True` anchors bars to 09:30 so 30m/1h bars
    align as 09:30, 10:00/10:30, etc. This avoids accidental 09:00-10:00
    hourly bars when the data begins at 09:30.
    """
    if timeframe in {"1m", "1min", "1T"}:
        return df.sort_values(timestamp_col).reset_index(drop=True)

    out = df.copy()
    out[timestamp_col] = pd.to_datetime(out[timestamp_col], errors="raise")
    out = out.sort_values(timestamp_col).set_index(timestamp_col)

    offset = "30min" if rth_anchor else "0min"

    resampled = (
        out.resample(
            timeframe,
            label="left",
            closed="left",
            origin="start_day",
            offset=offset,
        )
        .agg(OHLCV_AGG)
        .dropna(subset=["open", "high", "low", "close"])
        .reset_index()
    )

    # volume can become float if any input is float; keep numeric but avoid forcing int.
    return resampled


def build_standard_timeframes(df_1m: pd.DataFrame, *, rth_anchor: bool = True) -> dict[str, pd.DataFrame]:
    """Build the project's standard timeframes from 1-minute bars."""
    return {
        "1m": resample_ohlcv(df_1m, "1min", rth_anchor=rth_anchor),
        "5m": resample_ohlcv(df_1m, "5min", rth_anchor=rth_anchor),
        "30m": resample_ohlcv(df_1m, "30min", rth_anchor=rth_anchor),
        "1h": resample_ohlcv(df_1m, "1h", rth_anchor=rth_anchor),
    }
