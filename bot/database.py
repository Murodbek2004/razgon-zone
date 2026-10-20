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

        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_deposit_wallets (
                user_id INTEGER PRIMARY KEY,
                tron_address TEXT UNIQUE,
                private_key TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS broker_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                broker_server TEXT,
                account_number TEXT,
                account_password TEXT,
                status TEXT DEFAULT 'pending',
                reject_reason TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Performance and Anti-Duplication Indexes
        await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_deposits_tx_hash ON deposits(tx_hash);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_deposits_user ON deposits(user_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_withdrawals_status ON withdrawals(status);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_status ON trading_sessions(user_id, status);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_user_wallets_addr ON user_deposit_wallets(tron_address);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_broker_user ON broker_accounts(user_id);")

        # Database migrations for new features
        try:
            await db.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'ru';")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE trading_sessions ADD COLUMN note TEXT DEFAULT '';")
        except Exception:
            pass
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

async def auto_credit_deposit(user_id: int, amount: float, tx_hash: str):
    """
    Checks if tx_hash already used.
    If not, creates deposit with status 'approved', credits balance instantly,
    awards referral bonus, and returns (True, deposit_dict, 'ok').
    """
    clean_tx = tx_hash.strip().lower()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id, user_id FROM deposits WHERE LOWER(tx_hash) = ? AND status = 'approved'", (clean_tx,)) as cursor:
            existing = await cursor.fetchone()
            if existing:
                return False, None, "Данный TxID уже был ранее активирован и зачислен на баланс!"

        cursor = await db.execute(
            "INSERT INTO deposits (user_id, amount, tx_hash, status) VALUES (?, ?, ?, 'approved')",
            (user_id, amount, clean_tx)
        )
        dep_id = cursor.lastrowid

        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

        async with db.execute("SELECT * FROM deposits WHERE id = ?", (dep_id,)) as cursor:
            dep_dict = dict(await cursor.fetchone())
            return True, dep_dict, "ok"

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

async def get_top_traders():
    """Returns top traders list for Hall of Fame leaderboard"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT user_id, username, first_name, total_profit, in_trading_balance FROM users ORDER BY total_profit DESC LIMIT 10"
        ) as cursor:
            rows = await cursor.fetchall()
            real_leaders = [dict(r) for r in rows if r["total_profit"] > 0]

    # Pre-populated leaderboard benchmark participants
    benchmarks = [
        {"name": "WhaleRider_X", "profit": 4820.50, "pnl_pct": 345.2, "mode": "🔥 Turbo"},
        {"name": "CryptoBull_77", "profit": 3150.00, "pnl_pct": 224.8, "mode": "🔥 Turbo"},
        {"name": "Satoshi_Pulse", "profit": 1840.20, "pnl_pct": 175.4, "mode": "⚡ Optimal"},
        {"name": "ApexScalper", "profit": 1290.80, "pnl_pct": 138.0, "mode": "⚡ Optimal"},
        {"name": "DeltaHedge_Pro", "profit": 920.40, "pnl_pct": 94.5, "mode": "🛡️ Safe"},
    ]
    return real_leaders, benchmarks

async def get_or_create_user_wallet(user_id: int) -> Tuple[str, str]:
    """Retrieves or creates unique dedicated TRON address and private key for a user"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT tron_address, private_key FROM user_deposit_wallets WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row["tron_address"], row["private_key"]

    # Generate new dedicated address
    from .tron_service import generate_tron_keypair
    priv_key, address = generate_tron_keypair()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO user_deposit_wallets (user_id, tron_address, private_key) VALUES (?, ?, ?)",
            (user_id, address, priv_key)
        )
        await db.commit()

    return address, priv_key

async def get_all_deposit_wallets() -> List[Dict[str, Any]]:
    """Returns all dedicated user deposit wallets with user metadata and balances"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT w.user_id, w.tron_address, w.private_key, w.created_at,
                   u.username, u.first_name, u.balance, u.in_trading_balance
            FROM user_deposit_wallets w
            LEFT JOIN users u ON w.user_id = u.user_id
            ORDER BY w.created_at DESC
        """) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def is_tx_already_credited(tx_hash: str) -> bool:
    """Check if transaction was already processed and credited"""
    clean_tx = tx_hash.strip().lower()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM deposits WHERE LOWER(tx_hash) = ? AND status = 'approved'", (clean_tx,)) as cursor:
            row = await cursor.fetchone()
            return row is not None

async def admin_get_user_card(identifier: str) -> Optional[Dict[str, Any]]:
    """Lookup user by user_id or @username and fetch full profile card"""
    clean_id = identifier.strip().lstrip("@")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if clean_id.isdigit():
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (int(clean_id),))
        else:
            cursor = await db.execute("SELECT * FROM users WHERE LOWER(username) = ?", (clean_id.lower(),))
        user_row = await cursor.fetchone()
        if not user_row:
            return None
        user = dict(user_row)

        # Active session
        async with db.execute("SELECT * FROM trading_sessions WHERE user_id = ? AND status = 'active' LIMIT 1", (user["user_id"],)) as c_sess:
            sess_row = await c_sess.fetchone()
            session = dict(sess_row) if sess_row else None

        # Dedicated wallet
        async with db.execute("SELECT tron_address, private_key FROM user_deposit_wallets WHERE user_id = ?", (user["user_id"],)) as c_w:
            w_row = await c_w.fetchone()
            wallet = dict(w_row) if w_row else None

        # Stats
        async with db.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0.0) FROM deposits WHERE user_id = ? AND status = 'approved'", (user["user_id"],)) as c_dep:
            dep_cnt, dep_sum = await c_dep.fetchone()

        async with db.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0.0) FROM withdrawals WHERE user_id = ? AND status = 'approved'", (user["user_id"],)) as c_wdr:
            wdr_cnt, wdr_sum = await c_wdr.fetchone()

        return {
            "user": user,
            "session": session,
            "wallet": wallet,
            "deposits_count": dep_cnt,
            "deposits_sum": round(dep_sum, 2),
            "withdrawals_count": wdr_cnt,
            "withdrawals_sum": round(wdr_sum, 2),
        }

async def admin_modify_balance(user_id: int, delta: float) -> Tuple[bool, float, str]:
    """Admin balance adjustment (+ or -)"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return False, 0.0, "Пользователь не найден в базе данных."
            current = row["balance"]

        new_bal = round(current + delta, 2)
        if new_bal < 0:
            return False, current, f"Баланс не может быть отрицательным (текущий: {current:.2f} USDT)."

        await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_bal, user_id))
        await db.commit()
        return True, new_bal, "ok"

async def admin_set_balance(user_id: int, exact_amount: float) -> Tuple[bool, float, str]:
    """Admin sets exact balance for user"""
    if exact_amount < 0:
        return False, 0.0, "Баланс не может быть отрицательным."
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return False, 0.0, "Пользователь не найден в базе данных."
        new_bal = round(float(exact_amount), 2)
        await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_bal, user_id))
        await db.commit()
        return True, new_bal, "ok"

async def get_all_user_ids() -> List[int]:
    """Returns all registered user IDs"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]

async def get_all_users_with_lang() -> List[Dict[str, Any]]:
    """Returns all registered users with their language"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT user_id, COALESCE(language, 'ru') as language FROM users") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_recent_deposits(limit: int = 10) -> List[Dict[str, Any]]:
    """Returns recent deposits with user info"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT d.*, u.username, u.first_name 
            FROM deposits d 
            LEFT JOIN users u ON d.user_id = u.user_id 
            ORDER BY d.id DESC LIMIT ?
        """, (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_pending_withdrawals_list() -> List[Dict[str, Any]]:
    """Returns pending withdrawals with user info"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT w.*, u.username, u.first_name 
            FROM withdrawals w 
            LEFT JOIN users u ON w.user_id = u.user_id 
            WHERE w.status = 'pending' 
            ORDER BY w.id ASC
        """) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_user_lang(user_id: int) -> str:
    """Returns preferred language of user ('ru' or 'uz')"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT language FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                return row[0]
    return "ru"

async def set_user_lang(user_id: int, lang: str):
    """Sets preferred language of user ('ru' or 'uz')"""
    clean_lang = "uz" if lang == "uz" else "ru"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET language = ? WHERE user_id = ?", (clean_lang, user_id))
        await db.commit()

async def start_simple_trading(user_id: int) -> Optional[Dict[str, Any]]:
    """Starts trading with all available balance (minimum 40.0 USDT)"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT balance, in_trading_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
            if not user or user["balance"] < 40.0:
                return None
            amount = round(user["balance"], 2)

        await db.execute(
            "UPDATE users SET balance = 0.0, in_trading_balance = in_trading_balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
        cursor = await db.execute(
            "INSERT INTO trading_sessions (user_id, mode, deposit_amount, current_profit, status) VALUES (?, 'auto', ?, 0.0, 'active')",
            (user_id, amount)
        )
        session_id = cursor.lastrowid
        await db.commit()

        async with db.execute("SELECT * FROM trading_sessions WHERE id = ?", (session_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row)

async def get_active_sessions_for_admin() -> List[Dict[str, Any]]:
    """Returns active trading sessions awaiting admin final report"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT s.*, u.username, u.first_name, COALESCE(u.language, 'ru') as language
            FROM trading_sessions s
            LEFT JOIN users u ON s.user_id = u.user_id
            WHERE s.status = 'active'
            ORDER BY s.id DESC
        """) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def admin_complete_session(session_id: int, profit_amount: float, note: str = "") -> Optional[Dict[str, Any]]:
    """
    Admin completes session with custom profit (USDT).
    0% fee: entire deposit + profit credited to user balance!
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM trading_sessions WHERE id = ? AND status = 'active'", (session_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            sess = dict(row)

        user_id = sess["user_id"]
        deposit = sess["deposit_amount"]
        profit = round(float(profit_amount), 2)
        total_returned = round(deposit + profit, 2)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        await db.execute(
            "UPDATE trading_sessions SET status = 'completed', current_profit = ?, stopped_at = ?, note = ? WHERE id = ?",
            (profit, now, note, session_id)
        )
        await db.execute(
            "UPDATE users SET balance = balance + ?, in_trading_balance = MAX(0.0, in_trading_balance - ?), total_profit = total_profit + ? WHERE user_id = ?",
            (total_returned, deposit, profit, user_id)
        )
        await db.commit()

        # Fetch updated user info
        async with db.execute("SELECT username, first_name, COALESCE(language, 'ru') as language, balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            u_row = await cursor.fetchone()

        sess["profit"] = profit
        sess["total_returned"] = total_returned
        sess["pnl_pct"] = round((profit / deposit) * 100.0, 1) if deposit > 0 else 0.0
        sess["note"] = note
        sess["user_lang"] = u_row["language"] if u_row else "ru"
        sess["user_first_name"] = u_row["first_name"] if u_row else "Трейдер"
        sess["new_balance"] = u_row["balance"] if u_row else total_returned
        return sess

async def user_cancel_trading_session(user_id: int) -> Optional[float]:
    """
    User manually stops trading.
    0% fee: entire deposit is returned 100% to free balance!
    Returns returned deposit amount or None.
    """
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

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        deposit = sess["deposit_amount"]

        await db.execute(
            "UPDATE trading_sessions SET status = 'stopped_by_user', stopped_at = ? WHERE id = ?",
            (now, sess["id"])
        )
        await db.execute(
            "UPDATE users SET balance = balance + ?, in_trading_balance = MAX(0.0, in_trading_balance - ?) WHERE user_id = ?",
            (deposit, deposit, user_id)
        )
        await db.commit()
        return deposit

async def clean_test_wallets() -> int:
    """Removes test users and their wallets created during test suites"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            DELETE FROM user_deposit_wallets 
            WHERE user_id IN (
                SELECT user_id FROM users 
                WHERE username IN ('test_trader', 'uz_trader') 
                   OR first_name IN ('Alex', 'Bekzod')
            )
        """)
        deleted_count = cursor.rowcount
        await db.execute("""
            DELETE FROM users 
            WHERE username IN ('test_trader', 'uz_trader') 
               OR first_name IN ('Alex', 'Bekzod')
        """)
        await db.commit()
        return deleted_count

# --- Broker Account Functions ---
async def save_broker_account(user_id: int, broker_server: str, account_number: str, account_password: str) -> int:
    """Saves new broker credentials for user, setting status to pending"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO broker_accounts (user_id, broker_server, account_number, account_password, status)
               VALUES (?, ?, ?, ?, 'pending')""",
            (user_id, broker_server.strip(), account_number.strip(), account_password.strip())
        )
        acc_id = cursor.lastrowid
        await db.commit()
        return acc_id

async def get_user_broker_account(user_id: int) -> Optional[Dict[str, Any]]:
    """Gets the most recent broker account for a user"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM broker_accounts WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_broker_account_by_id(account_id: int) -> Optional[Dict[str, Any]]:
    """Gets a broker account by ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM broker_accounts WHERE id = ?",
            (account_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_broker_status(account_id: int, status: str, reject_reason: str = "") -> Optional[Dict[str, Any]]:
    """Updates broker account status and returns updated record with user info"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            "UPDATE broker_accounts SET status = ?, reject_reason = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, reject_reason, account_id)
        )
        await db.commit()
        async with db.execute("""
            SELECT b.*, u.username, u.first_name, COALESCE(u.language, 'ru') as language
            FROM broker_accounts b
            LEFT JOIN users u ON b.user_id = u.user_id
            WHERE b.id = ?
        """, (account_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_all_broker_accounts(limit: int = 50) -> List[Dict[str, Any]]:
    """Gets all broker accounts for admin panel"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT b.*, u.username, u.first_name
            FROM broker_accounts b
            LEFT JOIN users u ON b.user_id = u.user_id
            ORDER BY b.id DESC LIMIT ?
        """, (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]




