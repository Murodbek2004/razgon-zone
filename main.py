import asyncio
import logging
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN, PORT
from bot.database import init_db
from bot.trading_engine import engine
from bot.handlers import user_router, trading_router, admin_router
from server import create_web_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("RazgonZone")

async def run_bot_polling(dp: Dispatcher, bot: Bot):
    logger.info("Starting Telegram Bot Polling...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

async def main():
    logger.info("Initializing Razgon Zone Database...")
    await init_db()

    logger.info("Starting Algorithmic Trading Engine...")
    engine.start()

    # Create aiohttp web app for Telegram Mini App
    app = create_web_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"⚡ Razgon Zone WebApp & API server running on port {PORT}")

    if not BOT_TOKEN or "ABCdefGhIJKlmNoPQRsTUVwxyZ" in BOT_TOKEN:
        logger.warning(
            "⚠️ BOT_TOKEN не установлен в .env! WebApp сервер работает, но для работы Telegram бота укажите реальный токен от @BotFather в файле .env"
        )
        # Keep web server alive even without telegram token
        while True:
            await asyncio.sleep(3600)
        return

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Register routers
    dp.include_router(user_router)
    dp.include_router(trading_router)
    dp.include_router(admin_router)

    try:
        await run_bot_polling(dp, bot)
    finally:
        logger.info("Stopping engine and closing sessions...")
        engine.stop()
        await runner.cleanup()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Razgon Zone shut down safely.")
