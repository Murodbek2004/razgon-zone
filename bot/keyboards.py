from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo
)
from .config import WEBAPP_URL, TRADING_MODES

def get_main_reply_keyboard(is_trading: bool = False) -> ReplyKeyboardMarkup:
    """Bottom persistent menu keyboard"""
    kb = []
    
    # WebApp button on top
    if WEBAPP_URL:
        kb.append([KeyboardButton(text="⚡ Razgon Terminal (Web App)", web_app=WebAppInfo(url=WEBAPP_URL))])
    
    if is_trading:
        kb.append([
            KeyboardButton(text="📊 Статус торговли"),
            KeyboardButton(text="🛑 Остановить торговлю")
        ])
    else:
        kb.append([
            KeyboardButton(text="🚀 Начать торговлю"),
            KeyboardButton(text="💼 Личный кабинет")
        ])

    kb.append([
        KeyboardButton(text="📥 Пополнить (USDT)"),
        KeyboardButton(text="📤 Вывод средств")
    ])
    kb.append([
        KeyboardButton(text="👥 Партнеры"),
        KeyboardButton(text="ℹ️ О платформе")
    ])

    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_modes_inline_keyboard() -> InlineKeyboardMarkup:
    """Trading mode selector"""
    buttons = [
        [InlineKeyboardButton(
            text="🛡️ Safe Run (+3.5% ~ +8%)",
            callback_data="select_mode:safe"
        )],
        [InlineKeyboardButton(
            text="⚡ Optimal Boost (+12% ~ +25%)",
            callback_data="select_mode:optimal"
        )],
        [InlineKeyboardButton(
            text="🔥 Turbo Razgon (+30% ~ +75%)",
            callback_data="select_mode:turbo"
        )],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_trade_keyboard(mode: str, amount: float) -> InlineKeyboardMarkup:
    """Confirm launch of trading session"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚀 ПОДТВЕРДИТЬ СТАРТ", callback_data=f"confirm_start:{mode}:{amount}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")
        ]
    ])

def get_live_status_keyboard() -> InlineKeyboardMarkup:
    """Keyboard on live trade status message"""
    buttons = [
        [
            InlineKeyboardButton(text="🔄 Обновить статус", callback_data="refresh_live_status"),
            InlineKeyboardButton(text="🛑 Остановить", callback_data="ask_stop_trade")
        ]
    ]
    if WEBAPP_URL:
        buttons.append([InlineKeyboardButton(text="📈 Открыть в WebApp терминале", web_app=WebAppInfo(url=WEBAPP_URL))])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_stop_keyboard() -> InlineKeyboardMarkup:
    """Confirmation to stop trading"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛑 ДА, ЗАФИКСИРОВАТЬ И ВЫЙТИ", callback_data="do_stop_trade")
        ],
        [
            InlineKeyboardButton(text="◀️ Продолжить торговлю", callback_data="continue_trade")
        ]
    ])

def get_deposit_keyboard() -> InlineKeyboardMarkup:
    """Deposit actions"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил (Ввести TxID)", callback_data="enter_deposit_txid")],
        [InlineKeyboardButton(text="💬 Поддержка", url="https://t.me/RazgonZoneSupport")]
    ])

def get_admin_deposit_keyboard(deposit_id: int) -> InlineKeyboardMarkup:
    """Admin review of deposit"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить + Баланс", callback_data=f"admin_dep_ok:{deposit_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_dep_no:{deposit_id}")
        ]
    ])

def get_admin_withdraw_keyboard(withdraw_id: int) -> InlineKeyboardMarkup:
    """Admin review of withdrawal"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Выплачено", callback_data=f"admin_wdr_ok:{withdraw_id}"),
            InlineKeyboardButton(text="❌ Отклонить (вернуть)", callback_data=f"admin_wdr_no:{withdraw_id}")
        ]
    ])
