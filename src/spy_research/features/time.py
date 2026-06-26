from __future__ import annotations

import pandas as pd

MARKET_OPEN_MINUTE = 9 * 60 + 30
LUNCH_START_MINUTE = 11 * 60 + 30
LUNCH_END_MINUTE = 13 * 60 + 30
POWER_HOUR_START_MINUTE = 15 * 60
POWER_HOUR_END_MINUTE = 16 * 60


def add_time_features(df: pd.DataFrame, *, timestamp_col: str = "timestamp") -> pd.DataFrame:
    """Add session and clock features for regular-hours intraday bars.

    Timestamps are treated as exchange-local naive timestamps, matching the
    current processed FirstRateData files.
    """
    out = df.copy()
    out[timestamp_col] = pd.to_datetime(out[timestamp_col], errors="raise")
    out = out.sort_values(timestamp_col).reset_index(drop=True)

    minute_of_day = out[timestamp_col].dt.hour * 60 + out[timestamp_col].dt.minute

    out["session_date"] = out[timestamp_col].dt.date
    out["day_of_week"] = out[timestamp_col].dt.dayofweek.astype("int64")
    out["time_hhmm"] = out[timestamp_col].dt.strftime("%H:%M")
    out["minute_of_day"] = minute_of_day.astype("int64")
    out["minute_from_open"] = (minute_of_day - MARKET_OPEN_MINUTE).astype("int64")
    out["bar_index_in_session"] = out.groupby("session_date", sort=False).cumcount().astype("int64")

    out["is_opening_30m"] = (out["minute_from_open"] >= 0) & (out["minute_from_open"] < 30)
    out["is_opening_60m"] = (out["minute_from_open"] >= 0) & (out["minute_from_open"] < 60)
    out["is_lunch_period"] = (out["minute_of_day"] >= LUNCH_START_MINUTE) & (
        out["minute_of_day"] < LUNCH_END_MINUTE
    )
    out["is_power_hour"] = (out["minute_of_day"] >= POWER_HOUR_START_MINUTE) & (
        out["minute_of_day"] < POWER_HOUR_END_MINUTE
    )

    return out
