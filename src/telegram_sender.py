import requests
from datetime import datetime, timezone
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_message(text: str, disable_preview: bool = True) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": disable_preview
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        return r.json().get("ok", False)
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def format_signal(signal: dict) -> str:
    side = signal["bias"].upper()
    emoji = "🟢 LONG" if side == "LONG" else "🔴 SHORT"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    text = f"""
{emoji} <b>{signal['symbol']}</b>
━━━━━━━━━━━━━━━━
Quote: <b>USDC</b> | Categoria: <code>{signal['category']}</code>
Entrada: <code>{signal['entry']}</code>
Stop Loss: <code>{signal['stop']}</code>
Take Profit: <code>{signal['target']}</code>
R:R ≈ <b>{signal['rr']}</b>
━━━━━━━━━━━━━━━━
RSI: {signal['rsi']} | Vol: {signal['vol_ratio']}x
Qualidade: {signal['quality']}/6
━━━━━━━━━━━━━━━━
Razões:
"""
    for r in signal.get("reasons", [])[:4]:
        text += f"• {r}\n"

    text += f"""
━━━━━━━━━━━━━━━━
⚠️ Apenas sinal de análise. Tu decides.
Capital pequeno = risco elevado de perda.
{now}
"""
    return text.strip()

def send_signal(signal: dict) -> bool:
    return send_message(format_signal(signal))

def send_status(msg: str) -> bool:
    return send_message(f"ℹ️ <b>Signal Desk</b>\n{msg}")
