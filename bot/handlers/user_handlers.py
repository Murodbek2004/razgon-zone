from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from ..database import (
    get_or_create_user,
    get_user,
    get_user_lang,
    set_user_lang,
    auto_credit_deposit,
    create_withdrawal,
    get_active_trading_session,
    get_or_create_user_wallet,
    start_simple_trading,
    user_cancel_trading_session
)
from ..localization import tr, LANGUAGES
from ..deposit_watcher import deposit_watcher
from ..keyboards import (
    get_main_reply_keyboard,
    get_language_inline_keyboard,
    get_deposit_keyboard,
    get_admin_withdraw_keyboard
)
from ..tron_service import (
    get_deposit_info,
    get_qr_code_stream,
    validate_tron_address,
    verify_tron_tx_onchain
)
from ..config import (
    ADMIN_IDS,
    MIN_DEPOSIT,
    MIN_WITHDRAW,
    TRON_USDT_WALLET
)

router = Router()

class DepositStates(StatesGroup):
    waiting_for_txid = State()

class WithdrawStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_address = State()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or "Трейдер"

    # Default to user's Telegram language if Uzbek
    initial_lang = "uz" if (message.from_user.language_code and message.from_user.language_code.startswith("uz")) else "ru"
    
    user = await get_or_create_user(user_id, username, first_name)
    user_lang = await get_user_lang(user_id) or initial_lang
    
    active_session = await get_active_trading_session(user_id)
    is_trading = active_session is not None

    trading_info = ""
    if is_trading:
        if user_lang == "uz":
            trading_info = f"🔥 <b>Razgondagi mablag':</b> <code>{user['in_trading_balance']:.2f} USDT</code>\n"
        else:
            trading_info = f"🔥 <b>В активном разгоне:</b> <code>{user['in_trading_balance']:.2f} USDT</code>\n"

    welcome_text = tr(
        "welcome",
        user_lang,
        name=first_name,
        balance=user["balance"],
        trading_info=trading_info
    )

    await message.answer(
        welcome_text,
        reply_markup=get_main_reply_keyboard(lang=user_lang, is_trading=is_trading),
        parse_mode="HTML"
    )

# --- Language Switching ---
@router.message(Command("language"))
@router.message(Command("lang"))
@router.message(F.text.in_(["🌐 Сменить язык", "🌐 Tilni o'zgartirish"]))
async def choose_language(message: Message):
    user_lang = await get_user_lang(message.from_user.id)
    text = tr("choose_language", user_lang)
    await message.answer(text, reply_markup=get_language_inline_keyboard(), parse_mode="HTML")

@router.callback_query(F.data.startswith("set_lang:"))
async def on_language_selected(call: CallbackQuery):
    lang_code = call.data.split(":")[1]
    if lang_code not in LANGUAGES:
        lang_code = "ru"

    await set_user_lang(call.from_user.id, lang_code)
    active_session = await get_active_trading_session(call.from_user.id)
    is_trading = active_session is not None

    ack_text = tr("language_set", lang_code)
    await call.answer(ack_text)
    await call.message.answer(
        ack_text,
        reply_markup=get_main_reply_keyboard(lang=lang_code, is_trading=is_trading),
        parse_mode="HTML"
    )

# --- 1-Click Trade Launch ---
@router.message(F.text.in_(["🚀 Запустить разгон", "🚀 Razgonni boshlash", "🚀 Начать разгон", "🚀 Начать торговлю"]))
async def handle_start_trade(message: Message):
    user_id = message.from_user.id
    user_lang = await get_user_lang(user_id)

    # 1. Check if already active
    active_session = await get_active_trading_session(user_id)
    if active_session:
        await message.answer(
            tr("trade_already_running", user_lang, amount=active_session["deposit_amount"]),
            reply_markup=get_main_reply_keyboard(lang=user_lang, is_trading=True),
            parse_mode="HTML"
        )
        return

    # 2. Check balance
    user = await get_user(user_id)
    balance = user["balance"] if user else 0.0

    if balance < MIN_DEPOSIT:
        await message.answer(
            tr("trade_no_money", user_lang, balance=balance),
            reply_markup=get_main_reply_keyboard(lang=user_lang, is_trading=False),
            parse_mode="HTML"
        )
        return

    # 3. Launch single-click trading
    sess = await start_simple_trading(user_id)
    if not sess:
        err_msg = "⚠️ Ошибка запуска разгона. Пожалуйста, проверьте баланс." if user_lang == "ru" else "⚠️ Razgonni boshlashda xatolik yuz berdi. Balansni tekshiring."
        await message.answer(err_msg)
        return

    session_id = sess["id"]
    deposit_amount = sess["deposit_amount"]

    # Send instant confirmation
    await message.answer(
        tr("trade_started", user_lang, amount=deposit_amount),
        reply_markup=get_main_reply_keyboard(lang=user_lang, is_trading=True),
        parse_mode="HTML"
    )

    # Notify admins about active session
    for admin_id in ADMIN_IDS:
        try:
            admin_notify = (
                f"🔔 <b>[ОПОВЕЩЕНИЕ АДМИНИСТРАТОРА]</b>\n"
                f"🚀 <b>Новый разгон запущен в работу</b>\n\n"
                f"👤 Трейдер: @{message.from_user.username or 'NoUser'} ({message.from_user.first_name})\n"
                f"🆔 Telegram ID: <code>{user_id}</code>\n"
                f"💵 Депозит в разгоне: <b>{deposit_amount:.2f} USDT</b>\n"
                f"🆔 Сессия: <code>#{session_id}</code>\n"
                f"🌐 Язык: <b>{user_lang.upper()}</b>"
            )
            await message.bot.send_message(chat_id=admin_id, text=admin_notify, parse_mode="HTML")
        except Exception:
            pass

# --- Live Status Button ---
@router.message(F.text.in_(["📊 Статус разгона", "📊 Razgon holati", "📊 Статус торговли (Live)"]))
async def handle_trade_status(message: Message):
    user_id = message.from_user.id
    user_lang = await get_user_lang(user_id)

    active_session = await get_active_trading_session(user_id)
    if active_session:
        text = tr(
            "status_running",
            user_lang,
            amount=active_session["deposit_amount"],
            started_at=active_session["started_at"]
        )
        await message.answer(
            text,
            reply_markup=get_main_reply_keyboard(lang=user_lang, is_trading=True),
            parse_mode="HTML"
        )
    else:
        text = tr("status_not_running", user_lang)
        await message.answer(
            text,
            reply_markup=get_main_reply_keyboard(lang=user_lang, is_trading=False),
            parse_mode="HTML"
        )

# --- Stop Trade by User ---
@router.message(F.text.in_(["🛑 Остановить разгон", "🛑 Razgonni to'xtatish", "🛑 Зафиксировать и выйти"]))
async def handle_stop_trade(message: Message):
    user_id = message.from_user.id
    user_lang = await get_user_lang(user_id)

    deposit = await user_cancel_trading_session(user_id)
    if not deposit:
        err = "⚪️ У вас нет активной торговли для остановки." if user_lang == "ru" else "⚪️ Sizda to'xtatish uchun faol razgon yo'q."
        await message.answer(
            err,
            reply_markup=get_main_reply_keyboard(lang=user_lang, is_trading=False)
        )
        return

    # Send confirmation
    await message.answer(
        tr("trade_stopped", user_lang, amount=deposit),
        reply_markup=get_main_reply_keyboard(lang=user_lang, is_trading=False),
        parse_mode="HTML"
    )

    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"🔔 <b>[ОПОВЕЩЕНИЕ АДМИНИСТРАТОРА]</b>\n"
                    f"🛑 <b>Разгон остановлен клиентом</b>\n\n"
                    f"👤 Трейдер: @{message.from_user.username or 'NoUser'} (ID: <code>{user_id}</code>)\n"
                    f"💵 Депозит возвращен на баланс: <b>{deposit:.2f} USDT</b>\n"
                    f"🌐 Язык: <b>{user_lang.upper()}</b>"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass

# --- Cabinet / Balance ---
@router.message(F.text.in_(["💼 Мой баланс", "💼 Mening hisobim", "💼 Кабинет & Статистика", "💼 Личный кабинет"]))
async def show_cabinet(message: Message):
    user_id = message.from_user.id
    user_lang = await get_user_lang(user_id)
    user = await get_user(user_id)
    if not user:
        user = await get_or_create_user(user_id, message.from_user.username or "", message.from_user.first_name or "")

    active_session = await get_active_trading_session(user_id)
    is_trading = active_session is not None

    if user_lang == "uz":
        status_str = "🟢 <b>RAZGONDA (Savdo faol)</b>" if is_trading else "⚪️ <i>Savdo to'xtatilgan</i>"
    else:
        status_str = "🟢 <b>В РАЗГОНЕ (Торговля активна)</b>" if is_trading else "⚪️ <i>Торговля остановлена</i>"

    text = tr(
        "cabinet_info",
        user_lang,
        name=message.from_user.full_name,
        user_id=user_id,
        status_str=status_str,
        balance=user["balance"],
        in_trading=user["in_trading_balance"],
        total_profit=user["total_profit"]
    )
    await message.answer(
        text,
        reply_markup=get_main_reply_keyboard(lang=user_lang, is_trading=is_trading),
        parse_mode="HTML"
    )

# --- Deposit USDT ---
@router.message(F.text.in_(["📥 Пополнить USDT", "📥 USDT to'ldirish", "📥 Пополнить (USDT)"]))
async def deposit_menu(message: Message):
    user_id = message.from_user.id
    user_lang = await get_user_lang(user_id)
    addr = TRON_USDT_WALLET

    info_text = tr("deposit_info", user_lang, address=addr)
    qr_stream = await get_qr_code_stream(addr)
    if qr_stream:
        qr_file = BufferedInputFile(qr_stream.getvalue(), filename="usdt_trc20_qr.png")
        await message.answer_photo(
            photo=qr_file,
            caption=info_text,
            reply_markup=get_deposit_keyboard(lang=user_lang),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            text=info_text,
            reply_markup=get_deposit_keyboard(lang=user_lang),
            parse_mode="HTML"
        )

@router.callback_query(F.data == "check_my_deposit_now")
async def on_check_my_deposit_now(call: CallbackQuery, state: FSMContext):
    await ask_txid(call, state)

@router.callback_query(F.data == "enter_deposit_txid")
async def ask_txid(call: CallbackQuery, state: FSMContext):
    user_lang = await get_user_lang(call.from_user.id)
    await state.set_state(DepositStates.waiting_for_txid)
    if user_lang == "uz":
        text = (
            "⚡ <b>BLOKCHEYN ORQALI AVTOMATIK TEKSHIRISH</b>\n"
            "────────────────────\n"
            "USDT (TRC-20) o'tkazmangizning <b>TxID (tranzaksiya heshi)</b> ni bu yerga yuboring:\n\n"
            "<i>(Bot zudlik bilan TRON nodlariga ulanib, tekshiradi va mablag'ni balansingizga o'tkazadi!)</i>"
        )
    else:
        text = (
            "⚡ <b>АВТОМАТИЧЕСКАЯ БЛОКЧЕЙН-ПРОВЕРКА</b>\n"
            "────────────────────\n"
            "Отправьте сюда <b>TxID (хеш транзакции)</b> вашего перевода USDT (TRC-20):\n\n"
            "<i>(Бот мгновенно обратится к нодам TRON, проверит подлинность смарт-контракта и зачислит баланс автоматически!)</i>"
        )
    await call.message.answer(text, parse_mode="HTML")
    await call.answer()

@router.message(DepositStates.waiting_for_txid)
async def process_deposit_txid(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_lang = await get_user_lang(user_id)
    txid = message.text.strip()
    await state.clear()

    wait_msg = "⏳ <b>Связываюсь с блокчейном TRON...</b>\nПроверяю статус транзакции USDT..." if user_lang == "ru" else "⏳ <b>TRON blokcheyni bilan bog'lanilmoqda...</b>\nUSDT tranzaksiya holati tekshirilmoqda..."
    status_msg = await message.answer(wait_msg, parse_mode="HTML")

    addr = TRON_USDT_WALLET
    is_valid, amount, info = await verify_tron_tx_onchain(txid, addr, MIN_DEPOSIT)

    if not is_valid:
        if user_lang == "uz":
            err_text = (
                "❌ <b>TRON blokcheyni tranzaksiyani tasdiqlamadi:</b>\n\n"
                f"⚠️ <i>{info}</i>\n\n"
                "💡 <b>Nima qilish kerak?</b>\n"
                "• Agar siz hozirgina o'tkazgan bo'lsangiz, TRON tarmog'ida tasdiqlanishi uchun 1-2 daqiqa kuting va TxID ni qaytadan yuboring.\n"
                "• O'tkazma <b>TRC-20</b> tarmog'ida shaxsiy hamyoningizga yuborilganiga ishonch hosil qiling."
            )
        else:
            err_text = (
                "❌ <b>Блокчейн TRON не подтвердил транзакцию:</b>\n\n"
                f"⚠️ <i>{info}</i>\n\n"
                "💡 <b>Что делать?</b>\n"
                "• Если вы только что отправили перевод, подождите 1–2 минуты для записи блока в TRON и отправьте TxID снова.\n"
                "• Убедитесь, что переводили в сети <b>TRC-20</b> на ваш персональный кошелек."
            )
        await status_msg.edit_text(err_text, parse_mode="HTML")
        return

    # Auto credit balance (0% fee, 0% referral bonus)
    ok, dep_dict, reason = await auto_credit_deposit(user_id, amount, txid)
    if not ok:
        await status_msg.edit_text(f"⚠️ {reason}", parse_mode="HTML")
        return

    user = await get_user(user_id)
    if user_lang == "uz":
        success_text = (
            "🎉 <b>DEPOZIT AVTOMATIK MUVAFFAQIYATLI QABUL QILINDI!</b> ⚡\n"
            "────────────────────\n"
            f"💵 To'ldirish summasi: <b>+{amount:.2f} USDT</b>\n"
            f"💰 Hozirgi balansingiz: <b>{user['balance']:.2f} USDT</b>\n"
            f"🔗 Hesh (TxID): <code>{txid[:16]}...{txid[-8:]}</code>\n"
            "────────────────────\n"
            "🚀 Mablag'ingiz tayyor! Razgonni boshlash uchun <b>«🚀 Razgonni boshlash»</b> tugmasini bosing."
        )
    else:
        success_text = (
            "🎉 <b>ДЕПОЗИТ УСПЕШНО ЗАЧИСЛЕН АВТОМАТИЧЕСКИ!</b> ⚡\n"
            "────────────────────\n"
            f"💵 Сумма пополнения: <b>+{amount:.2f} USDT</b>\n"
            f"💰 Ваш актуальный баланс: <b>{user['balance']:.2f} USDT</b>\n"
            f"🔗 Хеш (TxID): <code>{txid[:16]}...{txid[-8:]}</code>\n"
            "────────────────────\n"
            "🚀 Средства готовы к работе! Нажмите <b>«🚀 Запустить разгон»</b>, чтобы начать торговлю."
        )
    await status_msg.edit_text(success_text, parse_mode="HTML")

    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            admin_msg = (
                f"🔔 <b>[ОПОВЕЩЕНИЕ АДМИНИСТРАТОРА]</b>\n"
                f"⚡ <b>Авто-пополнение USDT</b>\n\n"
                f"👤 Пользователь: @{message.from_user.username or 'NoUser'} (ID: <code>{user_id}</code>)\n"
                f"💰 Сумма: <b>+{amount:.2f} USDT</b>\n"
                f"🔗 Хеш: <code>{txid}</code>\n"
                f"<a href='https://tronscan.org/#/transaction/{txid}'>Посмотреть в TronScan</a>"
            )
            await message.bot.send_message(chat_id=admin_id, text=admin_msg, parse_mode="HTML")
        except Exception:
            pass

# --- Withdraw Funds ---
@router.message(F.text.in_(["📤 Вывод средств", "📤 Pulni yechish", "📤 Pul yechish"]))
async def withdraw_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_lang = await get_user_lang(user_id)
    user = await get_user(user_id)
    balance = user["balance"] if user else 0.0

    if balance < MIN_WITHDRAW:
        if user_lang == "uz":
            err_msg = (
                f"⚠️ <b>Mablag' yetarli emas.</b>\n\n"
                f"Mavjud erkin balans: <b>{balance:.2f} USDT</b>\n"
                f"Chiqarish uchun minimal summa: <b>{MIN_WITHDRAW} USDT</b>\n\n"
                "<i>(Agar mablag' razgonda bo'lsa, savdo sessiyasi yakunlanishini kuting)</i>"
            )
        else:
            err_msg = (
                f"⚠️ <b>Недостаточно средств для вывода.</b>\n\n"
                f"Ваш доступный баланс: <b>{balance:.2f} USDT</b>\n"
                f"Минимальная сумма для вывода: <b>{MIN_WITHDRAW} USDT</b>\n\n"
                "<i>(Если средства находятся в разгоне, дождитесь завершения торговой сессии)</i>"
            )
        await message.answer(err_msg, parse_mode="HTML")
        return

    await state.set_state(WithdrawStates.waiting_for_amount)
    prompt_text = tr("withdraw_prompt_amount", user_lang, balance=balance)
    await message.answer(prompt_text, parse_mode="HTML")

@router.message(WithdrawStates.waiting_for_amount)
async def process_withdraw_amount(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_lang = await get_user_lang(user_id)
    user = await get_user(user_id)
    balance = user["balance"] if user else 0.0

    try:
        amount = float(message.text.replace(",", ".").strip())
        if amount < MIN_WITHDRAW:
            err = f"⚠️ Минимальная сумма вывода — <b>{MIN_WITHDRAW} USDT</b>." if user_lang == "ru" else f"⚠️ Minimal yechib olish summasi — <b>{MIN_WITHDRAW} USDT</b>."
            await message.answer(err, parse_mode="HTML")
            return
        if amount > balance:
            err = f"⚠️ Сумма превышает ваш баланс (<b>{balance:.2f} USDT</b>). Введите меньшую сумму:" if user_lang == "ru" else f"⚠️ Summa balansingizdan katta (<b>{balance:.2f} USDT</b>). Kichikroq summa kiriting:"
            await message.answer(err, parse_mode="HTML")
            return
    except ValueError:
        err = "⚠️ Введите корректное число (например: 25):" if user_lang == "ru" else "⚠️ To'g'ri son kiriting (masalan: 25):"
        await message.answer(err, parse_mode="HTML")
        return

    await state.update_data(withdraw_amount=amount)
    await state.set_state(WithdrawStates.waiting_for_address)
    prompt_addr = tr("withdraw_prompt_address", user_lang, amount=amount)
    await message.answer(prompt_addr, parse_mode="HTML")

@router.message(WithdrawStates.waiting_for_address)
async def process_withdraw_address(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_lang = await get_user_lang(user_id)
    address = message.text.strip()

    if not validate_tron_address(address):
        err = "⚠️ Неверный формат TRC-20 адреса. Адрес должен начинаться с 'T' и состоять из 34 символов:" if user_lang == "ru" else "⚠️ TRC-20 manzili noto'g'ri. Manzil 'T' harfi bilan boshlanishi va 34 ta belgidan iborat bo'lishi kerak:"
        await message.answer(err, parse_mode="HTML")
        return

    data = await state.get_data()
    amount = data["withdraw_amount"]
    wdr_id = await create_withdrawal(user_id, amount, address)
    await state.clear()

    if not wdr_id:
        err = "⚠️ Ошибка списания баланса. Пожалуйста, проверьте баланс." if user_lang == "ru" else "⚠️ Balansdan yechishda xatolik. Iltimos balansingizni tekshiring."
        await message.answer(err, parse_mode="HTML")
        return

    success_msg = tr("withdraw_success", user_lang, wdr_id=wdr_id, amount=amount, address=address)
    await message.answer(success_msg, parse_mode="HTML")

    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            admin_msg = (
                f"🔔 <b>[ОПОВЕЩЕНИЕ АДМИНИСТРАТОРА]</b>\n"
                f"🚨 <b>Заявка на вывод #{wdr_id}</b>\n\n"
                f"👤 Юзер: @{message.from_user.username or 'NoUser'} (ID: <code>{user_id}</code>)\n"
                f"💰 Сумма: <b>{amount:.2f} USDT</b>\n"
                f"📍 Кошелек TRC-20: <code>{address}</code>"
            )
            await message.bot.send_message(
                chat_id=admin_id,
                text=admin_msg,
                reply_markup=get_admin_withdraw_keyboard(wdr_id),
                parse_mode="HTML"
            )
        except Exception:
            pass

# --- About Service ---
@router.message(F.text.in_(["ℹ️ О сервисе", "ℹ️ Xizmat haqida", "ℹ️ О платформе"]))
async def show_about(message: Message):
    user_lang = await get_user_lang(message.from_user.id)
    text = tr("about", user_lang)
    await message.answer(text, parse_mode="HTML")
