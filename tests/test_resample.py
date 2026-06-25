import pandas as pd

from spy_research.features.resample import resample_ohlcv


def test_resample_5m_ohlcv():
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2023-01-03 09:30:00", periods=5, freq="1min"),
            "open": [1, 2, 3, 4, 5],
            "high": [2, 3, 4, 5, 6],
            "low": [0, 1, 2, 3, 4],
            "close": [1.5, 2.5, 3.5, 4.5, 5.5],
            "volume": [10, 20, 30, 40, 50],
        }
    )

    out = resample_ohlcv(df, "5min", rth_anchor=True)

    assert len(out) == 1
    row = out.iloc[0]
    assert row["open"] == 1
    assert row["high"] == 6
    assert row["low"] == 0
    assert row["close"] == 5.5
    assert row["volume"] == 150
