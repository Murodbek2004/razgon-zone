import asyncio
import random
import time
from typing import Dict, Any, List, Optional
from .database import (
    get_all_active_sessions,
    update_session_profit,
    add_or_update_deal,
    get_session_deals
)
from .config import TRADING_MODES

PAIRS = [
    {"symbol": "BTC/USDT", "base_price": 92450.0, "step": 150.0},
    {"symbol": "ETH/USDT", "base_price": 3150.0, "step": 12.0},
    {"symbol": "SOL/USDT", "base_price": 195.0, "step": 1.5},
    {"symbol": "TON/USDT", "base_price": 5.40, "step": 0.08},
    {"symbol": "SUI/USDT", "base_price": 2.85, "step": 0.05},
]

class TradingEngine:
    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        # In-memory fast cache for live tick calculations
        self._sessions_cache: Dict[int, Dict[str, Any]] = {}

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._trade_loop())

    def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()

    async def _trade_loop(self):
        while self._running:
            try:
                active_sessions = await get_all_active_sessions()
                for sess in active_sessions:
                    await self._process_session(sess)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[TradingEngine Error] {e}")
            await asyncio.sleep(3.0)

    async def _process_session(self, session: Dict[str, Any]):
        sess_id = session["id"]
        mode_key = session.get("mode", "optimal")
        mode_cfg = TRADING_MODES.get(mode_key, TRADING_MODES["optimal"])

        deposit = session["deposit_amount"]
        current_profit = session["current_profit"]

        # Calculate incremental PnL tick
        if mode_key == "safe":
            pnl_increment = random.uniform(0.05, 0.25) * (deposit / 100.0)
        elif mode_key == "optimal":
            pnl_increment = random.uniform(0.15, 0.65) * (deposit / 100.0)
        else: # turbo
            pnl_increment = random.uniform(0.35, 1.45) * (deposit / 100.0)

        # Micro-fluctuation (sometimes slight correction, but positive drift)
        if random.random() < 0.15:
            pnl_increment = -abs(pnl_increment * 0.4)

        new_profit = round(max(0.0, current_profit + pnl_increment), 2)
        await update_session_profit(sess_id, new_profit)

        # Occasionally add/update simulated deal
        if random.random() < 0.35:
            pair = random.choice(PAIRS)
            side = random.choice(["LONG 📈", "SHORT 📉"])
            entry = pair["base_price"] + random.uniform(-pair["step"], pair["step"])
            delta_p = random.uniform(0.2, 1.8) * (1 if "LONG" in side else -1)
            curr = entry + (pair["step"] * (delta_p / 100.0))
            deal_pnl = round(deposit * random.uniform(0.01, 0.04), 2)
            deal_pct = round((deal_pnl / deposit) * 100.0, 2)

            await add_or_update_deal(
                session_id=sess_id,
                pair=pair["symbol"],
                side=side,
                entry_price=round(entry, 2),
                current_price=round(curr, 2),
                pnl_amount=deal_pnl,
                pnl_percent=deal_pct
            )

    async def get_live_stats(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive live data for bot messages and WebApp"""
        sess_id = session["id"]
        mode_key = session.get("mode", "optimal")
        mode_cfg = TRADING_MODES.get(mode_key, TRADING_MODES["optimal"])

        deposit = session["deposit_amount"]
        profit = session.get("current_profit", 0.0)
        total_balance = round(deposit + profit, 2)
        pnl_percent = round((profit / deposit) * 100.0, 2) if deposit > 0 else 0.0

        deals = await get_session_deals(sess_id)

        # Calculate uptime
        started = session.get("started_at")

        # Speed indicator (0-100 gauge)
        if mode_key == "safe":
            speed_val = min(40, int(20 + pnl_percent * 3))
        elif mode_key == "optimal":
            speed_val = min(75, int(45 + pnl_percent * 2))
        else:
            speed_val = min(100, int(70 + pnl_percent * 1.5))

        return {
            "session_id": sess_id,
            "mode_title": mode_cfg["title"],
            "mode_key": mode_key,
            "speed_label": mode_cfg["speed_label"],
            "speed_val": speed_val,
            "deposit": deposit,
            "profit": profit,
            "total_balance": total_balance,
            "pnl_percent": pnl_percent,
            "started_at": started,
            "deals": deals,
            "active": session.get("status") == "active"
        }

engine = TradingEngine()
