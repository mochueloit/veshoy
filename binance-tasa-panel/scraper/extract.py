import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scraper"))

load_dotenv(ROOT_DIR / ".env")

import os

from browser import launch_chromium

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:10001").rstrip("/")
INTERNAL_TOKEN = os.getenv("TOKEN_INTERNO", "")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
SCRAPE_MAX_RETRIES = int(os.getenv("SCRAPE_MAX_RETRIES", "3"))
BCV_TIMEOUT_MS = int(os.getenv("BCV_TIMEOUT_MS", "60000"))

# Solo usar en servidores legacy; en Docker la imagen oficial ya trae navegadores
_playwright_path = os.getenv("PLAYWRIGHT_BROWSERS_PATH", "")
if _playwright_path:
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = _playwright_path

BINANCE_P2P_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def get_binance_price():
    payload = {
        "asset": "USDT",
        "fiat": "VES",
        "tradeType": "BUY",
        "page": 1,
        "rows": 10,
        "countries": [],
        "proMerchantAds": False,
        "shieldMerchantAds": False,
        "publisherType": None,
        "payTypes": [],
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    if BINANCE_API_KEY:
        headers["X-MBX-APIKEY"] = BINANCE_API_KEY

    response = requests.post(BINANCE_P2P_URL, json=payload, headers=headers, timeout=20)
    response.raise_for_status()
    body = response.json()

    if not body.get("success") or not body.get("data"):
        raise RuntimeError(f"Respuesta inesperada de Binance P2P: {body}")

    prices = [float(ad["adv"]["price"]) for ad in body["data"][:5]]
    if not prices:
        raise RuntimeError("Binance P2P no devolvió anuncios con precio")

    prices.sort()
    mid = len(prices) // 2
    return prices[mid] if len(prices) % 2 else (prices[mid - 1] + prices[mid]) / 2


def get_bcv_price(browser):
    page = browser.new_page()
    try:
        page.set_extra_http_headers({"User-Agent": USER_AGENT})
        print("Consultando BCV...")
        page.goto("https://www.bcv.org.ve/", wait_until="load", timeout=BCV_TIMEOUT_MS)
        element = page.locator("#dolar strong")
        element.wait_for(state="visible", timeout=15000)
        raw_val = element.inner_text()
        return float(raw_val.replace(",", ".").strip())
    finally:
        page.close()


def get_bcv_price_with_playwright():
    with sync_playwright() as playwright:
        browser = launch_chromium(playwright)
        try:
            return get_bcv_price(browser)
        finally:
            browser.close()


def enviar_al_backend(binance_price, bcv_price):
    headers = {
        "x-internal-key": INTERNAL_TOKEN,
        "Content-Type": "application/json",
    }
    payload = {"binance": binance_price, "bcv": bcv_price}
    url = f"{BACKEND_URL}/api/update"
    return requests.post(url, json=payload, timeout=15, headers=headers)


def run_scraper():
    if not INTERNAL_TOKEN:
        print("ERROR: TOKEN_INTERNO no configurado en .env")
        return False

    binance_price = None
    bcv_price = None
    last_error = None

    for attempt in range(1, SCRAPE_MAX_RETRIES + 1):
        try:
            print(f"[{datetime.now():%H:%M:%S}] Intento {attempt}/{SCRAPE_MAX_RETRIES}")
            print("Consultando Binance P2P (API)...")
            binance_price = get_binance_price()
            bcv_price = get_bcv_price_with_playwright()
            if binance_price and bcv_price:
                break
        except Exception as exc:
            last_error = exc
            print(f"Intento {attempt} fallido: {exc}")
            if attempt < SCRAPE_MAX_RETRIES:
                time.sleep(attempt * 5)

    if not binance_price or not bcv_price:
        print(f"Falló la captura. Binance: {binance_price} | BCV: {bcv_price}")
        if last_error:
            print(f"Último error: {last_error}")
        return False

    response = enviar_al_backend(binance_price, bcv_price)
    if response.status_code == 200:
        print(f"ÉXITO: Binance({binance_price}) | BCV({bcv_price})")
        return True

    print(f"Error Backend: {response.status_code} - {response.text}")
    return False


if __name__ == "__main__":
    ok = run_scraper()
    sys.exit(0 if ok else 1)
