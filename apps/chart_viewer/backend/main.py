from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


Timeframe = Literal["1m", "5m", "30m", "1h"]

APP_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

TIMEFRAME_FILES: dict[str, list[str]] = {
    "1m": ["spy_1m_rth.parquet", "spy_1m.parquet"],
    "5m": ["spy_5m_rth.parquet", "spy_5m.parquet"],
    "30m": ["spy_30m_rth.parquet", "spy_30m.parquet"],
    "1h": ["spy_1h_rth.parquet", "spy_1h.parquet"],
}

app = FastAPI(title="SPY Research Chart Viewer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def resolve_timeframe_path(timeframe: str) -> Path:
    candidates = TIMEFRAME_FILES.get(timeframe)
    if not candidates:
        raise HTTPException(status_code=400, detail=f"Unsupported timeframe: {timeframe}")

    for filename in candidates:
        path = PROCESSED_DIR / filename
        if path.exists():
            return path

    raise HTTPException(
        status_code=404,
        detail={
            "message": f"No processed file found for timeframe {timeframe}",
            "looked_for": [str(PROCESSED_DIR / name) for name in candidates],
        },
    )


def normalize_bars(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "timestamp" not in df.columns:
        if isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
            df = df.rename(columns={df.columns[0]: "timestamp"})
        else:
            possible_time_cols = ["datetime", "date", "time"]
            found = next((col for col in possible_time_cols if col in df.columns), None)
            if found is None:
                raise HTTPException(
                    status_code=500,
                    detail=f"Could not find timestamp column. Columns: {list(df.columns)}",
                )
            df = df.rename(columns={found: "timestamp"})

    required = ["timestamp", "open", "high", "low", "close"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise HTTPException(status_code=500, detail=f"Missing columns: {missing}")

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Treat naive timestamps as exchange time. Convert to UTC seconds for Lightweight Charts.
    if df["timestamp"].dt.tz is None:
        ts_utc = df["timestamp"].dt.tz_localize(
            "America/New_York",
            ambiguous="infer",
            nonexistent="shift_forward",
        ).dt.tz_convert("UTC")
    else:
        ts_utc = df["timestamp"].dt.tz_convert("UTC")

    df["time"] = (ts_utc.astype("int64") // 1_000_000_000).astype(int)
    df["timestamp_et"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Lightweight Charts requires strictly unique, ascending time values.
    df = df.drop_duplicates(subset=["time"], keep="last")
    df = df.sort_values("time")

    out_cols = ["time", "timestamp_et", "open", "high", "low", "close"]
    if "volume" in df.columns:
        out_cols.append("volume")

    df = df[out_cols].sort_values("time")

    return df


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/timeframes")
def timeframes() -> dict[str, list[str]]:
    available: list[str] = []

    for timeframe, filenames in TIMEFRAME_FILES.items():
        if any((PROCESSED_DIR / filename).exists() for filename in filenames):
            available.append(timeframe)

    return {"timeframes": available}


@app.get("/api/bars")
def bars(
    timeframe: Timeframe = Query("5m"),
    limit: int = Query(5000, ge=1, le=100_000),
) -> list[dict]:
    path = resolve_timeframe_path(timeframe)

    df = pd.read_parquet(path)
    df = normalize_bars(df)

    if limit:
        df = df.tail(limit)

    return df.to_dict(orient="records")


@app.get("/api/debug")
def debug(timeframe: Timeframe = Query("5m")) -> dict:
    path = resolve_timeframe_path(timeframe)
    df = pd.read_parquet(path)
    normalized = normalize_bars(df)

    return {
        "timeframe": timeframe,
        "path": str(path),
        "raw_rows": len(df),
        "normalized_rows": len(normalized),
        "columns": list(df.columns),
        "first_time": normalized["timestamp_et"].iloc[0] if len(normalized) else None,
        "last_time": normalized["timestamp_et"].iloc[-1] if len(normalized) else None,
        "duplicate_chart_times_after_normalize": int(normalized["time"].duplicated().sum()),
        "is_time_monotonic_increasing": bool(normalized["time"].is_monotonic_increasing),
    }