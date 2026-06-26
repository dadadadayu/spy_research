from __future__ import annotations

import numpy as np
import pandas as pd


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace(0, np.nan)
    return numerator / denominator


def add_running_session_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add running high/low/range and location features within each session."""
    if "session_date" not in df.columns:
        raise ValueError("add_running_session_features requires session_date. Run add_time_features first.")

    out = df.copy()
    grouped = out.groupby("session_date", sort=False)

    out["session_open"] = grouped["open"].transform("first")
    out["running_session_high"] = grouped["high"].cummax()
    out["running_session_low"] = grouped["low"].cummin()
    out["session_range_so_far_pts"] = out["running_session_high"] - out["running_session_low"]
    out["dist_from_session_open_pts"] = out["close"] - out["session_open"]
    out["dist_from_running_high_pts"] = out["close"] - out["running_session_high"]
    out["dist_from_running_low_pts"] = out["close"] - out["running_session_low"]
    out["close_location_in_session_range"] = _safe_divide(
        out["close"] - out["running_session_low"],
        out["session_range_so_far_pts"],
    )

    prev_running_high = grouped["high"].cummax().groupby(out["session_date"], sort=False).shift(1)
    prev_running_low = grouped["low"].cummin().groupby(out["session_date"], sort=False).shift(1)
    out["new_session_high"] = prev_running_high.isna() | (out["high"] > prev_running_high)
    out["new_session_low"] = prev_running_low.isna() | (out["low"] < prev_running_low)

    return out


def add_previous_day_levels(df: pd.DataFrame) -> pd.DataFrame:
    """Add previous RTH session OHLC levels and distance-to-level features."""
    if "session_date" not in df.columns:
        raise ValueError("add_previous_day_levels requires session_date. Run add_time_features first.")
    if "session_open" not in df.columns:
        df = add_running_session_features(df)

    out = df.copy()

    daily = (
        out.groupby("session_date", sort=True)
        .agg(
            day_open=("open", "first"),
            day_high=("high", "max"),
            day_low=("low", "min"),
            day_close=("close", "last"),
        )
        .sort_index()
    )
    previous = daily.shift(1)

    out["prev_day_open"] = out["session_date"].map(previous["day_open"])
    out["prev_day_high"] = out["session_date"].map(previous["day_high"])
    out["prev_day_low"] = out["session_date"].map(previous["day_low"])
    out["prev_day_close"] = out["session_date"].map(previous["day_close"])
    out["prev_day_range_pts"] = out["prev_day_high"] - out["prev_day_low"]

    out["gap_from_prev_close_pts"] = out["session_open"] - out["prev_day_close"]
    out["gap_from_prev_close_pct"] = _safe_divide(out["gap_from_prev_close_pts"], out["prev_day_close"])

    out["dist_to_prev_day_high_pts"] = out["close"] - out["prev_day_high"]
    out["dist_to_prev_day_low_pts"] = out["close"] - out["prev_day_low"]
    out["dist_to_prev_day_close_pts"] = out["close"] - out["prev_day_close"]
    out["above_prev_day_high"] = out["close"] > out["prev_day_high"]
    out["below_prev_day_low"] = out["close"] < out["prev_day_low"]

    return out


def add_opening_range_features(df: pd.DataFrame, *, windows: tuple[int, ...] = (30, 60)) -> pd.DataFrame:
    """Add opening range levels for selected minute windows.

    Opening range values are only exposed once the corresponding window is
    complete. Before completion, level columns remain NA and `or*_complete` is false.
    """
    required = {"session_date", "minute_from_open"}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"add_opening_range_features requires columns: {missing}")

    out = df.copy()

    for window in windows:
        prefix = f"or{window}"
        mask = (out["minute_from_open"] >= 0) & (out["minute_from_open"] < window)
        opening = (
            out.loc[mask]
            .groupby("session_date", sort=True)
            .agg(or_high=("high", "max"), or_low=("low", "min"))
        )

        complete = out["minute_from_open"] >= window
        high = out["session_date"].map(opening["or_high"]).where(complete)
        low = out["session_date"].map(opening["or_low"]).where(complete)

        out[f"{prefix}_high"] = high
        out[f"{prefix}_low"] = low
        out[f"{prefix}_range_pts"] = high - low
        out[f"{prefix}_mid"] = (high + low) / 2
        out[f"{prefix}_complete"] = complete & high.notna() & low.notna()
        out[f"dist_to_{prefix}_high_pts"] = out["close"] - high
        out[f"dist_to_{prefix}_low_pts"] = out["close"] - low
        out[f"above_{prefix}_high"] = out["close"] > high
        out[f"below_{prefix}_low"] = out["close"] < low

    return out
