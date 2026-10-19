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
        KeyboardButton(text=tr("btn_bind_broker", lang)),
        KeyboardButton(text=tr("btn_change_lang", lang))
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

def get_broker_menu_keyboard(lang: str = "ru", has_account: bool = False, is_active: bool = False) -> InlineKeyboardMarkup:
    """Broker account management inline keyboard"""
    if has_account:
        btn_text = "🔄 Подключить другой счет" if lang == "ru" else "🔄 Boshqa hisobni ulash"
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=btn_text, callback_data="broker_enter_data")]
        ])
    else:
        btn_connect = "⚡ Подключить счет" if lang == "ru" else "⚡ Hisobni ulash"
        btn_cancel = "❌ Отмена" if lang == "ru" else "❌ Bekor qilish"
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=btn_connect, callback_data="broker_enter_data")],
            [InlineKeyboardButton(text=btn_cancel, callback_data="broker_cancel")]
        ])

def get_broker_cancel_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Cancel broker binding input"""
    btn_cancel = "❌ Отмена" if lang == "ru" else "❌ Bekor qilish"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_cancel, callback_data="broker_cancel")]
    ])

def get_admin_broker_keyboard(account_id: int) -> InlineKeyboardMarkup:
    """Admin review of broker account credentials"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить подключение", callback_data=f"adm_brk_ok:{account_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_brk_no:{account_id}")
        ]
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
            InlineKeyboardButton(text="📢 Рассылка всем", callback_data="adm_broadcast"),
            InlineKeyboardButton(text="✉️ Написать клиенту", callback_data="adm_direct_msg")
        ],
        [
            InlineKeyboardButton(text="💼 Счета брокеров (MT4/5)", callback_data="adm_view_brokers")
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
