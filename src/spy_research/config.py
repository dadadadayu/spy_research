from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
VENDOR_SAMPLE_DIR = DATA_DIR / "vendor_sample"

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
SIGNALS_DIR = OUTPUTS_DIR / "signals"
BACKTESTS_DIR = OUTPUTS_DIR / "backtests"
REPORTS_DIR = OUTPUTS_DIR / "reports"

RAW_SPY_1M_CSV = RAW_DIR / "SPY_1min_firstratedata.csv"

OHLCV_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]

RTH_START = "09:30"
RTH_END = "16:00"
