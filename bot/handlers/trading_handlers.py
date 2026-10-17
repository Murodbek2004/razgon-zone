from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from ..database import (
    get_user,
    get_active_trading_session,
    start_trading_session,
    stop_trading_session,
)
from ..trading_engine import engine
from ..config import TRADING_MODES, SERVICE_FEE_PERCENT
from ..keyboards import (
    get_main_reply_keyboard,
    get_modes_inline_keyboard,
    get_confirm_trade_keyboard,
    get_live_status_keyboard,
    get_confirm_stop_keyboard
)

router = Router()

class TradeSetupStates(StatesGroup):
    waiting_for_mode = State()
    waiting_for_amount = State()

@router.message(F.text == "🚀 Начать торговлю")
async def start_trade_flow(message: Message, state: FSMContext):
    user_id = message.from_user.id
    active_sess = await get_active_trading_session(user_id)
    if active_sess:
        await message.answer(
            "⚠️ <b>У вас уже запущена активная торговля!</b>\n\n"
            "Нажмите <b>«📊 Статус торговли»</b> для просмотра или <b>«🛑 Остановить торговлю»</b> для фиксации прибыли.",
            reply_markup=get_main_reply_keyboard(is_trading=True),
            parse_mode="HTML"
        )
        return

    user = await get_user(user_id)
    balance = user["balance"] if user else 0.0

    if balance < 10.0:
        await message.answer(
            f"⚠️ <b>Недостаточно средств для старта разгона.</b>\n\n"
            f"Текущий свободный баланс: <b>{balance:.2f} USDT</b>\n"
            "Минимальный депозит для торговли: <b>10.00 USDT</b>\n\n"
            "Нажмите <b>«📥 Пополнить (USDT)»</b> для внесения средств.",
            parse_mode="HTML"
        )
        return

    text = (
        "🚀 <b>ВЫБОР СТРАТЕГИИ РАЗГОНА | RAZGON ZONE</b>\n"
        "────────────────────\n"
        "Выберите желаемый режим торговли:\n\n"
        "🛡️ <b>Safe Run (+3.5% ~ +8%)</b>\n"
        "<i>Минимальный риск, мультибиржевой арбитраж. Защита капитала.</i>\n\n"
        "⚡ <b>Optimal Boost (+12% ~ +25%)</b>\n"
        "<i>Сбалансированный трендовый скальпинг BTC/ETH/SOL. Оптимальная скорость.</i>\n\n"
        "🔥 <b>Turbo Razgon (+30% ~ +75%)</b>\n"
        "<i>Максимальный импульсный разгон на высоковолатильных парах. Высокая скорость.</i>\n"
        "────────────────────\n"
        "Выберите стратегию кнопкой ниже:"
    )
    await message.answer(text, reply_markup=get_modes_inline_keyboard(), parse_mode="HTML")

@router.callback_query(F.data.startswith("select_mode:"))
async def on_mode_selected(call: CallbackQuery, state: FSMContext):
    mode = call.data.split(":")[1]
    mode_info = TRADING_MODES.get(mode, TRADING_MODES["optimal"])
    await state.update_data(selected_mode=mode)
    await state.set_state(TradeSetupStates.waiting_for_amount)

    user = await get_user(call.from_user.id)
    balance = user["balance"] if user else 0.0

    text = (
        f"🎯 <b>Выбран режим: {mode_info['title']}</b>\n"
        f"📝 <i>{mode_info['desc']}</i>\n\n"
        f"💵 Доступно на балансе: <b>{balance:.2f} USDT</b>\n\n"
        "Введите сумму в USDT, которую вы хотите направить в разгон:\n"
        f"<i>(Либо отправьте <code>{balance:.2f}</code> чтобы разогнать весь баланс)</i>"
    )
    await call.message.edit_text(text, parse_mode="HTML")
    await call.answer()

@router.message(TradeSetupStates.waiting_for_amount)
async def process_trade_amount(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    balance = user["balance"] if user else 0.0

    try:
        amount = float(message.text.replace(",", ".").strip())
        if amount < 10.0:
            await message.answer("⚠️ Минимальная сумма для входа в разгон — <b>10.00 USDT</b>:")
            return
        if amount > balance:
            await message.answer(f"⚠️ Сумма превышает свободный баланс (<b>{balance:.2f} USDT</b>). Введите доступную сумму:")
            return
    except ValueError:
        await message.answer("⚠️ Введите корректное число (например: 50):")
        return

    data = await state.get_data()
    mode = data.get("selected_mode", "optimal")
    mode_info = TRADING_MODES[mode]

    text = (
        "⚡ <b>ПОДТВЕРЖДЕНИЕ ЗАПУСКА ТОРГОВЛИ</b>\n"
        "────────────────────\n"
        f"🎯 <b>Стратегия:</b> {mode_info['title']}\n"
        f"💰 <b>Сумма депозита в работу:</b> <code>{amount:.2f} USDT</code>\n"
        f"📊 <b>Ожидаемая доходность:</b> +{mode_info['target_pnl_min']}% ~ +{mode_info['target_pnl_max']}%\n"
        f"🔒 <b>Комиссия платформы с чистой прибыли:</b> {SERVICE_FEE_PERCENT:.0f}%\n"
        "────────────────────\n"
        "Вы можете в любой момент остановить разгон и зафиксировать прибыль на баланс!"
    )

    await message.answer(text, reply_markup=get_confirm_trade_keyboard(mode, amount), parse_mode="HTML")
    await state.clear()

@router.callback_query(F.data.startswith("confirm_start:"))
async def on_confirm_start(call: CallbackQuery):
    parts = call.data.split(":")
    mode = parts[1]
    amount = float(parts[2])

    session = await start_trading_session(call.from_user.id, mode, amount)
    if not session:
        await call.message.edit_text("❌ Ошибка запуска. Проверьте баланс.", parse_mode="HTML")
        await call.answer()
        return

    # Notify success
    mode_info = TRADING_MODES[mode]
    text = (
        "🟢 <b>РАЗГОН УСПЕШНО ЗАПУЩЕН!</b> 🚀\n"
        "────────────────────\n"
        f"📈 <b>Режим:</b> {mode_info['title']}\n"
        f"💵 <b>Сумма в разгоне:</b> <code>{amount:.2f} USDT</code>\n"
        "⏱ <b>Статус:</b> В ТОРГОВЛЕ (Live)\n\n"
        "Торговые боты сканируют книгу ордеров и открывают позиции.\n"
        "Нажмите <b>«📊 Статус торговли»</b>, чтобы смотреть PnL и сделки!"
    )

    await call.message.delete()
    await call.message.answer(
        text,
        reply_markup=get_main_reply_keyboard(is_trading=True),
        parse_mode="HTML"
    )
    await call.answer("🚀 Торговля запущена!")

@router.message(F.text == "📊 Статус торговли")
async def show_live_status(message: Message):
    user_id = message.from_user.id
    session = await get_active_trading_session(user_id)
    if not session:
        await message.answer(
            "⚪️ <b>Торговля сейчас не активна.</b>\n\n"
            "Нажмите <b>«🚀 Начать торговлю»</b>, чтобы запустить разгон аккаунта!",
            reply_markup=get_main_reply_keyboard(is_trading=False),
            parse_mode="HTML"
        )
        return

    stats = await engine.get_live_stats(session)

    # Format deals
    deals_text = ""
    if stats["deals"]:
        deals_text = "\n<b>Последние сделки:</b>\n"
        for d in stats["deals"][:4]:
            side_icon = "🟢" if "LONG" in d["side"] else "🔴"
            deals_text += (
                f"• {side_icon} <b>{d['pair']}</b> ({d['side']}) | "
                f"Вход: <code>${d['entry_price']}</code> ➔ PnL: <b>+{d['pnl_amount']:.2f}$ (+{d['pnl_percent']}%)</b>\n"
            )

    # Speed bar
    bar_filled = int(stats["speed_val"] / 10)
    speed_bar = "🟩" * bar_filled + "⬜" * (10 - bar_filled)

    text = (
        "📊 <b>СТАТУС ТОРГОВЛИ | RAZGON ZONE LIVE</b>\n"
        "────────────────────\n"
        f"🎯 <b>Режим:</b> {stats['mode_title']}\n"
        f"⚡ <b>Скорость разгона:</b> {speed_bar} ({stats['speed_val']}%)\n\n"
        f"💵 <b>Вложенный депозит:</b> <code>{stats['deposit']:.2f} USDT</code>\n"
        f"📈 <b>Текущая прибыль (PnL):</b> <code>+{stats['profit']:.2f} USDT</code> (<b>+{stats['pnl_percent']:.2f}%</b>)\n"
        f"💰 <b>Текущий баланс в сделках:</b> <code>{stats['total_balance']:.2f} USDT</code>\n"
        f"⏱ <b>Время старта:</b> <code>{stats['started_at']}</code>\n"
        "────────────────────"
        f"{deals_text}\n"
        "💡 <i>Нажмите «Остановить», чтобы зафиксировать прибыль и вернуть депозит на баланс!</i>"
    )

    await message.answer(text, reply_markup=get_live_status_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "refresh_live_status")
async def on_refresh_live_status(call: CallbackQuery):
    user_id = call.from_user.id
    session = await get_active_trading_session(user_id)
    if not session:
        await call.message.edit_text("⚪️ Торговля была завершена.", parse_mode="HTML")
        await call.answer()
        return

    stats = await engine.get_live_stats(session)

    deals_text = ""
    if stats["deals"]:
        deals_text = "\n<b>Последние сделки:</b>\n"
        for d in stats["deals"][:4]:
            side_icon = "🟢" if "LONG" in d["side"] else "🔴"
            deals_text += (
                f"• {side_icon} <b>{d['pair']}</b> ({d['side']}) | "
                f"Вход: <code>${d['entry_price']}</code> ➔ PnL: <b>+{d['pnl_amount']:.2f}$ (+{d['pnl_percent']}%)</b>\n"
            )

    bar_filled = int(stats["speed_val"] / 10)
    speed_bar = "🟩" * bar_filled + "⬜" * (10 - bar_filled)

    text = (
        "📊 <b>СТАТУС ТОРГОВЛИ | RAZGON ZONE LIVE</b>\n"
        "────────────────────\n"
        f"🎯 <b>Режим:</b> {stats['mode_title']}\n"
        f"⚡ <b>Скорость разгона:</b> {speed_bar} ({stats['speed_val']}%)\n\n"
        f"💵 <b>Вложенный депозит:</b> <code>{stats['deposit']:.2f} USDT</code>\n"
        f"📈 <b>Текущая прибыль (PnL):</b> <code>+{stats['profit']:.2f} USDT</code> (<b>+{stats['pnl_percent']:.2f}%</b>)\n"
        f"💰 <b>Текущий баланс в сделках:</b> <code>{stats['total_balance']:.2f} USDT</code>\n"
        f"⏱ <b>Время старта:</b> <code>{stats['started_at']}</code>\n"
        "────────────────────"
        f"{deals_text}\n"
        "💡 <i>Нажмите «Остановить», чтобы зафиксировать прибыль и вернуть депозит на баланс!</i>"
    )

    try:
        await call.message.edit_text(text, reply_markup=get_live_status_keyboard(), parse_mode="HTML")
    except Exception:
        pass
    await call.answer("🔄 Данные обновлены!")

@router.message(F.text == "🛑 Остановить торговлю")
@router.callback_query(F.data == "ask_stop_trade")
async def ask_stop_trading(event: Message | CallbackQuery):
    user_id = event.from_user.id
    session = await get_active_trading_session(user_id)

    if not session:
        msg = "⚠️ У вас нет активной торговли для остановки."
        if isinstance(event, Message):
            await event.answer(msg)
        else:
            await event.answer(msg, show_alert=True)
        return

    text = (
        "⚠️ <b>ВЫ УВЕРЕНЫ, ЧТО ХОТИТЕ ОСТАНОВИТЬ РАЗГОН?</b>\n\n"
        f"💰 Депозит: <b>{session['deposit_amount']:.2f} USDT</b>\n"
        f"📈 Текущий PnL: <b>+{session['current_profit']:.2f} USDT</b>\n\n"
        "При остановке все позиции будут мгновенно закрыты по рынку, а депозит с прибылью поступит на ваш баланс!"
    )

    if isinstance(event, Message):
        await event.answer(text, reply_markup=get_confirm_stop_keyboard(), parse_mode="HTML")
    else:
        await event.message.edit_text(text, reply_markup=get_confirm_stop_keyboard(), parse_mode="HTML")
        await event.answer()

@router.callback_query(F.data == "continue_trade")
async def continue_trade_callback(call: CallbackQuery):
    await call.message.edit_text("✅ Торговля продолжается в штатном режиме!", parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "do_stop_trade")
async def do_stop_trade_callback(call: CallbackQuery):
    user_id = call.from_user.id
    res = await stop_trading_session(user_id, service_fee_percent=SERVICE_FEE_PERCENT)

    if not res:
        await call.message.edit_text("❌ Активная сессия не найдена.", parse_mode="HTML")
        await call.answer()
        return

    report_text = (
        "🛑 <b>ТОРГОВЛЯ ОСТАНОВЛЕНА | RAZGON REPORT</b> 🏁\n"
        "────────────────────\n"
        f"👤 <b>Трейдер:</b> {call.from_user.full_name}\n"
        f"💵 <b>Исходный депозит:</b> <code>{res['deposit_amount']:.2f} USDT</code>\n"
        f"📈 <b>Начисленный профит:</b> <code>+{res['current_profit']:.2f} USDT</code>\n"
        f"🏷 <b>Комиссия сервиса ({SERVICE_FEE_PERCENT:.0f}%):</b> <code>-{res['fee']:.2f} USDT</code>\n"
        f"💎 <b>Чистый доход:</b> <code>+{res['net_profit']:.2f} USDT</code>\n"
        "────────────────────\n"
        f"💰 <b>ИТОГО ЗАЧИСЛЕНО НА БАЛАНС:</b> <code>{res['total_returned']:.2f} USDT</code> ✅\n\n"
        "Средства уже доступны на балансе. Вы можете вывести их или запустить новый разгон!"
    )

    await call.message.delete()
    await call.message.answer(
        report_text,
        reply_markup=get_main_reply_keyboard(is_trading=False),
        parse_mode="HTML"
    )
    await call.answer("🛑 Торговля остановлена, профит зафиксирован!")

@router.callback_query(F.data == "cancel_action")
async def on_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Действие отменено.", parse_mode="HTML")
    await call.answer()
