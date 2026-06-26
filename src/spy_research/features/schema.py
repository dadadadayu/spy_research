from __future__ import annotations

BASE_OHLCV_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]

TIME_FEATURE_COLUMNS = [
    "session_date",
    "day_of_week",
    "time_hhmm",
    "minute_of_day",
    "minute_from_open",
    "bar_index_in_session",
    "is_opening_30m",
    "is_opening_60m",
    "is_lunch_period",
    "is_power_hour",
]

PREVIOUS_DAY_COLUMNS = [
    "prev_day_open",
    "prev_day_high",
    "prev_day_low",
    "prev_day_close",
    "prev_day_range_pts",
    "gap_from_prev_close_pts",
    "gap_from_prev_close_pct",
    "dist_to_prev_day_high_pts",
    "dist_to_prev_day_low_pts",
    "dist_to_prev_day_close_pts",
    "above_prev_day_high",
    "below_prev_day_low",
]

OPENING_RANGE_COLUMNS = [
    "or30_high",
    "or30_low",
    "or30_range_pts",
    "or30_mid",
    "or30_complete",
    "dist_to_or30_high_pts",
    "dist_to_or30_low_pts",
    "above_or30_high",
    "below_or30_low",
    "or60_high",
    "or60_low",
    "or60_range_pts",
    "or60_mid",
    "or60_complete",
    "dist_to_or60_high_pts",
    "dist_to_or60_low_pts",
    "above_or60_high",
    "below_or60_low",
]

RUNNING_SESSION_COLUMNS = [
    "session_open",
    "running_session_high",
    "running_session_low",
    "session_range_so_far_pts",
    "dist_from_session_open_pts",
    "dist_from_running_high_pts",
    "dist_from_running_low_pts",
    "close_location_in_session_range",
    "new_session_high",
    "new_session_low",
]

VWAP_COLUMNS = [
    "vwap",
    "dist_to_vwap_pts",
    "dist_to_vwap_pct",
    "above_vwap",
]

VOLATILITY_COLUMNS = [
    "bar_range_pts",
    "true_range_pts",
    "atr14_pts",
]

VOLUME_FEATURE_COLUMNS = [
    "rolling_volume_20_bars",
    "relative_volume_20",
]

F1_FEATURE_COLUMNS = (
    BASE_OHLCV_COLUMNS
    + TIME_FEATURE_COLUMNS
    + PREVIOUS_DAY_COLUMNS
    + OPENING_RANGE_COLUMNS
    + RUNNING_SESSION_COLUMNS
    + VWAP_COLUMNS
    + VOLATILITY_COLUMNS
    + VOLUME_FEATURE_COLUMNS
)
