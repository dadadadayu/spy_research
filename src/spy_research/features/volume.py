from __future__ import annotations

import numpy as np
import pandas as pd


def add_volume_features(df: pd.DataFrame, *, window: int = 20) -> pd.DataFrame:
    """Add simple rolling relative-volume features."""
    out = df.copy()
    out["rolling_volume_20_bars"] = out["volume"].rolling(window, min_periods=1).mean()
    out["relative_volume_20"] = out["volume"] / out["rolling_volume_20_bars"].replace(0, np.nan)
    return out
