from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from ..database import (
    get_or_create_user,
    get_user,
    create_deposit,
    create_withdrawal,
    get_active_trading_session
)
from ..keyboards import (
    get_main_reply_keyboard,
    get_deposit_keyboard,
    get_admin_deposit_keyboard,
    get_admin_withdraw_keyboard
)
from ..tron_service import (
    get_deposit_info,
    generate_qr_code,
    validate_tron_address,
    validate_tron_tx_hash
)
from ..config import (
    ADMIN_IDS,
    MIN_DEPOSIT,
    MIN_WITHDRAW,
    REFERRAL_BONUS_PERCENT,
    WEBAPP_URL
)

router = Router()

class DepositStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_txid = State()

class WithdrawStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_address = State()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or "Трейдер"

    # Extract ref id
    referrer_id = None
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref") and args[1][3:].isdigit():
        referrer_id = int(args[1][3:])

    user = await get_or_create_user(user_id, username, first_name, referrer_id)
    active_session = await get_active_trading_session(user_id)
    is_trading = active_session is not None

    welcome_text = (
        f"⚡ <b>Добро пожаловать в RAZGON ZONE!</b> 🚀\n\n"
        f"Привет, <b>{first_name}</b>! Это алгоритмическая платформа автоматического разгона крипто-активов.\n\n"
        f"💵 <b>Ваш доступный баланс:</b> <code>{user['balance']:.2f} USDT</code>\n"
        + (f"🔥 <b>В разгоне / торговле:</b> <code>{user['in_trading_balance']:.2f} USDT</code>\n" if is_trading else "")
        + f"🏆 <b>Зафиксировано прибыли:</b> <code>{user['total_profit']:.2f} USDT</code>\n\n"
        "💡 <b>Как это работает?</b>\n"
        "1. Пополните баланс в <b>USDT TRC-20</b>.\n"
        "2. Нажмите <b>«Начать торговлю»</b> и выберите стратегию разгона.\n"
        "3. Следите за статусом и PnL сделок в реальном времени.\n"
        "4. Нажмите <b>«Остановить торговлю»</b> в любой момент — профит мгновенно поступит на ваш баланс!\n\n"
        "👇 <i>Используйте кнопки меню ниже для управления:</i>"
    )

    await message.answer(
        welcome_text,
        reply_markup=get_main_reply_keyboard(is_trading=is_trading),
        parse_mode="HTML"
    )

@router.message(F.text == "💼 Личный кабинет")
async def show_cabinet(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    if not user:
        user = await get_or_create_user(user_id)

    active_session = await get_active_trading_session(user_id)
    status_str = "🟢 <b>В РАЗГОНЕ (Торговля активна)</b>" if active_session else "⚪️ <i>Торговля остановлена</i>"

    text = (
        "💼 <b>ЛИЧНЫЙ КАБИНЕТ | RAZGON ZONE</b>\n"
        "────────────────────\n"
        f"👤 <b>Пользователь:</b> {message.from_user.full_name} (ID: <code>{user_id}</code>)\n"
        f"📊 <b>Статус:</b> {status_str}\n\n"
        f"💰 <b>Свободный баланс:</b> <code>{user['balance']:.2f} USDT</code>\n"
        f"📈 <b>В активной торговле:</b> <code>{user['in_trading_balance']:.2f} USDT</code>\n"
        f"🎯 <b>Суммарный заработок:</b> <code>{user['total_profit']:.2f} USDT</code>\n"
        "────────────────────\n"
        "🔒 <i>Депозиты защищены мультиподписным пулом ликвидности.</i>"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📥 Пополнить (USDT)")
async def deposit_menu(message: Message, state: FSMContext):
    user_id = message.from_user.id
    addr, info_text = get_deposit_info(user_id)

    # Generate QR Code
    qr_stream = generate_qr_code(addr)
    qr_file = BufferedInputFile(qr_stream.getvalue(), filename="usdt_trc20_qr.png")

    await message.answer_photo(
        photo=qr_file,
        caption=info_text,
        reply_markup=get_deposit_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "enter_deposit_txid")
async def ask_txid(call: CallbackQuery, state: FSMContext):
    await state.set_state(DepositStates.waiting_for_amount)
    await call.message.answer(
        "✏️ <b>Шаг 1 из 2:</b>\nВведите сумму отправленного пополнения в USDT (например: <code>50</code>):",
        parse_mode="HTML"
    )
    await call.answer()

@router.message(DepositStates.waiting_for_amount)
async def process_deposit_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", ".").strip())
        if amount < MIN_DEPOSIT:
            await message.answer(f"⚠️ Минимальная сумма депозита — <b>{MIN_DEPOSIT} USDT</b>. Попробуйте снова:")
            return
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите корректное число (например: 50):")
        return

    await state.update_data(deposit_amount=amount)
    await state.set_state(DepositStates.waiting_for_txid)
    await message.answer(
        f"✅ Сумма: <b>{amount} USDT</b>\n\n"
        "✏️ <b>Шаг 2 из 2:</b>\nОтправьте <b>TxID (хеш транзакции)</b> из вашего кошелька/биржи:",
        parse_mode="HTML"
    )

@router.message(DepositStates.waiting_for_txid)
async def process_deposit_txid(message: Message, state: FSMContext):
    txid = message.text.strip()
    data = await state.get_data()
    amount = data.get("deposit_amount", 10.0)

    # Create deposit record
    dep_id = await create_deposit(message.from_user.id, amount, txid)
    await state.clear()

    await message.answer(
        f"🎉 <b>Заявка на пополнение #{dep_id} принята!</b>\n\n"
        f"💵 Сумма: <b>{amount:.2f} USDT</b>\n"
        f"🔗 TxID: <code>{txid}</code>\n\n"
        "⏳ Транзакция верифицируется в блокчейне TRON. Средства поступят на баланс в течение нескольких минут.",
        parse_mode="HTML"
    )

    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            admin_msg = (
                f"🔔 <b>НОВЫЙ ДЕПОЗИТ #{dep_id}</b>\n\n"
                f"👤 Юзер: @{message.from_user.username or 'NoUser'} (ID: <code>{message.from_user.id}</code>)\n"
                f"💰 Сумма: <b>{amount:.2f} USDT</b>\n"
                f"🔗 Хеш: <code>{txid}</code>\n"
                f"<a href='https://tronscan.org/#/transaction/{txid}'>Посмотреть в TronScan</a>"
            )
            await message.bot.send_message(
                chat_id=admin_id,
                text=admin_msg,
                reply_markup=get_admin_deposit_keyboard(dep_id),
                parse_mode="HTML"
            )
        except Exception:
            pass

@router.message(F.text == "📤 Вывод средств")
async def withdraw_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await get_user(user_id)
    balance = user["balance"] if user else 0.0

    if balance < MIN_WITHDRAW:
        await message.answer(
            f"⚠️ <b>Недостаточно средств для вывода.</b>\n\n"
            f"Ваш доступный баланс: <b>{balance:.2f} USDT</b>\n"
            f"Минимальная сумма для вывода: <b>{MIN_WITHDRAW} USDT</b>\n\n"
            "<i>(Если средства находятся в торговле, сначала нажмите «Остановить торговлю»)</i>",
            parse_mode="HTML"
        )
        return

    await state.set_state(WithdrawStates.waiting_for_amount)
    await message.answer(
        f"📤 <b>Вывод средств в USDT (TRC-20)</b>\n\n"
        f"Доступно к выводу: <b>{balance:.2f} USDT</b>\n"
        f"Минимум: <b>{MIN_WITHDRAW} USDT</b>\n\n"
        "Введите сумму, которую хотите вывести:",
        parse_mode="HTML"
    )

@router.message(WithdrawStates.waiting_for_amount)
async def process_withdraw_amount(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    balance = user["balance"] if user else 0.0

    try:
        amount = float(message.text.replace(",", ".").strip())
        if amount < MIN_WITHDRAW:
            await message.answer(f"⚠️ Минимальная сумма вывода — <b>{MIN_WITHDRAW} USDT</b>.")
            return
        if amount > balance:
            await message.answer(f"⚠️ Сумма превышает ваш баланс (<b>{balance:.2f} USDT</b>). Введите меньшую сумму:")
            return
    except ValueError:
        await message.answer("⚠️ Введите корректное число (например: 25):")
        return

    await state.update_data(withdraw_amount=amount)
    await state.set_state(WithdrawStates.waiting_for_address)
    await message.answer(
        f"Сумма к выводу: <b>{amount:.2f} USDT</b>\n\n"
        "Отправьте ваш адрес кошелька <b>TRON (TRC-20)</b> для получения средств:\n"
        "<i>(Пример: T...)</i>",
        parse_mode="HTML"
    )

@router.message(WithdrawStates.waiting_for_address)
async def process_withdraw_address(message: Message, state: FSMContext):
    address = message.text.strip()
    if not validate_tron_address(address):
        await message.answer("⚠️ Неверный формат TRC-20 адреса. Адрес должен начинаться с 'T' и состоять из 34 символов:")
        return

    data = await state.get_data()
    amount = data["withdraw_amount"]
    wdr_id = await create_withdrawal(message.from_user.id, amount, address)
    await state.clear()

    if not wdr_id:
        await message.answer("⚠️ Ошибка списания баланса. Пожалуйста, проверьте баланс.")
        return

    await message.answer(
        f"✅ <b>Заявка на вывод #{wdr_id} успешно создана!</b>\n\n"
        f"💵 Сумма: <b>{amount:.2f} USDT</b>\n"
        f"📍 Адрес выплаты: <code>{address}</code>\n\n"
        "Выплата отправляется в течение 10–60 минут после подтверждения безопасности.",
        parse_mode="HTML"
    )

    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            admin_msg = (
                f"🚨 <b>ЗАЯВКА НА ВЫВОД #{wdr_id}</b>\n\n"
                f"👤 Юзер: @{message.from_user.username or 'NoUser'} (ID: <code>{message.from_user.id}</code>)\n"
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

@router.message(F.text == "👥 Партнеры")
async def show_referral(message: Message):
    user_id = message.from_user.id
    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref{user_id}"

    text = (
        "🤝 <b>ПАРТНЕРСКАЯ ПРОГРАММА RAZGON ZONE</b>\n"
        "────────────────────\n"
        f"Приглашайте друзей и получайте <b>{REFERRAL_BONUS_PERCENT:.0f}%</b> от каждого пополнения депозита их разгонов прямо на баланс!\n\n"
        f"🔗 <b>Ваша реферальная ссылка:</b>\n<code>{ref_link}</code>\n\n"
        "💸 <i>Бонусы начисляются мгновенно и доступны для разгона или вывода!</i>"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "ℹ️ О платформе")
async def show_about(message: Message):
    text = (
        "🔥 <b>RAZGON ZONE — HFT & ALGO TRADING ECOSYSTEM</b>\n"
        "────────────────────\n"
        "<b>Razgon Zone</b> — передовая платформа алгоритмического трейдинга и разгона депозитов.\n\n"
        "🚀 <b>Преимущества:</b>\n"
        "• <b>Высокочастотный арбитраж:</b> Торговля кросс-биржами (Bybit, Binance, OKX).\n"
        "• <b>Контроль в 1 клик:</b> Вы можете запустить торговлю и остановить её в любой момент!\n"
        "• <b>Мгновенная фиксация:</b> Накопленная прибыль немедленно зачисляется на ваш баланс при остановке.\n"
        "• <b>Прозрачность:</b> Полная статистика по каждой сделке и WebApp-терминал.\n\n"
        "💬 <b>Техническая поддержка:</b> @RazgonZoneSupport"
    )
    await message.answer(text, parse_mode="HTML")
