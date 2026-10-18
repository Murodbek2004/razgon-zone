from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from .localization import tr, LANGUAGES

def get_main_reply_keyboard(lang: str = "ru", is_trading: bool = False) -> ReplyKeyboardMarkup:
    """Bottom persistent menu keyboard (multilingual RU / UZ)"""
    kb = []
    
    if is_trading:
        kb.append([
            KeyboardButton(text=tr("btn_trade_status", lang)),
            KeyboardButton(text=tr("btn_stop_trade", lang))
        ])
        kb.append([
            KeyboardButton(text=tr("btn_cabinet", lang))
        ])
    else:
        kb.append([
            KeyboardButton(text=tr("btn_start_trade", lang)),
            KeyboardButton(text=tr("btn_cabinet", lang))
        ])

    kb.append([
        KeyboardButton(text=tr("btn_deposit", lang)),
        KeyboardButton(text=tr("btn_withdraw", lang))
    ])
    kb.append([
        KeyboardButton(text=tr("btn_change_lang", lang)),
        KeyboardButton(text=tr("btn_about", lang))
    ])

    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_language_inline_keyboard() -> InlineKeyboardMarkup:
    """Language selection keyboard"""
    buttons = [
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang:ru"),
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="set_lang:uz")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_deposit_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Deposit actions with auto-check & manual fallback"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr("btn_check_deposit", lang), callback_data="check_my_deposit_now")],
        [InlineKeyboardButton(text=tr("btn_manual_txid", lang), callback_data="enter_deposit_txid")],
        [InlineKeyboardButton(text=tr("btn_support", lang), url="https://t.me/RazgonZoneSupport")]
    ])

def get_admin_dashboard_keyboard() -> InlineKeyboardMarkup:
    """Admin interactive dashboard with session completion"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Обновить сводку", callback_data="adm_refresh_stats"),
            InlineKeyboardButton(text="🚀 Активные разгоны (Отчет)", callback_data="adm_active_sessions")
        ],
        [
            InlineKeyboardButton(text="🔑 Кошельки клиентов", callback_data="adm_view_wallets"),
            InlineKeyboardButton(text="👤 Поиск юзера / Баланс", callback_data="adm_find_user")
        ],
        [
            InlineKeyboardButton(text="📤 Заявки на вывод", callback_data="adm_pending_wdr"),
            InlineKeyboardButton(text="📥 История пополнений", callback_data="adm_recent_dep")
        ],
        [
            InlineKeyboardButton(text="📢 Рассылка всем", callback_data="adm_broadcast")
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
