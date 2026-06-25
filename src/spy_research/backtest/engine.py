from __future__ import annotations

import pandas as pd


def label_target_before_stop(
    bars: pd.DataFrame,
    signals: pd.DataFrame,
    *,
    horizon_bars: int,
    target_points: float,
    stop_points: float,
) -> pd.DataFrame:
    """Label whether each signal reaches target before stop within N bars.

    This is for research labeling, not execution. It uses future bars by design
    because it creates outcomes after a signal timestamp. Do not use these labels
    as prediction-time features.
    """
    bars = bars.sort_values("timestamp").reset_index(drop=True).copy()
    signals = signals.sort_values("timestamp").reset_index(drop=True).copy()

    bar_index = {ts: i for i, ts in enumerate(bars["timestamp"])}

    rows = []
    for _, sig in signals.iterrows():
        ts = sig["timestamp"]
        if ts not in bar_index:
            continue

        i = bar_index[ts]
        entry = float(sig["entry_reference"])
        side = sig["side"]
        future = bars.iloc[i + 1 : i + 1 + horizon_bars]

        outcome = "timeout"
        bars_to_outcome = None
        mfe = 0.0
        mae = 0.0

        for step, bar in enumerate(future.itertuples(index=False), start=1):
            if side == "long":
                mfe = max(mfe, float(bar.high) - entry)
                mae = min(mae, float(bar.low) - entry)
                hit_target = float(bar.high) >= entry + target_points
                hit_stop = float(bar.low) <= entry - stop_points
            else:
                mfe = max(mfe, entry - float(bar.low))
                mae = min(mae, entry - float(bar.high))
                hit_target = float(bar.low) <= entry - target_points
                hit_stop = float(bar.high) >= entry + stop_points

            if hit_target and hit_stop:
                outcome = "ambiguous_same_bar"
                bars_to_outcome = step
                break
            if hit_target:
                outcome = "target"
                bars_to_outcome = step
                break
            if hit_stop:
                outcome = "stop"
                bars_to_outcome = step
                break

        rec = sig.to_dict()
        rec.update(
            {
                "label_horizon_bars": horizon_bars,
                "label_target_points": target_points,
                "label_stop_points": stop_points,
                "outcome": outcome,
                "bars_to_outcome": bars_to_outcome,
                "mfe_points": mfe,
                "mae_points": mae,
            }
        )
        rows.append(rec)

    return pd.DataFrame.from_records(rows)
