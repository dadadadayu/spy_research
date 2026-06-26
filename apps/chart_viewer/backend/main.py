from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


Timeframe = Literal["1m", "5m", "30m", "1h"]


def find_repo_root(start: Path) -> Path:
    """Find the repo root by walking upward until pyproject.toml is found."""
    for candidate in [start, *start.parents]:
        if (candidate / "pyproject.toml").exists():
            return candidate

    # Normal expected location:
    # repo/apps/chart_viewer/backend/main.py
    return Path(__file__).resolve().parents[3]


REPO_ROOT = find_repo_root(Path(__file__).resolve())
DATA_DIR = REPO_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
FEATURES_DIR = DATA_DIR / "features"

PROCESSED_FILES: dict[str, list[str]] = {
    "1m": ["spy_1m_rth.parquet", "spy_1m.parquet"],
    "5m": ["spy_5m_rth.parquet", "spy_5m.parquet"],
    "30m": ["spy_30m_rth.parquet", "spy_30m.parquet"],
    "1h": ["spy_1h_rth.parquet", "spy_1h.parquet"],
}

FEATURE_FILES: dict[str, list[str]] = {
    "1m": ["spy_1m_rth_features.parquet", "spy_1m_features.parquet"],
    "5m": ["spy_5m_rth_features.parquet", "spy_5m_features.parquet"],
    "30m": ["spy_30m_rth_features.parquet", "spy_30m_features.parquet"],
    "1h": ["spy_1h_rth_features.parquet", "spy_1h_features.parquet"],
}

FEATURE_COLUMNS: list[str] = [
    "session_date",
    "minute_from_open",
    "bar_index_in_session",
    "session_open",
    "running_session_high",
    "running_session_low",
    "session_range_so_far_pts",
    "close_location_in_session_range",
    "prev_day_high",
    "prev_day_low",
    "prev_day_close",
    "gap_from_prev_close_pts",
    "or30_high",
    "or30_low",
    "or30_range_pts",
    "or30_complete",
    "or60_high",
    "or60_low",
    "or60_range_pts",
    "or60_complete",
    "vwap",
    "dist_to_vwap_pts",
    "bar_range_pts",
    "true_range_pts",
    "atr14_pts",
    "rolling_volume_20_bars",
    "relative_volume_20",
]

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


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "app": "SPY Research Chart Viewer API",
        "status": "ok",
        "endpoints": [
            "/api/health",
            "/api/timeframes",
            "/api/files",
            "/api/bars?timeframe=5m&limit=5000",
            "/api/feature-bars?timeframe=5m&limit=5000",
            "/api/debug?timeframe=5m",
        ],
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/files")
def files() -> dict[str, Any]:
    processed_files = sorted(path.name for path in PROCESSED_DIR.glob("*") if path.is_file())
    feature_files = sorted(path.name for path in FEATURES_DIR.glob("*") if path.is_file())

    return {
        "repo_root": str(REPO_ROOT),
        "processed_dir": str(PROCESSED_DIR),
        "features_dir": str(FEATURES_DIR),
        "processed_files": processed_files,
        "feature_files": feature_files,
    }


@app.get("/api/timeframes")
def timeframes() -> dict[str, Any]:
    processed_available: list[str] = []
    features_available: list[str] = []

    for timeframe, filenames in PROCESSED_FILES.items():
        if any((PROCESSED_DIR / filename).exists() for filename in filenames):
            processed_available.append(timeframe)

    for timeframe, filenames in FEATURE_FILES.items():
        if any((FEATURES_DIR / filename).exists() for filename in filenames):
            features_available.append(timeframe)

    return {
        "processed_timeframes": processed_available,
        "feature_timeframes": features_available,
    }


def resolve_first_existing(base_dir: Path, filenames: list[str]) -> Path | None:
    for filename in filenames:
        path = base_dir / filename
        if path.exists():
            return path
    return None


def resolve_processed_path(timeframe: str) -> Path:
    candidates = PROCESSED_FILES.get(timeframe)
    if not candidates:
        raise HTTPException(status_code=400, detail=f"Unsupported timeframe: {timeframe}")

    path = resolve_first_existing(PROCESSED_DIR, candidates)
    if path is not None:
        return path

    raise HTTPException(
        status_code=404,
        detail={
            "message": f"No processed file found for timeframe {timeframe}",
            "processed_dir": str(PROCESSED_DIR),
            "looked_for": [str(PROCESSED_DIR / name) for name in candidates],
            "available_files": sorted(path.name for path in PROCESSED_DIR.glob("*")),
        },
    )


def resolve_feature_path(timeframe: str) -> Path | None:
    candidates = FEATURE_FILES.get(timeframe)
    if not candidates:
        raise HTTPException(status_code=400, detail=f"Unsupported timeframe: {timeframe}")

    return resolve_first_existing(FEATURES_DIR, candidates)


def read_timeframe_dataframe(timeframe: str, prefer_features: bool) -> tuple[pd.DataFrame, Path, bool]:
    feature_path = resolve_feature_path(timeframe)

    if prefer_features and feature_path is not None:
        return pd.read_parquet(feature_path), feature_path, True

    processed_path = resolve_processed_path(timeframe)
    return pd.read_parquet(processed_path), processed_path, False


def normalize_bars(df: pd.DataFrame, include_features: bool = False) -> pd.DataFrame:
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
                    detail={
                        "message": "Could not find timestamp column.",
                        "columns": list(df.columns),
                        "index_type": type(df.index).__name__,
                    },
                )
            df = df.rename(columns={found: "timestamp"})

    required = ["timestamp", "open", "high", "low", "close"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Missing required OHLC columns.",
                "missing": missing,
                "columns": list(df.columns),
            },
        )

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    for col in ["open", "high", "low", "close", "volume", *FEATURE_COLUMNS]:
        if col in df.columns and col not in ["session_date"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["timestamp", "open", "high", "low", "close"])
    df = df.sort_values("timestamp")

    # Treat naive timestamps as US/Eastern exchange time, then convert to UTC seconds
    # for TradingView Lightweight Charts.
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

    if include_features:
        out_cols.extend(col for col in FEATURE_COLUMNS if col in df.columns)

    out = df[out_cols].copy()

    if "session_date" in out.columns:
        out["session_date"] = out["session_date"].astype("string")

    # Convert NaN / NA values to JSON-safe nulls.
    out = out.astype(object).where(pd.notna(out), None)

    return out


def dataframe_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    return df.to_dict(orient="records")


@app.get("/api/bars")
def bars(
    timeframe: Timeframe = Query("5m"),
    limit: int = Query(5000, ge=1, le=100_000),
) -> list[dict[str, Any]]:
    df, _, _ = read_timeframe_dataframe(timeframe, prefer_features=False)
    normalized = normalize_bars(df, include_features=False)

    if limit:
        normalized = normalized.tail(limit)

    return dataframe_records(normalized)


@app.get("/api/feature-bars")
def feature_bars(
    timeframe: Timeframe = Query("5m"),
    limit: int = Query(5000, ge=1, le=100_000),
) -> dict[str, Any]:
    df, path, has_features = read_timeframe_dataframe(timeframe, prefer_features=True)
    normalized = normalize_bars(df, include_features=has_features)

    if limit:
        normalized = normalized.tail(limit)

    feature_cols = [col for col in FEATURE_COLUMNS if col in normalized.columns]

    return {
        "meta": {
            "timeframe": timeframe,
            "rows": len(normalized),
            "features_available": has_features,
            "feature_columns": feature_cols,
            "source_path": str(path),
        },
        "bars": dataframe_records(normalized),
    }


@app.get("/api/debug")
def debug(timeframe: Timeframe = Query("5m")) -> dict[str, Any]:
    df, path, has_features = read_timeframe_dataframe(timeframe, prefer_features=True)
    normalized = normalize_bars(df, include_features=has_features)

    return {
        "timeframe": timeframe,
        "path": str(path),
        "features_available": has_features,
        "raw_rows": len(df),
        "normalized_rows": len(normalized),
        "columns": list(df.columns),
        "feature_columns_found": [col for col in FEATURE_COLUMNS if col in df.columns],
        "first_time": normalized["timestamp_et"].iloc[0] if len(normalized) else None,
        "last_time": normalized["timestamp_et"].iloc[-1] if len(normalized) else None,
        "duplicate_chart_times_after_normalize": int(normalized["time"].duplicated().sum()),
        "is_time_monotonic_increasing": bool(normalized["time"].is_monotonic_increasing),
    }
