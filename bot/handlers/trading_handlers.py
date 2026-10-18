from aiogram import Router, F
from aiogram.types import CallbackQuery

from ..database import get_user_lang, get_active_trading_session
from ..localization import tr
from ..keyboards import get_main_reply_keyboard

router = Router()

# Legacy callbacks redirect to simplified flow
@router.callback_query(F.data.startswith("select_mode:"))
async def on_legacy_select_mode(call: CallbackQuery):
    user_lang = await get_user_lang(call.from_user.id)
    active_sess = await get_active_trading_session(call.from_user.id)
    is_trading = active_sess is not None

    msg = "💡 Платформа упрощена: теперь разгон запускается в 1 клик через главное меню!" if user_lang == "ru" else "💡 Platforma soddalashtirildi: endi razgon asosiy menyu orqali 1 ta bosishda ishga tushadi!"
    await call.answer(msg, show_alert=True)
    await call.message.delete()
    await call.message.answer(
        msg,
        reply_markup=get_main_reply_keyboard(lang=user_lang, is_trading=is_trading)
    )

@router.callback_query(F.data.in_(["confirm_stop_trade", "cancel_stop_trade"]))
async def on_legacy_stop(call: CallbackQuery):
    user_lang = await get_user_lang(call.from_user.id)
    active_sess = await get_active_trading_session(call.from_user.id)
    is_trading = active_sess is not None

    msg = "💡 Итоговый отчет и прибыль присылает трейдер по окончании торговой сессии." if user_lang == "ru" else "💡 Yakuniy hisobot va sof foydani savdo sessiyasi tugagach treyder taqdim etadi."
    await call.answer(msg, show_alert=True)
