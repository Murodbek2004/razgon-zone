import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Admin IDs list
admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(i.strip()) for i in admin_ids_raw.split(",") if i.strip().isdigit()]

# Tron TRC-20 Wallet for Deposits
TRON_USDT_WALLET = os.getenv("TRON_USDT_WALLET", "TXq1yRazgonZoneWalletTronTRC20ExampleXX").strip()

# WebApp URL
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://razgon-zone.up.railway.app").rstrip("/")

# Server Port
PORT = int(os.getenv("PORT", "8080"))

# Financial & Trading settings
MIN_DEPOSIT = float(os.getenv("MIN_DEPOSIT", "10.0"))
MIN_WITHDRAW = float(os.getenv("MIN_WITHDRAW", "10.0"))
SERVICE_FEE_PERCENT = float(os.getenv("SERVICE_FEE_PERCENT", "20.0"))  # Service share of profit
REFERRAL_BONUS_PERCENT = float(os.getenv("REFERRAL_BONUS_PERCENT", "5.0"))

# Preset Trading Modes for Razgon Zone
TRADING_MODES = {
    "safe": {
        "title": "🛡️ SAFE RUN (Консервативный)",
        "desc": "Минимальный риск, алгоритмический арбитраж. Защита от просадок.",
        "target_pnl_min": 3.5,
        "target_pnl_max": 8.0,
        "speed_label": "Низкая волатильность",
        "tick_interval": 3.0,
    },
    "optimal": {
        "title": "⚡ OPTIMAL BOOST (Сбалансированный)",
        "desc": "Трендовый скальпинг + пробой уровней BTC/ETH/SOL. Оптимальный баланс.",
        "target_pnl_min": 12.0,
        "target_pnl_max": 25.0,
        "speed_label": "Средняя волатильность",
        "tick_interval": 2.5,
    },
    "turbo": {
        "title": "🔥 TURBO RAZGON (Максимальный)",
        "desc": "Агрессивный памп-скальпинг высоковолатильных альткоинов. Быстрый разгон.",
        "target_pnl_min": 30.0,
        "target_pnl_max": 75.0,
        "speed_label": "Высокая волатильность",
        "tick_interval": 2.0,
    }
}
