import asyncio
import logging
from aiogram import Bot
from .database import (
    get_all_deposit_wallets,
    get_user,
    is_tx_already_credited,
    auto_credit_deposit
)
from .tron_service import check_address_transfers_onchain
from .config import ADMIN_IDS, MIN_DEPOSIT

logger = logging.getLogger("RazgonZone.Watcher")

class DepositWatcher:
    def __init__(self):
        self._running = False
        self._task = None

    def start(self, bot: Bot):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._watch_loop(bot))
            logger.info("⚡ Автоматический блокчейн-наблюдатель депозитов TRON запущен!")

    def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()

    async def _watch_loop(self, bot: Bot):
        await asyncio.sleep(5)  # initial delay
        while self._running:
            try:
                wallets = await get_all_deposit_wallets()
                for w in wallets:
                    if not self._running:
                        break
                    await self._scan_wallet(bot, w["user_id"], w["tron_address"])
                    # Slight throttle between address queries
                    await asyncio.sleep(1.0)
            except Exception as e:
                logger.error(f"Ошибка в цикле сканирования блокчейна: {e}")

            # Sleep 12 seconds before next round
            await asyncio.sleep(12)

    async def _scan_wallet(self, bot: Bot, user_id: int, address: str) -> bool:
        """Scan single user wallet for confirmed USDT transfers"""
        try:
            transfers = await check_address_transfers_onchain(address, min_amount=MIN_DEPOSIT)
            for t in transfers:
                tx_hash = t["tx_hash"]
                amount = t["amount"]

                already_credited = await is_tx_already_credited(tx_hash)
                if already_credited:
                    continue

                # Auto credit
                ok, dep_dict, reason = await auto_credit_deposit(user_id, amount, tx_hash)
                if not ok:
                    logger.warning(f"Не удалось зачислить депозит {tx_hash}: {reason}")
                    continue

                user = await get_user(user_id)
                new_balance = user["balance"] if user else amount

                logger.info(f"🎉 ОБНАРУЖЕН ДЕПОЗИТ В БЛОКЧЕЙНЕ: +{amount} USDT для юзера {user_id} (Tx: {tx_hash})")

                # Send celebration message to user
                user_text = (
                    "🎉 <b>ДЕПОЗИТ УСПЕШНО ОБНАРУЖЕН В БЛОКЧЕЙНЕ!</b> ⚡\n"
                    "────────────────────\n"
                    f"💵 Пополнение: <b>+{amount:.2f} USDT</b>\n"
                    f"💰 Доступный баланс: <b>{new_balance:.2f} USDT</b>\n"
                    f"📍 Адрес зачисления: <code>{address}</code>\n"
                    f"🔗 Хеш (TxID): <code>{tx_hash[:16]}...{tx_hash[-8:]}</code>\n"
                    "────────────────────\n"
                    "🚀 Средства зачислены автоматически! Нажмите <b>«🚀 Начать разгон»</b> для старта торговли."
                )
                try:
                    await bot.send_message(chat_id=user_id, text=user_text, parse_mode="HTML")
                except Exception as ex:
                    logger.warning(f"Не удалось отправить уведомление юзеру {user_id}: {ex}")

                # Notify admins
                for admin_id in ADMIN_IDS:
                    try:
                        uname = user.get("username", "") if user else ""
                        admin_text = (
                            "⚡ <b>[НОВОЕ АВТО-ПОПОЛНЕНИЕ В СЕТИ TRON]</b>\n\n"
                            f"👤 Трейдер: @{uname or 'NoUser'} (ID: <code>{user_id}</code>)\n"
                            f"💰 Сумма: <b>+{amount:.2f} USDT</b>\n"
                            f"📍 Персональный адрес: <code>{address}</code>\n"
                            f"🔗 TxID: <code>{tx_hash}</code>\n"
                            f"<a href='https://tronscan.org/#/transaction/{tx_hash}'>Посмотреть в TronScan</a>"
                        )
                        await bot.send_message(chat_id=admin_id, text=admin_text, parse_mode="HTML")
                    except Exception:
                        pass

                return True
        except Exception as e:
            logger.error(f"Ошибка сканирования кошелька {address}: {e}")

        return False

    async def scan_now_for_user(self, bot: Bot, user_id: int, address: str) -> bool:
        """Immediate on-demand check for user button press"""
        return await self._scan_wallet(bot, user_id, address)

deposit_watcher = DepositWatcher()
