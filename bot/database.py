import aiosqlite
from pathlib import Path
from typing import Optional, Dict, Any, List
import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "razgon_zone.sqlite3"

async def init_db():
    """Initialize database tables"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance REAL DEFAULT 0.0,
                in_trading_balance REAL DEFAULT 0.0,
                total_profit REAL DEFAULT 0.0,
                referrer_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                tx_hash TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                wallet_address TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS trading_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                mode TEXT,
                deposit_amount REAL,
                current_profit REAL DEFAULT 0.0,
                status TEXT DEFAULT 'active',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                stopped_at TIMESTAMP
            );
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS trade_deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                pair TEXT,
                side TEXT,
                entry_price REAL,
                current_price REAL,
                pnl_amount REAL DEFAULT 0.0,
                pnl_percent REAL DEFAULT 0.0,
                status TEXT DEFAULT 'OPEN',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await db.commit()

async def get_or_create_user(user_id: int, username: str = "", first_name: str = "", referrer_id: Optional[int] = None) -> Dict[str, Any]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                # Update username if changed
                await db.execute(
                    "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
                    (username, first_name, user_id)
                )
                await db.commit()
                return dict(row)

        # Create new user
        # Avoid self-referral
        if referrer_id == user_id:
            referrer_id = None

        await db.execute(
            """INSERT INTO users (user_id, username, first_name, balance, in_trading_balance, total_profit, referrer_id)
               VALUES (?, ?, ?, 0.0, 0.0, 0.0, ?)""",
            (user_id, username, first_name, referrer_id)
        )
        await db.commit()

        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            new_row = await cursor.fetchone()
            return dict(new_row)

async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_balance(user_id: int, delta_amount: float) -> float:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (delta_amount, user_id))
        await db.commit()
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            res = await cursor.fetchone()
            return res[0] if res else 0.0

async def create_deposit(user_id: int, amount: float, tx_hash: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO deposits (user_id, amount, tx_hash, status) VALUES (?, ?, ?, 'pending')",
            (user_id, amount, tx_hash)
        )
        await db.commit()
        return cursor.lastrowid

async def approve_deposit(deposit_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM deposits WHERE id = ?", (deposit_id,)) as cursor:
            dep = await cursor.fetchone()
            if not dep or dep["status"] != "pending":
                return None
            dep_dict = dict(dep)

        await db.execute("UPDATE deposits SET status = 'approved' WHERE id = ?", (deposit_id,))
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (dep_dict["amount"], dep_dict["user_id"]))

        # Check referral bonus
        async with db.execute("SELECT referrer_id FROM users WHERE user_id = ?", (dep_dict["user_id"],)) as cursor:
            user_row = await cursor.fetchone()
            if user_row and user_row[0]:
                ref_id = user_row[0]
                bonus = round(dep_dict["amount"] * 0.05, 2)
                if bonus > 0:
                    await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (bonus, ref_id))

        await db.commit()
        return dep_dict

async def create_withdrawal(user_id: int, amount: float, wallet_address: str) -> Optional[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row or row["balance"] < amount:
                return None

        # Lock balance
        await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
        cursor = await db.execute(
            "INSERT INTO withdrawals (user_id, amount, wallet_address, status) VALUES (?, ?, ?, 'pending')",
            (user_id, amount, wallet_address)
        )
        await db.commit()
        return cursor.lastrowid

async def get_active_trading_session(user_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM trading_sessions WHERE user_id = ? AND status = 'active' ORDER BY id DESC LIMIT 1",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def start_trading_session(user_id: int, mode: str, amount: float) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT balance, in_trading_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
            if not user or user["balance"] < amount or amount <= 0:
                return None

        # Deduct from free balance, add to in_trading_balance
        await db.execute(
            "UPDATE users SET balance = balance - ?, in_trading_balance = in_trading_balance + ? WHERE user_id = ?",
            (amount, amount, user_id)
        )
        cursor = await db.execute(
            "INSERT INTO trading_sessions (user_id, mode, deposit_amount, current_profit, status) VALUES (?, ?, ?, 0.0, 'active')",
            (user_id, mode, amount)
        )
        session_id = cursor.lastrowid
        await db.commit()

        async with db.execute("SELECT * FROM trading_sessions WHERE id = ?", (session_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row)

async def stop_trading_session(user_id: int, service_fee_percent: float = 20.0) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM trading_sessions WHERE user_id = ? AND status = 'active' ORDER BY id DESC LIMIT 1",
            (user_id,)
        ) as cursor:
            session = await cursor.fetchone()
            if not session:
                return None
            sess = dict(session)

        # Calculate final profit & commission
        gross_profit = max(0.0, sess["current_profit"])
        fee = round(gross_profit * (service_fee_percent / 100.0), 2)
        net_profit = round(gross_profit - fee, 2)
        total_returned = round(sess["deposit_amount"] + net_profit, 2)

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        await db.execute(
            "UPDATE trading_sessions SET status = 'stopped', stopped_at = ? WHERE id = ?",
            (now, sess["id"])
        )
        await db.execute(
            "UPDATE users SET balance = balance + ?, in_trading_balance = MAX(0.0, in_trading_balance - ?), total_profit = total_profit + ? WHERE user_id = ?",
            (total_returned, sess["deposit_amount"], net_profit, user_id)
        )
        await db.execute(
            "UPDATE trade_deals SET status = 'CLOSED' WHERE session_id = ? AND status = 'OPEN'",
            (sess["id"],)
        )
        await db.commit()

        sess["fee"] = fee
        sess["net_profit"] = net_profit
        sess["total_returned"] = total_returned
        return sess

async def update_session_profit(session_id: int, new_profit: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE trading_sessions SET current_profit = ? WHERE id = ?", (new_profit, session_id))
        await db.commit()

async def get_session_deals(session_id: int) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM trade_deals WHERE session_id = ? ORDER BY id DESC LIMIT 10", (session_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def add_or_update_deal(session_id: int, pair: str, side: str, entry_price: float, current_price: float, pnl_amount: float, pnl_percent: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO trade_deals (session_id, pair, side, entry_price, current_price, pnl_amount, pnl_percent, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN')""",
            (session_id, pair, side, entry_price, current_price, pnl_amount, pnl_percent)
        )
        await db.commit()

async def get_all_active_sessions() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM trading_sessions WHERE status = 'active'") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_platform_stats() -> Dict[str, Any]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*), SUM(balance), SUM(in_trading_balance), SUM(total_profit) FROM users") as c1:
            u_count, u_bal, u_trade, u_prof = await c1.fetchone()
        async with db.execute("SELECT COUNT(*) FROM trading_sessions WHERE status = 'active'") as c2:
            active_sessions = (await c2.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM deposits WHERE status = 'pending'") as c3:
            pending_deposits = (await c3.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM withdrawals WHERE status = 'pending'") as c4:
            pending_withdrawals = (await c4.fetchone())[0]

        return {
            "total_users": u_count or 0,
            "total_balance": round(u_bal or 0.0, 2),
            "in_trading": round(u_trade or 0.0, 2),
            "total_profit_paid": round(u_prof or 0.0, 2),
            "active_sessions": active_sessions or 0,
            "pending_deposits": pending_deposits or 0,
            "pending_withdrawals": pending_withdrawals or 0
        }
