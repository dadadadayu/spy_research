from __future__ import annotations

import numpy as np
import pandas as pd


def add_vwap_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add session VWAP and distance-to-VWAP features."""
    if "session_date" not in df.columns:
        raise ValueError("add_vwap_features requires session_date. Run add_time_features first.")

    out = df.copy()
    typical_price = (out["high"] + out["low"] + out["close"]) / 3.0
    price_volume = typical_price * out["volume"]

    grouped = out.groupby("session_date", sort=False)
    cumulative_pv = price_volume.groupby(out["session_date"], sort=False).cumsum()
    cumulative_volume = grouped["volume"].cumsum().replace(0, np.nan)

    out["vwap"] = cumulative_pv / cumulative_volume
    out["dist_to_vwap_pts"] = out["close"] - out["vwap"]
    out["dist_to_vwap_pct"] = out["dist_to_vwap_pts"] / out["vwap"].replace(0, np.nan)
    out["above_vwap"] = out["close"] > out["vwap"]

    return out
