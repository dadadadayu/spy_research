from __future__ import annotations

import pandas as pd

from spy_research.data.loaders import normalize_ohlcv_columns
from spy_research.features.levels import (
    add_opening_range_features,
    add_previous_day_levels,
    add_running_session_features,
)
from spy_research.features.time import add_time_features
from spy_research.features.vwap import add_vwap_features
from spy_research.features.volatility import add_volatility_features
from spy_research.features.volume import add_volume_features


def build_f1_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build the first feature foundation used by Phase 2 and early Phase 3.

    This intentionally avoids a large indicator pile. It creates structural
    intraday state features: time/session, previous day levels, opening ranges,
    running session state, VWAP, volatility, and relative volume.
    """
    out = normalize_ohlcv_columns(df)
    out = out.sort_values("timestamp").reset_index(drop=True)

    out = add_time_features(out)
    out = add_running_session_features(out)
    out = add_previous_day_levels(out)
    out = add_opening_range_features(out, windows=(30, 60))
    out = add_vwap_features(out)
    out = add_volatility_features(out)
    out = add_volume_features(out)

    return out
