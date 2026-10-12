#!/usr/bin/env python3
"""
Bybit Signal Desk - High quality Long/Short signals (USDC only)
Runs 24/7, scans available USDC pairs, applies strict filters, sends only the best setups.
"""

import time
import logging
from pathlib import Path

from config import (
    SCAN_INTERVAL_MINUTES, CATEGORIES, KLINE_INTERVAL, KLINE_LIMIT, MIN_RR
)
from bybit_client import get_all_tickers, get_klines
from filters import pre_filter_tickers
from analysis import detect_structure, is_high_quality_setup
from telegram_sender import send_signal, send_status

# Logging
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/desk.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("desk")

# Simple in-memory cooldown to avoid spamming the same symbol
last_sent = {}  # symbol -> timestamp
COOLDOWN_MINUTES = 90

def already_sent_recently(symbol: str) -> bool:
    ts = last_sent.get(symbol)
    if not ts:
        return False
    return (time.time() - ts) < COOLDOWN_MINUTES * 60

def run_cycle():
    log.info("=== Starting scan cycle ===")
    candidates = []

    for cat in CATEGORIES:
        try:
            tickers = get_all_tickers(cat)
            filtered = pre_filter_tickers(tickers, cat)
            candidates.extend(filtered)
            log.info(f"{cat}: {len(tickers)} tickers → {len(filtered)} after liquidity filter")
        except Exception as e:
            log.error(f"Error fetching {cat}: {e}")

    # Deduplicate by symbol (prefer linear if both exist)
    seen = {}
    for c in candidates:
        sym = c["symbol"]
        if sym not in seen or c["category"] == "linear":
            seen[sym] = c
    candidates = list(seen.values())
    candidates.sort(key=lambda x: x["turnover24h"], reverse=True)

    log.info(f"Total unique candidates for deep analysis: {len(candidates)}")

    signals_sent = 0
    for c in candidates[:25]:  # hard cap per cycle
        symbol = c["symbol"]
        category = c["category"]

        if already_sent_recently(symbol):
            continue

        try:
            klines = get_klines(category, symbol, KLINE_INTERVAL, KLINE_LIMIT)
            if len(klines) < 40:
                continue

            analysis = detect_structure(klines)
            analysis.update({
                "symbol": symbol,
                "category": category,
                "turnover24h": c["turnover24h"],
                "change24h": c["change24h"],
            })

            if is_high_quality_setup(analysis, MIN_RR):
                ok = send_signal(analysis)
                if ok:
                    last_sent[symbol] = time.time()
                    signals_sent += 1
                    log.info(f"SIGNAL SENT → {symbol} {analysis['bias'].upper()} (Q={analysis['quality']})")
                    time.sleep(1.2)
                else:
                    log.warning(f"Failed to send signal for {symbol}")
        except Exception as e:
            log.error(f"Error analysing {symbol}: {e}")
            continue

    log.info(f"Cycle finished. Signals sent: {signals_sent}")
    return signals_sent

def main():
    send_status(f"Signal Desk iniciado\nIntervalo: {SCAN_INTERVAL_MINUTES} min\nFiltros: rigorosos (só USDC)")
    log.info("Signal Desk started")

    while True:
        try:
            run_cycle()
        except Exception as e:
            log.exception(f"Cycle crashed: {e}")
            send_status(f"Erro no ciclo: {str(e)[:200]}")

        log.info(f"Sleeping {SCAN_INTERVAL_MINUTES} minutes...")
        time.sleep(SCAN_INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    main()
