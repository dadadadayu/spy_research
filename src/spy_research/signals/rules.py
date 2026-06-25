from __future__ import annotations

import pandas as pd


def empty_signal_frame() -> pd.DataFrame:
    """Return the standard signal-log schema.

    Keep this stable. Add fields only when the research question requires them.
    """
    return pd.DataFrame(
        columns=[
            "timestamp",
            "symbol",
            "side",
            "setup_name",
            "entry_reference",
            "stop_reference",
            "target_reference",
            "context",
        ]
    )


def simple_breakout_candidates(
    bars_5m: pd.DataFrame,
    *,
    lookback: int = 6,
    symbol: str = "SPY",
) -> pd.DataFrame:
    """A deliberately simple placeholder candidate generator.

    Hypothesis:
        A close breaking above/below the previous N-bar range may identify a
        directional candidate worth evaluating.

    This is not an endorsed strategy yet. It is only a tiny deterministic
    rule to test the plumbing of signal logging and later backtesting.
    """
    df = bars_5m.copy().sort_values("timestamp").reset_index(drop=True)

    prev_high = df["high"].rolling(lookback).max().shift(1)
    prev_low = df["low"].rolling(lookback).min().shift(1)

    long_mask = df["close"] > prev_high
    short_mask = df["close"] < prev_low

    records = []
    for _, row in df.loc[long_mask | short_mask].iterrows():
        side = "long" if row["close"] > prev_high.loc[row.name] else "short"
        records.append(
            {
                "timestamp": row["timestamp"],
                "symbol": symbol,
                "side": side,
                "setup_name": f"simple_{lookback}_bar_breakout",
                "entry_reference": row["close"],
                "stop_reference": None,
                "target_reference": None,
                "context": {"lookback": lookback},
            }
        )

    return pd.DataFrame.from_records(records)
