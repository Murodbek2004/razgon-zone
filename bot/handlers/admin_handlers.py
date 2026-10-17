from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import aiosqlite

from ..config import ADMIN_IDS
from ..database import (
    get_platform_stats,
    approve_deposit,
    DB_PATH
)

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет прав доступа к панели администратора.")
        return

    stats = await get_platform_stats()

    text = (
        "👑 <b>ПАНЕЛЬ АДМИНИСТРАТОРА | RAZGON ZONE</b>\n"
        "────────────────────\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"💰 Свободный баланс клиентов: <b>{stats['total_balance']:.2f} USDT</b>\n"
        f"📈 Баланс в активной торговле: <b>{stats['in_trading']:.2f} USDT</b>\n"
        f"🏆 Суммарная выплаченная прибыль: <b>{stats['total_profit_paid']:.2f} USDT</b>\n"
        f"🚀 Активных сессий разгона: <b>{stats['active_sessions']}</b>\n"
        "────────────────────\n"
        f"📥 Ожидают подтверждения депозитов: <b>{stats['pending_deposits']}</b>\n"
        f"📤 Ожидают выплаты выводов: <b>{stats['pending_withdrawals']}</b>\n"
    )
    await message.answer(text, parse_mode="HTML")

@router.callback_query(F.data.startswith("admin_dep_ok:"))
async def on_approve_deposit(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Доступ запрещен.", show_alert=True)
        return

    dep_id = int(call.data.split(":")[1])
    res = await approve_deposit(dep_id)

    if not res:
        await call.message.edit_text(f"⚠️ Депозит #{dep_id} уже обработан или не найден.")
        await call.answer()
        return

    await call.message.edit_text(
        f"✅ <b>Депозит #{dep_id} успешно подтвержден!</b>\n"
        f"Сумма: <b>{res['amount']:.2f} USDT</b> зачислена пользователю ID: <code>{res['user_id']}</code>",
        parse_mode="HTML"
    )

    # Notify user
    try:
        await call.bot.send_message(
            chat_id=res["user_id"],
            text=(
                f"🎉 <b>Ваш депозит успешно зачислен!</b>\n\n"
                f"💵 Сумма: <b>+{res['amount']:.2f} USDT</b>\n"
                "Средства поступили на баланс и готовы к запуску разгона!"
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass

    await call.answer("Депозит подтвержден!")

@router.callback_query(F.data.startswith("admin_dep_no:"))
async def on_reject_deposit(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Доступ запрещен.", show_alert=True)
        return

    dep_id = int(call.data.split(":")[1])
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE deposits SET status = 'rejected' WHERE id = ?", (dep_id,))
        await db.commit()

    await call.message.edit_text(f"❌ Депозит #{dep_id} отклонен администратором.", parse_mode="HTML")
    await call.answer("Отклонено")

@router.callback_query(F.data.startswith("admin_wdr_ok:"))
async def on_approve_withdraw(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Доступ запрещен.", show_alert=True)
        return

    wdr_id = int(call.data.split(":")[1])
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM withdrawals WHERE id = ?", (wdr_id,)) as cursor:
            row = await cursor.fetchone()
            if not row or row["status"] != "pending":
                await call.message.edit_text(f"⚠️ Заявка на вывод #{wdr_id} уже обработана.")
                await call.answer()
                return
            wdr = dict(row)

        await db.execute("UPDATE withdrawals SET status = 'approved' WHERE id = ?", (wdr_id,))
        await db.commit()

    await call.message.edit_text(
        f"✅ <b>Вывод #{wdr_id} подтвержден (выплачен)!</b>\n"
        f"Сумма: <b>{wdr['amount']:.2f} USDT</b> на адрес: <code>{wdr['wallet_address']}</code>",
        parse_mode="HTML"
    )

    try:
        await call.bot.send_message(
            chat_id=wdr["user_id"],
            text=(
                f"🚀 <b>Ваша выплата успешно отправлена!</b>\n\n"
                f"💵 Сумма: <b>{wdr['amount']:.2f} USDT</b>\n"
                f"📍 Адрес TRC-20: <code>{wdr['wallet_address']}</code>\n\n"
                "Спасибо за работу с Razgon Zone!"
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass

    await call.answer("Вывод подтвержден!")

@router.callback_query(F.data.startswith("admin_wdr_no:"))
async def on_reject_withdraw(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Доступ запрещен.", show_alert=True)
        return

    wdr_id = int(call.data.split(":")[1])
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM withdrawals WHERE id = ?", (wdr_id,)) as cursor:
            row = await cursor.fetchone()
            if not row or row["status"] != "pending":
                await call.message.edit_text(f"⚠️ Заявка #{wdr_id} уже обработана.")
                await call.answer()
                return
            wdr = dict(row)

        # Refund user balance
        await db.execute("UPDATE withdrawals SET status = 'rejected' WHERE id = ?", (wdr_id,))
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (wdr["amount"], wdr["user_id"]))
        await db.commit()

    await call.message.edit_text(f"❌ Вывод #{wdr_id} отклонен. Средства возвращены на баланс пользователя.", parse_mode="HTML")
    await call.answer("Отклонено и возвращено")
