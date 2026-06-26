import math

import pandas as pd

from spy_research.features.build import build_f1_features


def make_two_day_5m_bars() -> pd.DataFrame:
    rows = []
    for day, base in [("2023-01-03", 100.0), ("2023-01-04", 110.0)]:
        for i in range(13):  # 09:30 through 10:30, enough for OR30/OR60 checks.
            ts = pd.Timestamp(f"{day} 09:30:00") + pd.Timedelta(minutes=5 * i)
            open_price = base + i * 0.10
            rows.append(
                {
                    "timestamp": ts,
                    "open": open_price,
                    "high": open_price + 1.0,
                    "low": open_price - 1.0,
                    "close": open_price + 0.5,
                    "volume": 100 + i,
                }
            )
    return pd.DataFrame(rows)


def test_build_f1_features_preserves_rows_and_adds_session_columns():
    df = make_two_day_5m_bars()
    out = build_f1_features(df)

    assert len(out) == len(df)
    assert "session_date" in out.columns
    assert "minute_from_open" in out.columns
    assert "bar_index_in_session" in out.columns
    assert out.loc[0, "minute_from_open"] == 0
    assert out.loc[0, "bar_index_in_session"] == 0
    assert out.loc[12, "bar_index_in_session"] == 12
    assert out.loc[13, "bar_index_in_session"] == 0


def test_previous_day_levels_use_prior_session_only():
    df = make_two_day_5m_bars()
    out = build_f1_features(df)

    first_day = out[out["session_date"] == pd.Timestamp("2023-01-03").date()]
    second_day = out[out["session_date"] == pd.Timestamp("2023-01-04").date()]

    assert first_day["prev_day_high"].isna().all()
    assert second_day["prev_day_high"].notna().all()
    assert second_day.iloc[0]["prev_day_high"] == first_day["high"].max()
    assert second_day.iloc[0]["prev_day_low"] == first_day["low"].min()
    assert second_day.iloc[0]["prev_day_close"] == first_day.iloc[-1]["close"]


def test_opening_range_levels_only_available_after_window_complete():
    df = make_two_day_5m_bars()
    out = build_f1_features(df)
    first_day = out[out["session_date"] == pd.Timestamp("2023-01-03").date()].reset_index(drop=True)

    # OR30 is not complete during 09:30-09:55 bars, then becomes available at 10:00.
    assert first_day.loc[0:5, "or30_complete"].eq(False).all()
    assert first_day.loc[6, "or30_complete"]
    assert first_day.loc[6, "or30_high"] == first_day.loc[0:5, "high"].max()
    assert first_day.loc[6, "or30_low"] == first_day.loc[0:5, "low"].min()

    # OR60 becomes available at 10:30 for this 5m test data.
    assert first_day.loc[0:11, "or60_complete"].eq(False).all()
    assert first_day.loc[12, "or60_complete"]


def test_vwap_first_bar_uses_typical_price():
    df = make_two_day_5m_bars()
    out = build_f1_features(df)
    row = out.iloc[0]
    expected_typical = (row["high"] + row["low"] + row["close"]) / 3.0

    assert math.isclose(row["vwap"], expected_typical)
    assert math.isclose(row["dist_to_vwap_pts"], row["close"] - expected_typical)


def test_volatility_and_volume_features_exist():
    df = make_two_day_5m_bars()
    out = build_f1_features(df)

    for col in ["bar_range_pts", "true_range_pts", "atr14_pts", "rolling_volume_20_bars", "relative_volume_20"]:
        assert col in out.columns
        assert out[col].notna().all()
