import asyncio
import logging
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.utils.token import TokenValidationError

from bot.config import BOT_TOKEN, PORT
from bot.database import init_db
from bot.trading_engine import engine
from bot.deposit_watcher import deposit_watcher
from bot.handlers import user_router, trading_router, admin_router
from server import create_web_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("RazgonZone")

async def run_bot_polling(dp: Dispatcher, bot: Bot):
    logger.info("Запуск Telegram Bot Polling...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

async def main():
    logger.info("Инициализация базы данных Razgon Zone...")
    await init_db()

    logger.info("Запуск торгового алгоритма...")
    engine.start()

    # WebApp server
    app = create_web_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"⚡ Веб-сервер и WebApp запущены на http://localhost:{PORT}")

    # Check bot token
    if not BOT_TOKEN or "ВСТАВЬТЕ_СЮДА" in BOT_TOKEN or "ABCdefGh" in BOT_TOKEN:
        logger.warning("=================================================================")
        logger.warning("⚠️  ВНИМАНИЕ: БОТ-ТОКЕН ЕЩЕ НЕ НАСТРОЕН!")
        logger.warning("👉 Откройте файл .env в этой папке и вставьте токен от @BotFather:")
        logger.warning("   BOT_TOKEN=123456789:ABC_ваш_настоящий_токен")
        logger.warning("🌐 WebApp терминал уже работает в браузере: http://localhost:8080")
        logger.warning("=================================================================")
        while True:
            await asyncio.sleep(3600)
        return

    try:
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
    except TokenValidationError:
        logger.warning("=================================================================")
        logger.warning("⚠️  ОШИБКА ФОРМАТА ТОКЕНА В .env!")
        logger.warning("👉 Токен должен иметь вид: 123456789:AABBCc_...")
        logger.warning("🌐 WebApp терминал по-прежнему доступен на http://localhost:8080")
        logger.warning("=================================================================")
        while True:
            await asyncio.sleep(3600)
        return

    dp = Dispatcher()
    dp.include_router(user_router)
    dp.include_router(trading_router)
    dp.include_router(admin_router)

    try:
        deposit_watcher.start(bot)
        await run_bot_polling(dp, bot)
    finally:
        logger.info("Остановка сервера и сохранение данных...")
        deposit_watcher.stop()
        engine.stop()
        await runner.cleanup()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Razgon Zone успешно остановлен.")
