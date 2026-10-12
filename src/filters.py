from typing import List, Dict
from config import MIN_TURNOVER_USDT, MIN_VOLUME_USDT, MAX_SPREAD_PCT
from bybit_client import get_orderbook_spread

def pre_filter_tickers(tickers: List[Dict], category: str) -> List[Dict]:
    """
    Hard liquidity + activity filter.
    ONLY USDC pairs are accepted.
    """
    passed = []
    for t in tickers:
        try:
            symbol = t.get("symbol", "")
            # Strict: only USDC pairs
            if not symbol.endswith("USDC"):
                continue

            turnover = float(t.get("turnover24h", 0) or 0)
            volume = float(t.get("volume24h", 0) or 0)
            last = float(t.get("lastPrice", 0) or 0)
            change = float(t.get("price24hPcnt", 0) or 0) * 100

            if last <= 0:
                continue
            if turnover < MIN_TURNOVER_USDT:
                continue
            if volume * last < MIN_VOLUME_USDT:
                continue

            # Avoid pure extreme moves already exhausted
            if abs(change) > 35:
                continue

            passed.append({
                "symbol": symbol,
                "category": category,
                "last": last,
                "turnover24h": turnover,
                "change24h": change,
                "high24h": float(t.get("highPrice24h", 0) or 0),
                "low24h": float(t.get("lowPrice24h", 0) or 0),
                "quote": "USDC",
            })
        except Exception:
            continue

    # Rank by turnover descending
    passed.sort(key=lambda x: x["turnover24h"], reverse=True)
    return passed[:50]


def apply_spread_filter(candidates: List[Dict]) -> List[Dict]:
    """Optional second pass for spread on the shortlist."""
    final = []
    for c in candidates:
        spread = get_orderbook_spread(c["category"], c["symbol"])
        if spread is None or spread <= MAX_SPREAD_PCT:
            c["spread"] = spread
            final.append(c)
    return final
