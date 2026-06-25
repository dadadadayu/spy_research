from __future__ import annotations

from pathlib import Path
import pandas as pd

from spy_research.config import OHLCV_COLUMNS, RAW_SPY_1M_CSV


def normalize_ohlcv_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize common OHLCV column names to the project standard."""
    renamed = {c: c.strip().lower() for c in df.columns}
    df = df.rename(columns=renamed)

    aliases = {
        "datetime": "timestamp",
        "date": "timestamp",
        "time": "timestamp",
        "o": "open",
        "h": "high",
        "l": "low",
        "c": "close",
        "v": "volume",
    }
    df = df.rename(columns={c: aliases.get(c, c) for c in df.columns})

    missing = [c for c in OHLCV_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required OHLCV columns: {missing}")

    df = df[OHLCV_COLUMNS].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="raise")

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="raise").astype("float64")

    df["volume"] = pd.to_numeric(df["volume"], errors="raise")
    return df


def load_ohlcv_csv(path: str | Path) -> pd.DataFrame:
    """Load a CSV with OHLCV data and normalize it."""
    df = pd.read_csv(path)
    df = normalize_ohlcv_columns(df)
    return df.sort_values("timestamp").reset_index(drop=True)


def load_raw_spy_1m(path: str | Path = RAW_SPY_1M_CSV) -> pd.DataFrame:
    """Load the raw SPY 1-minute CSV."""
    return load_ohlcv_csv(path)


def load_processed_parquet(path: str | Path) -> pd.DataFrame:
    """Load a processed Parquet OHLCV file."""
    df = pd.read_parquet(path)
    return normalize_ohlcv_columns(df)


def save_ohlcv_parquet(df: pd.DataFrame, path: str | Path) -> None:
    """Save OHLCV data to Parquet."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
