from __future__ import annotations

import pandas as pd


def add_volatility_features(df: pd.DataFrame, *, atr_window: int = 14) -> pd.DataFrame:
    """Add bar range, true range, and simple ATR features.

    This uses only current and previous bars. The first bar's true range falls
    back to high-low because no previous close exists.
    """
    out = df.copy()

    out["bar_range_pts"] = out["high"] - out["low"]

    prev_close = out["close"].shift(1)
    high_low = out["high"] - out["low"]
    high_prev_close = (out["high"] - prev_close).abs()
    low_prev_close = (out["low"] - prev_close).abs()

    out["true_range_pts"] = pd.concat(
        [high_low, high_prev_close, low_prev_close],
        axis=1,
    ).max(axis=1)
    out["atr14_pts"] = out["true_range_pts"].rolling(atr_window, min_periods=1).mean()

    return out
