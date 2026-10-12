from typing import Dict, List, Optional, Tuple
import numpy as np

def _to_float(v):
    try:
        return float(v)
    except Exception:
        return 0.0

def calculate_rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    deltas = np.diff(closes[-(period + 1):])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_ema(values: List[float], period: int) -> float:
    if len(values) < period:
        return values[-1] if values else 0.0
    weights = np.exp(np.linspace(-1., 0., period))
    weights /= weights.sum()
    return float(np.convolve(values[-period:], weights, mode="valid")[0])

def detect_structure(klines: List[list]) -> Dict:
    """
    Simple but rigorous structure analysis on 15m candles.
    Returns bias, key levels and quality score.
    """
    if len(klines) < 30:
        return {"bias": "neutral", "quality": 0, "reason": "insufficient data"}

    closes = [_to_float(k[4]) for k in klines]
    highs = [_to_float(k[2]) for k in klines]
    lows = [_to_float(k[3]) for k in klines]
    volumes = [_to_float(k[5]) for k in klines]

    last_close = closes[-1]
    rsi = calculate_rsi(closes)
    ema20 = calculate_ema(closes, 20)
    ema50 = calculate_ema(closes, 50)

    # Recent swing high / low (last 20 candles)
    recent_high = max(highs[-20:])
    recent_low = min(lows[-20:])

    # Volume confirmation
    avg_vol = np.mean(volumes[-20:]) if volumes else 1
    last_vol = volumes[-1]
    vol_ratio = last_vol / avg_vol if avg_vol > 0 else 1

    # Momentum
    change_5 = (closes[-1] - closes[-6]) / closes[-6] * 100 if closes[-6] else 0
    change_10 = (closes[-1] - closes[-11]) / closes[-11] * 100 if len(closes) > 10 and closes[-11] else 0

    bias = "neutral"
    quality = 0
    reasons = []

    # === LONG conditions (strict) ===
    long_score = 0
    if last_close > ema20 > ema50:
        long_score += 2
        reasons.append("price above EMA20 & EMA50")
    if 40 < rsi < 65:
        long_score += 1
        reasons.append(f"RSI healthy ({rsi:.1f})")
    if change_5 > 0.8 and change_10 > 0:
        long_score += 1
        reasons.append("positive momentum")
    if vol_ratio > 1.3:
        long_score += 1
        reasons.append("volume confirmation")
    if last_close > recent_low * 1.01 and (recent_high - last_close) / last_close > 0.012:
        long_score += 1
        reasons.append("room to recent high")

    # === SHORT conditions (strict) ===
    short_score = 0
    if last_close < ema20 < ema50:
        short_score += 2
        reasons.append("price below EMA20 & EMA50")
    if 35 < rsi < 60:
        short_score += 1
        reasons.append(f"RSI not oversold ({rsi:.1f})")
    if change_5 < -0.8 and change_10 < 0:
        short_score += 1
        reasons.append("negative momentum")
    if vol_ratio > 1.3:
        short_score += 1
        reasons.append("volume confirmation")
    if last_close < recent_high * 0.99 and (last_close - recent_low) / last_close > 0.012:
        short_score += 1
        reasons.append("room to recent low")

    if long_score >= 4 and long_score > short_score:
        bias = "long"
        quality = long_score
    elif short_score >= 4 and short_score > long_score:
        bias = "short"
        quality = short_score
    else:
        bias = "neutral"
        quality = max(long_score, short_score)

    # Suggested levels
    atr_proxy = (recent_high - recent_low) / 2
    if bias == "long":
        entry = last_close
        stop = max(recent_low * 0.995, entry - atr_proxy * 0.9)
        target = entry + (entry - stop) * 2.0
    elif bias == "short":
        entry = last_close
        stop = min(recent_high * 1.005, entry + atr_proxy * 0.9)
        target = entry - (stop - entry) * 2.0
    else:
        entry = stop = target = last_close

    rr = abs(target - entry) / abs(entry - stop) if abs(entry - stop) > 0 else 0

    return {
        "bias": bias,
        "quality": quality,
        "rsi": round(rsi, 1),
        "ema20": ema20,
        "ema50": ema50,
        "entry": round(entry, 8),
        "stop": round(stop, 8),
        "target": round(target, 8),
        "rr": round(rr, 2),
        "vol_ratio": round(vol_ratio, 2),
        "reasons": reasons,
        "recent_high": recent_high,
        "recent_low": recent_low,
    }

def is_high_quality_setup(analysis: Dict, min_rr: float = 1.8) -> bool:
    if analysis["bias"] == "neutral":
        return False
    if analysis["quality"] < 4:
        return False
    if analysis["rr"] < min_rr:
        return False
    return True
