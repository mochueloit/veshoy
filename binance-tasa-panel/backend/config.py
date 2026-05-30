import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_FILE = BASE_DIR / "data" / "historial.json"
TOKENS_FILE = BASE_DIR / "data" / "tokens.json"

INTERNAL_UPDATE_KEY = os.getenv("TOKEN_INTERNO", "")
API_ADMIN_TOKEN = os.getenv("API_ADMIN_TOKEN", os.getenv("API_TOKEN", ""))

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:10001").rstrip("/")
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "10001"))

MAX_HISTORY_ENTRIES = int(os.getenv("MAX_HISTORY_ENTRIES", "5000"))
UPDATE_INTERVAL_HOURS = int(os.getenv("UPDATE_INTERVAL_HOURS", "1"))

PLAYWRIGHT_BROWSERS_PATH = os.getenv("PLAYWRIGHT_BROWSERS_PATH", "")

_cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:10001,http://127.0.0.1:10001")
CORS_ORIGINS = [origin.strip() for origin in _cors_raw.split(",") if origin.strip()]

SCRAPE_MAX_RETRIES = int(os.getenv("SCRAPE_MAX_RETRIES", "3"))
BCV_TIMEOUT_MS = int(os.getenv("BCV_TIMEOUT_MS", "60000"))
