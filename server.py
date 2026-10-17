import os
from pathlib import Path
from aiohttp import web
from bot.database import (
    get_or_create_user,
    get_user,
    get_active_trading_session,
    start_trading_session,
    stop_trading_session
)
from bot.trading_engine import engine
from bot.tron_service import generate_qr_code, TRON_USDT_WALLET
from bot.config import SERVICE_FEE_PERCENT

STATIC_DIR = Path(__file__).resolve().parent / "bot" / "webapp"

async def handle_index(request: web.Request) -> web.FileResponse:
    return web.FileResponse(STATIC_DIR / "index.html")

async def handle_status(request: web.Request) -> web.Response:
    user_id_raw = request.query.get("user_id")
    if not user_id_raw or not user_id_raw.isdigit():
        return web.json_response({"error": "Missing or invalid user_id"}, status=400)

    user_id = int(user_id_raw)
    user = await get_or_create_user(user_id)
    session = await get_active_trading_session(user_id)

    session_data = None
    if session:
        session_data = await engine.get_live_stats(session)

    return web.json_response({
        "user": {
            "user_id": user["user_id"],
            "balance": user["balance"],
            "in_trading_balance": user["in_trading_balance"],
            "total_profit": user["total_profit"]
        },
        "session": session_data
    })

async def handle_start(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        mode = data.get("mode", "optimal")
        amount = float(data.get("amount", 10.0))
    except Exception:
        return web.json_response({"error": "Invalid request payload"}, status=400)

    session = await start_trading_session(user_id, mode, amount)
    if not session:
        return web.json_response({"error": "Insufficient free balance or active session exists"}, status=400)

    stats = await engine.get_live_stats(session)
    return web.json_response({"ok": True, "session": stats})

async def handle_stop(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
    except Exception:
        return web.json_response({"error": "Invalid request payload"}, status=400)

    res = await stop_trading_session(user_id, service_fee_percent=SERVICE_FEE_PERCENT)
    if not res:
        return web.json_response({"error": "No active session found"}, status=400)

    return web.json_response({"ok": True, "result": res})

async def handle_deposit_info(request: web.Request) -> web.Response:
    return web.json_response({
        "network": "TRON (TRC-20)",
        "currency": "USDT",
        "address": TRON_USDT_WALLET
    })

async def handle_qr(request: web.Request) -> web.Response:
    text = request.query.get("text", TRON_USDT_WALLET)
    qr_stream = generate_qr_code(text)
    return web.Response(body=qr_stream.getvalue(), content_type="image/png")

def create_web_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/status", handle_status)
    app.router.add_post("/api/start", handle_start)
    app.router.add_post("/api/stop", handle_stop)
    app.router.add_get("/api/deposit-info", handle_deposit_info)
    app.router.add_get("/api/qr", handle_qr)
    app.router.add_static("/static/", path=str(STATIC_DIR), name="static")
    return app
