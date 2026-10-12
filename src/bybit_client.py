import requests
import time
from typing import List, Dict, Optional
from config import BYBIT_BASE_URL, CATEGORIES

session = requests.Session()
session.headers.update({"User-Agent": "SignalDesk/1.0"})

def _get(endpoint: str, params: dict = None) -> dict:
    url = f"{BYBIT_BASE_URL}{endpoint}"
    for attempt in range(3):
        try:
            r = session.get(url, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            if data.get("retCode") == 0:
                return data.get("result", {})
            time.sleep(1)
        except Exception:
            time.sleep(1.5)
    return {}

def get_all_tickers(category: str) -> List[Dict]:
    """Fetch all tickers for a category."""
    result = _get("/v5/market/tickers", {"category": category})
    return result.get("list", [])

def get_instruments(category: str) -> List[Dict]:
    """Fetch trading instruments (status Trading)."""
    instruments = []
    cursor = None
    while True:
        params = {"category": category, "limit": 500, "status": "Trading"}
        if cursor:
            params["cursor"] = cursor
        result = _get("/v5/market/instruments-info", params)
        instruments.extend(result.get("list", []))
        cursor = result.get("nextPageCursor")
        if not cursor:
            break
        time.sleep(0.2)
    return instruments

def get_klines(category: str, symbol: str, interval: str = "15", limit: int = 100) -> List[list]:
    """Return klines oldest -> newest."""
    result = _get("/v5/market/kline", {
        "category": category,
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    })
    raw = result.get("list", [])
    # Bybit returns newest first → reverse
    return list(reversed(raw))

def get_orderbook_spread(category: str, symbol: str) -> Optional[float]:
    """Approximate spread % from top of book."""
    result = _get("/v5/market/orderbook", {
        "category": category,
        "symbol": symbol,
        "limit": 1
    })
    try:
        bid = float(result["b"][0][0])
        ask = float(result["a"][0][0])
        mid = (bid + ask) / 2
        if mid == 0:
            return None
        return ((ask - bid) / mid) * 100
    except Exception:
        return None
