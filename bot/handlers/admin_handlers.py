from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import aiosqlite
from datetime import datetime

from ..config import ADMIN_IDS
from ..database import (
    get_platform_stats,
    get_all_deposit_wallets,
    admin_get_user_card,
    admin_modify_balance,
    get_all_user_ids,
    get_recent_deposits,
    get_pending_withdrawals_list,
    get_active_sessions_for_admin,
    admin_complete_session,
    clean_test_wallets,
    DB_PATH
)
from ..tron_service import get_tron_account_balance
from ..localization import tr
from ..keyboards import (
    get_admin_dashboard_keyboard,
    get_admin_withdraw_keyboard,
    get_main_reply_keyboard
)

router = Router()

class AdminStates(StatesGroup):
    waiting_for_user_query = State()
    waiting_for_balance_delta = State()
    waiting_for_broadcast = State()
    waiting_for_session_profit = State()
    waiting_for_direct_msg_recipient = State()
    waiting_for_direct_msg_text = State()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def build_stats_text() -> str:
    stats = await get_platform_stats()
    return (
        "👑 <b>КОМАНДНЫЙ ЦЕНТР АДМИНИСТРАТОРА | RAZGON ZONE</b>\n"
        "────────────────────\n"
        f"👥 Зарегистрировано трейдеров: <b>{stats['total_users']}</b>\n"
        f"💰 Свободный баланс клиентов: <b>{stats['total_balance']:.2f} USDT</b>\n"
        f"📈 Капитал в активном разгоне: <b>{stats['in_trading']:.2f} USDT</b>\n"
        f"🏆 Суммарная выплаченная прибыль: <b>{stats['total_profit_paid']:.2f} USDT</b>\n"
        f"🚀 Активных торговых сессий: <b>{stats['active_sessions']}</b>\n"
        "────────────────────\n"
        f"📥 Необработанных депозитов: <b>{stats['pending_deposits']}</b>\n"
        f"📤 Ожидающих заявок на вывод: <b>{stats['pending_withdrawals']}</b>\n\n"
        "<i>Используйте кнопки управления ниже:</i>"
    )

@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет прав доступа к панели администратора.")
        return
    await state.clear()
    text = await build_stats_text()
    await message.answer(text, reply_markup=get_admin_dashboard_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "adm_refresh_stats")
async def on_refresh_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    text = await build_stats_text()
    try:
        await call.message.edit_text(text, reply_markup=get_admin_dashboard_keyboard(), parse_mode="HTML")
    except Exception:
        pass
    await call.answer("📊 Статистика обновлена!")

# --- Active Sessions & Reporting by Admin ---
@router.callback_query(F.data == "adm_active_sessions")
async def on_view_active_sessions(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    sessions = await get_active_sessions_for_admin()
    if not sessions:
        await call.message.answer(
            "ℹ️ <b>Сейчас нет активных разгонов в работе.</b>\n\n"
            "Как только пользователь запустит разгон со своего депозита, он отобразится здесь с возможностью завершить торги и выслать отчет с прибылью.",
            parse_mode="HTML"
        )
        await call.answer()
        return

    await call.message.answer(
        f"🚀 <b>АКТИВНЫЕ РАЗГОНЫ В РАБОТЕ ({len(sessions)} шт.):</b>",
        parse_mode="HTML"
    )

    for s in sessions:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"🏁 Завершить разгон #{s['id']} и отправить отчет",
                callback_data=f"adm_finish_sess:{s['id']}"
            )]
        ])
        text = (
            f"🚀 <b>СЕССИЯ #{s['id']}</b>\n"
            f"────────────────────\n"
            f"👤 Трейдер: <b>{s.get('first_name') or 'N/A'}</b> (@{s.get('username') or 'NoUsername'})\n"
            f"🆔 User ID: <code>{s['user_id']}</code>\n"
            f"💵 Депозит в разгоне: <b>{s['deposit_amount']:.2f} USDT</b>\n"
            f"🌐 Язык интерфейса: <b>{s.get('language', 'ru').upper()}</b>\n"
            f"⏱ Время старта: <code>{s['started_at']}</code>\n"
            f"────────────────────\n"
            f"Нажмите кнопку ниже, чтобы завершить торги и отправить отчет:"
        )
        await call.message.answer(text, reply_markup=kb, parse_mode="HTML")

    await call.answer()

@router.callback_query(F.data.startswith("adm_finish_sess:"))
async def on_finish_session_click(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return

    session_id = int(call.data.split(":")[1])
    await state.update_data(finish_session_id=session_id)
    await state.set_state(AdminStates.waiting_for_session_profit)

    prompt = (
        f"🏁 <b>ЗАВЕРШЕНИЕ РАЗГОНА | СЕССИЯ #{session_id}</b>\n\n"
        "Введите сумму <b>чистой прибыли (в USDT)</b>, которую заработал алгоритм для этого пользователя (например: <code>35.50</code>):\n\n"
        "💡 <i>Депозит пользователя вернется автоматически + эта чистая прибыль поступит на баланс (0% комиссии). "
        "Бот мгновенно сформирует и отправит официальный отчет пользователю на его языке!</i>\n\n"
        "<i>(Или отправьте 'отмена')</i>"
    )
    await call.message.answer(prompt, parse_mode="HTML")
    await call.answer()

@router.message(AdminStates.waiting_for_session_profit)
async def process_session_profit(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    if text.lower() == "отмена":
        await state.clear()
        await message.answer("❌ Завершение сессии отменено.")
        return

    try:
        profit = float(text.replace(",", "."))
        if profit < 0:
            await message.answer("⚠️ Сумма прибыли не может быть отрицательной. Введите число >= 0:")
            return
    except ValueError:
        await message.answer("⚠️ Введите корректное число прибыли (например: 45.20):")
        return

    data = await state.get_data()
    session_id = data["finish_session_id"]
    await state.clear()

    s_dict = await admin_complete_session(session_id, profit, note="")
    if not s_dict:
        await message.answer(f"❌ Ошибка: Сессия #{session_id} не найдена или уже завершена.")
        return

    user_id = s_dict["user_id"]
    user_lang = s_dict.get("user_lang") or s_dict.get("language") or "ru"
    deposit = s_dict["deposit_amount"]
    total = s_dict["total_returned"]
    pnl_pct = s_dict["pnl_pct"]
    date_str = datetime.now().strftime("%d.%m.%Y %H:%M")

    # Send official report to user in their language
    report_text = tr(
        "session_report",
        user_lang,
        deposit=deposit,
        profit=profit,
        pnl_pct=pnl_pct,
        total=total,
        note="",
        date=date_str
    )

    delivery_status = "✅ Отчет успешно доставлен пользователю"
    try:
        await message.bot.send_message(
            chat_id=user_id,
            text=report_text,
            reply_markup=get_main_reply_keyboard(lang=user_lang, is_trading=False),
            parse_mode="HTML"
        )
    except Exception as e:
        delivery_status = f"⚠️ Ошибка отправки отчета пользователю: {e}"

    # Confirm to admin
    admin_confirm = (
        f"🎉 <b>РАЗГОН #{session_id} УСПЕШНО ЗАВЕРШЕН!</b>\n\n"
        f"👤 Клиент ID: <code>{user_id}</code>\n"
        f"💵 Возвращен депозит: <b>{deposit:.2f} USDT</b>\n"
        f"📈 Начислена чистая прибыль: <b>+{profit:.2f} USDT</b> (+{pnl_pct:.1f}%)\n"
        f"💰 Итого зачислено на баланс: <b>{total:.2f} USDT</b>\n"
        f"🌐 Язык отчета: <b>{user_lang.upper()}</b>\n"
        f"📩 Статус: <b>{delivery_status}</b>"
    )
    await message.answer(admin_confirm, parse_mode="HTML")

# --- Wallets, Users & Withdrawals ---
@router.callback_query(F.data == "adm_view_wallets")
@router.message(Command("wallets"))
async def admin_list_wallets(event: Message | CallbackQuery):
    user_id = event.from_user.id
    if not is_admin(user_id):
        return

    wallets = await get_all_deposit_wallets()
    if not wallets:
        msg = "ℹ️ Пользователи еще не генерировали персональные кошельки пополнения."
        if isinstance(event, Message):
            await event.answer(msg)
        else:
            await event.message.answer(msg)
            await event.answer()
        return

    # Progress message
    status_msg = None
    if isinstance(event, Message):
        status_msg = await event.answer("⏳ <i>Опрашиваю блокчейн TRON и запрашиваю актуальные балансы...</i>", parse_mode="HTML")
    else:
        await event.answer("⏳ Сканирую ончейн-балансы кошельков...")

    header = f"🔑 <b>КОШЕЛЬКИ КЛИЕНТОВ И ОНЧЕЙН-БАЛАНСЫ ({len(wallets)} шт.)</b>\n────────────────────\n"
    
    entries = []
    for w in wallets:
        addr = w['tron_address']
        bal = await get_tron_account_balance(addr)
        u_name = f"@{w['username']}" if w.get('username') else (w.get('first_name') or 'N/A')
        bot_bal = w.get('balance', 0.0) or 0.0
        in_trade = w.get('in_trading_balance', 0.0) or 0.0

        entry = (
            f"👤 <b>Клиент:</b> {u_name} (ID: <code>{w['user_id']}</code>)\n"
            f"📍 <b>TRC-20:</b> <code>{addr}</code>\n"
            f"🌐 <b>В блокчейне TRON:</b> <b>{bal['usdt']:.2f} USDT</b> | {bal['trx']:.2f} TRX\n"
            f"💰 <b>В боте:</b> {bot_bal:.2f} USDT" + (f" (В разгоне: {in_trade:.2f} USDT)" if in_trade > 0 else "") + "\n"
            f"🔐 <b>Private Key:</b> <tg-spoiler><code>{w['private_key']}</code></tg-spoiler>\n"
            f"🔗 <a href='https://tronscan.org/#/address/{addr}'>Проверить в TronScan</a>\n"
            "────────────────────\n"
        )
        entries.append(entry)

    footer = "💡 <i>Все приватные ключи под спойлером. Нажмите, чтобы скопировать.</i>"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Обновить балансы", callback_data="adm_view_wallets"),
            InlineKeyboardButton(text="🧹 Очистить тестовые", callback_data="adm_clean_test_wallets")
        ],
        [
            InlineKeyboardButton(text="❌ Закрыть", callback_data="adm_cancel")
        ]
    ])

    # Split into chunks under 3800 chars
    chunks = []
    current_chunk = header
    for entry in entries:
        if len(current_chunk) + len(entry) + len(footer) > 3800:
            chunks.append(current_chunk)
            current_chunk = entry
        else:
            current_chunk += entry
    current_chunk += footer
    chunks.append(current_chunk)

    target_chat = event.from_user.id
    if status_msg:
        try:
            await status_msg.delete()
        except Exception:
            pass

    for i, chunk in enumerate(chunks):
        markup = kb if i == len(chunks) - 1 else None
        if isinstance(event, Message):
            await event.answer(chunk, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)
        else:
            await event.message.answer(chunk, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)

@router.callback_query(F.data == "adm_clean_test_wallets")
async def on_clean_test_wallets(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    deleted_cnt = await clean_test_wallets()
    await call.answer(f"🧹 Удалено {deleted_cnt} тестовых кошельков!", show_alert=True)
    await admin_list_wallets(call)

@router.callback_query(F.data == "adm_find_user")
async def on_find_user_prompt(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_user_query)
    text = (
        "🔍 <b>ПОИСК И УПРАВЛЕНИЕ СЧЕТОМ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        "Отправьте сюда <b>Telegram ID</b> (например: <code>12345678</code>) или <b>@username</b> пользователя:"
    )
    await call.message.answer(text, parse_mode="HTML")
    await call.answer()

@router.message(AdminStates.waiting_for_user_query)
async def process_user_query(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    card = await admin_get_user_card(message.text.strip())
    if not card:
        await message.answer("❌ Пользователь с таким ID или логином не найден в базе данных.")
        await state.clear()
        return

    u = card["user"]
    sess = card["session"]
    w = card["wallet"]

    status_str = f"🟢 В РАЗГОНЕ ({sess['deposit_amount']:.2f} USDT)" if sess else "⚪️ Торговля остановлена"
    wallet_str = f"<code>{w['tron_address']}</code>\n🔐 Key: <code>{w['private_key']}</code>" if w else "<i>Еще не создан</i>"

    text = (
        "👤 <b>КАРТОЧКА СЧЕТА ПОЛЬЗОВАТЕЛЯ</b>\n"
        "────────────────────\n"
        f"🆔 ID: <code>{u['user_id']}</code> | @{u['username'] or 'NoUsername'}\n"
        f"👤 Имя: <b>{u['first_name']}</b> | Язык: <b>{u.get('language', 'ru').upper()}</b>\n"
        f"💰 Свободный баланс: <b>{u['balance']:.2f} USDT</b>\n"
        f"📈 Баланс в разгоне: <b>{u['in_trading_balance']:.2f} USDT</b>\n"
        f"🏆 Общий заработок: <b>{u['total_profit']:.2f} USDT</b>\n"
        f"📊 Статус торговли: {status_str}\n"
        "────────────────────\n"
        f"📍 Персональный TRON кошелек:\n{wallet_str}\n"
        "────────────────────\n"
        f"📥 Пополнений: <b>{card['deposits_count']}</b> на сумму <b>{card['deposits_sum']:.2f} USDT</b>\n"
        f"📤 Выводов: <b>{card['withdrawals_count']}</b> на сумму <b>{card['withdrawals_sum']:.2f} USDT</b>\n"
        "────────────────────\n"
        "Выберите действие с балансом:"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Начислить USDT", callback_data=f"adm_add_bal:{u['user_id']}"),
            InlineKeyboardButton(text="➖ Списать USDT", callback_data=f"adm_sub_bal:{u['user_id']}")
        ],
        [
            InlineKeyboardButton(text="✉️ Написать клиенту", callback_data=f"adm_send_msg:{u['user_id']}"),
            InlineKeyboardButton(text="❌ Закрыть", callback_data="adm_cancel")
        ]
    ])

    await message.answer(text, reply_markup=kb, parse_mode="HTML")
    await state.clear()

@router.callback_query(F.data.startswith("adm_add_bal:") | F.data.startswith("adm_sub_bal:"))
async def on_balance_action_click(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split(":")
    action = parts[0]
    target_user_id = int(parts[1])

    is_add = action == "adm_add_bal"
    await state.update_data(target_user_id=target_user_id, is_add=is_add)
    await state.set_state(AdminStates.waiting_for_balance_delta)

    prompt = f"Введите сумму для {'НАЧИСЛЕНИЯ' if is_add else 'СПИСАНИЯ'} пользователю <code>{target_user_id}</code> (в USDT):"
    await call.message.answer(prompt, parse_mode="HTML")
    await call.answer()

@router.message(AdminStates.waiting_for_balance_delta)
async def process_balance_delta(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    target_user_id = data["target_user_id"]
    is_add = data["is_add"]
    await state.clear()

    try:
        val = float(message.text.replace(",", ".").strip())
        delta = val if is_add else -val
    except ValueError:
        await message.answer("⚠️ Введено не число. Действие отменено.")
        return

    ok, new_bal, reason = await admin_modify_balance(target_user_id, delta)
    if not ok:
        await message.answer(f"❌ Ошибка: {reason}")
        return

    action_name = "начислено" if is_add else "списано"
    sign = "+" if is_add else "-"
    await message.answer(
        f"✅ <b>Успешно {action_name} {sign}{val:.2f} USDT!</b>\n"
        f"👤 Пользователь ID: <code>{target_user_id}</code>\n"
        f"💰 Новый свободный баланс: <b>{new_bal:.2f} USDT</b>",
        parse_mode="HTML"
    )

    try:
        notify_text = (
            f"🔔 <b>Уведомление по счету</b>\n\n"
            f"Вам {'начислено' if is_add else 'списано'}: <b>{sign}{val:.2f} USDT</b>\n"
            f"💰 Ваш актуальный баланс: <b>{new_bal:.2f} USDT</b>"
        )
        await message.bot.send_message(chat_id=target_user_id, text=notify_text, parse_mode="HTML")
    except Exception:
        pass

@router.callback_query(F.data == "adm_pending_wdr")
async def on_view_pending_withdrawals(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    wdrs = await get_pending_withdrawals_list()
    if not wdrs:
        await call.message.answer("✅ <b>Нет ожидающих заявок на вывод!</b> Все заявки обработаны.", parse_mode="HTML")
        await call.answer()
        return

    await call.message.answer(f"📤 <b>ОЖИДАЮТ ВЫПЛАТЫ ({len(wdrs)} шт.):</b>", parse_mode="HTML")
    for w in wdrs:
        w_text = (
            f"🚨 <b>ЗАЯВКА НА ВЫВОД #{w['id']}</b>\n"
            f"👤 Юзер: @{w.get('username') or 'NoUser'} (ID: <code>{w['user_id']}</code>)\n"
            f"💵 Сумма: <b>{w['amount']:.2f} USDT</b>\n"
            f"📍 Кошелек TRC-20: <code>{w['wallet_address']}</code>\n"
            f"⏱ Создана: <code>{w['created_at']}</code>"
        )
        await call.message.answer(
            w_text,
            reply_markup=get_admin_withdraw_keyboard(w["id"]),
            parse_mode="HTML"
        )
    await call.answer()

@router.callback_query(F.data == "adm_recent_dep")
async def on_view_recent_deposits(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    deps = await get_recent_deposits(10)
    if not deps:
        await call.message.answer("ℹ️ История пополнений пока пуста.")
        await call.answer()
        return

    text = "📥 <b>ПОСЛЕДНИЕ ПОПОЛНЕНИЯ БАЛАНСОВ:</b>\n────────────────────\n"
    for d in deps:
        status_icon = "✅" if d["status"] == "approved" else "⏳"
        tx_short = d['tx_hash'][:12] + "..." if d['tx_hash'] else "N/A"
        text += (
            f"{status_icon} <b>+{d['amount']:.2f} USDT</b> | User ID: <code>{d['user_id']}</code> (@{d.get('username') or 'NoUser'})\n"
            f"🔗 Tx: <code>{tx_short}</code> | <i>{d['created_at']}</i>\n"
            "────────────────────\n"
        )
    await call.message.answer(text, parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "adm_broadcast")
async def on_broadcast_prompt(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_broadcast)
    text = (
        "📢 <b>МАССОВАЯ РАССЫЛКА ВСЕМ ПОЛЬЗОВАТЕЛЯМ</b>\n\n"
        "Отправьте текст сообщения для рассылки (поддерживается HTML-разметка):\n"
        "<i>(Или отправьте 'отмена')</i>"
    )
    await call.message.answer(text, parse_mode="HTML")
    await call.answer()

@router.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()

    text = message.text
    if text.lower() == "отмена":
        await message.answer("❌ Рассылка отменена.")
        return

    user_ids = await get_all_user_ids()
    sent_cnt = 0
    fail_cnt = 0

    progress_msg = await message.answer(f"⏳ Отправка сообщений {len(user_ids)} пользователям...")

    for uid in user_ids:
        try:
            await message.bot.send_message(chat_id=uid, text=text, parse_mode="HTML")
            sent_cnt += 1
        except Exception:
            fail_cnt += 1

    await progress_msg.edit_text(
        f"📢 <b>РАССЫЛКА ЗАВЕРШЕНА!</b>\n\n"
        f"✅ Успешно доставлено: <b>{sent_cnt}</b>\n"
        f"❌ Не доставлено: <b>{fail_cnt}</b>",
        parse_mode="HTML"
    )

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

        await db.execute("UPDATE withdrawals SET status = 'rejected' WHERE id = ?", (wdr_id,))
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (wdr["amount"], wdr["user_id"]))
        await db.commit()

    await call.message.edit_text(f"❌ Вывод #{wdr_id} отклонен. Средства возвращены на баланс пользователя.", parse_mode="HTML")
    await call.answer("Отклонено и возвращено")

@router.callback_query(F.data == "adm_cancel")
async def on_adm_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.answer("Закрыто")

# --- Direct Messaging from Bot to User ---
@router.message(Command("msg", "send"))
async def admin_msg_command(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) >= 3:
        target_query = parts[1].strip()
        text_content = parts[2].strip()
        card = await admin_get_user_card(target_query)
        if not card:
            await message.answer(f"❌ Пользователь '{target_query}' не найден в базе данных.")
            return
        u = card["user"]
        await _execute_send_user_message(message, u["user_id"], u["first_name"], u.get("language", "ru"), text_content)
        return
    elif len(parts) == 2:
        target_query = parts[1].strip()
        card = await admin_get_user_card(target_query)
        if not card:
            await message.answer(f"❌ Пользователь '{target_query}' не найден в базе данных.")
            return
        u = card["user"]
        await state.update_data(target_user_id=u["user_id"], target_name=u["first_name"], target_lang=u.get("language", "ru"))
        await state.set_state(AdminStates.waiting_for_direct_msg_text)
        await message.answer(
            f"👤 <b>Клиент:</b> {u['first_name']} (@{u.get('username') or 'N/A'}, ID: <code>{u['user_id']}</code>)\n"
            f"🌐 Язык: <b>{u.get('language', 'ru').upper()}</b>\n\n"
            "Введите текст сообщения, которое бот отправит клиенту:\n"
            "<i>(Или отправьте 'отмена')</i>",
            parse_mode="HTML"
        )
        return
    else:
        await state.set_state(AdminStates.waiting_for_direct_msg_recipient)
        await message.answer(
            "✉️ <b>ОТПРАВКА СООБЩЕНИЯ КЛИЕНТУ ОТ ИМЕНИ БОТА</b>\n"
            "────────────────────\n"
            "Введите <b>User ID</b> (число) или <b>@username</b> пользователя:\n"
            "<i>(Или отправьте 'отмена')</i>",
            parse_mode="HTML"
        )

@router.callback_query(F.data == "adm_direct_msg")
async def on_direct_msg_click(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_direct_msg_recipient)
    await call.message.answer(
        "✉️ <b>ОТПРАВКА СООБЩЕНИЯ КЛИЕНТУ ОТ ИМЕНИ БОТА</b>\n"
        "────────────────────\n"
        "Введите <b>User ID</b> (число) или <b>@username</b> пользователя, которому хотите написать:\n"
        "<i>(Или отправьте 'отмена')</i>",
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("adm_send_msg:"))
async def on_send_msg_to_user_click(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    target_id = call.data.split(":")[1].strip()
    card = await admin_get_user_card(target_id)
    if not card:
        await call.answer("Пользователь не найден.", show_alert=True)
        return
    u = card["user"]
    await state.update_data(target_user_id=u["user_id"], target_name=u["first_name"], target_lang=u.get("language", "ru"))
    await state.set_state(AdminStates.waiting_for_direct_msg_text)
    await call.message.answer(
        f"✉️ <b>Отправка сообщения клиенту:</b> {u['first_name']} (@{u.get('username') or 'N/A'}, ID: <code>{u['user_id']}</code>)\n"
        f"🌐 Язык: <b>{u.get('language', 'ru').upper()}</b>\n\n"
        "Введите текст сообщения (поддерживается HTML-разметка):\n"
        "<i>(Или отправьте 'отмена')</i>",
        parse_mode="HTML"
    )
    await call.answer()

@router.message(AdminStates.waiting_for_direct_msg_recipient)
async def process_direct_msg_recipient(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    query = message.text.strip()
    if query.lower() == "отмена":
        await state.clear()
        await message.answer("❌ Отправка сообщения отменена.")
        return
    card = await admin_get_user_card(query)
    if not card:
        await message.answer("❌ Пользователь с таким ID или логином не найден в базе.\nВведите другой ID / @username или напишите 'отмена':")
        return
    u = card["user"]
    await state.update_data(target_user_id=u["user_id"], target_name=u["first_name"], target_lang=u.get("language", "ru"))
    await state.set_state(AdminStates.waiting_for_direct_msg_text)
    await message.answer(
        f"👤 <b>Клиент найден:</b> {u['first_name']} (@{u.get('username') or 'N/A'}, ID: <code>{u['user_id']}</code>)\n"
        f"🌐 Язык клиента: <b>{u.get('language', 'ru').upper()}</b>\n\n"
        "Введите текст сообщения для отправки:\n"
        "<i>(Или отправьте 'отмена')</i>",
        parse_mode="HTML"
    )

@router.message(AdminStates.waiting_for_direct_msg_text)
async def process_direct_msg_text(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    text_content = message.text
    if text_content and text_content.lower() == "отмена":
        await state.clear()
        await message.answer("❌ Отправка сообщения отменена.")
        return
    data = await state.get_data()
    target_user_id = data["target_user_id"]
    target_name = data.get("target_name", "Клиент")
    target_lang = data.get("target_lang", "ru")
    await state.clear()

    await _execute_send_user_message(message, target_user_id, target_name, target_lang, text_content)

async def _execute_send_user_message(message: Message, target_user_id: int, target_name: str, target_lang: str, text_content: str):
    header = (
        "💬 <b>СООБЩЕНИЕ ОТ СЛУЖБЫ ПОДДЕРЖКИ | RAZGON ZONE</b>\n"
        "────────────────────\n"
        if target_lang == "ru" else
        "💬 <b>QO'LLAB-QUVVATLASh XIZMATIDAN XABAR | RAZGON ZONE</b>\n"
        "────────────────────\n"
    )
    user_msg = f"{header}{text_content}"

    try:
        await message.bot.send_message(
            chat_id=target_user_id,
            text=user_msg,
            parse_mode="HTML"
        )
        await message.answer(
            f"✅ <b>СООБЩЕНИЕ УСПЕШНО ДОСТАВЛЕНО!</b>\n\n"
            f"👤 Получатель: <b>{target_name}</b> (ID: <code>{target_user_id}</code>)\n"
            f"🌐 Язык клиента: <b>{target_lang.upper()}</b>\n\n"
            f"📝 <b>Текст сообщения:</b>\n{text_content}",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(
            f"⚠️ <b>Ошибка при отправке сообщения клиенту:</b>\n"
            f"<code>{str(e)}</code>\n\n"
            f"<i>Возможная причина: пользователь заблокировал бота или остановил диалог.</i>",
            parse_mode="HTML"
        )
