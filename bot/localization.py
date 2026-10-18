from typing import Dict, Any

LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "uz": "🇺🇿 O'zbekcha"
}

TEXTS: Dict[str, Dict[str, str]] = {
    # Main menu buttons
    "btn_start_trade": {
        "ru": "🚀 Запустить разгон",
        "uz": "🚀 Razgonni boshlash"
    },
    "btn_trade_status": {
        "ru": "📊 Статус разгона",
        "uz": "📊 Razgon holati"
    },
    "btn_stop_trade": {
        "ru": "🛑 Остановить разгон",
        "uz": "🛑 Razgonni to'xtatish"
    },
    "btn_cabinet": {
        "ru": "💼 Мой баланс",
        "uz": "💼 Mening hisobim"
    },
    "btn_deposit": {
        "ru": "📥 Пополнить USDT",
        "uz": "📥 USDT to'ldirish"
    },
    "btn_withdraw": {
        "ru": "📤 Вывод средств",
        "uz": "📤 Pulni yechish"
    },
    "btn_change_lang": {
        "ru": "🌐 Сменить язык",
        "uz": "🌐 Tilni o'zgartirish"
    },
    "btn_about": {
        "ru": "ℹ️ О сервисе",
        "uz": "ℹ️ Xizmat haqida"
    },
    "btn_check_deposit": {
        "ru": "🔄 Проверить статус оплаты",
        "uz": "🔄 To'lov holatini tekshirish"
    },
    "btn_manual_txid": {
        "ru": "⚡ Ввести TxID вручную",
        "uz": "⚡ TxID ni qo'lda kiritish"
    },
    "btn_support": {
        "ru": "💬 Поддержка",
        "uz": "💬 Qo'llab-quvvatlash"
    },

    # Welcome message (Apple-grade minimalist & confident)
    "welcome": {
        "ru": (
            "<b>RAZGON ZONE</b>\n"
            "Алгоритмический разгон криптоактивов.\n\n"
            "Привет, <b>{name}</b>. Чистая математика рынка вместо эмоций. "
            "Автоматизированный арбитраж и скальпинг волатильности без скрытых условий.\n\n"
            "💵 <b>Доступно на балансе:</b> <code>{balance:.2f} USDT</code>\n"
            "{trading_info}\n"
            "<b>Как это работает:</b>\n"
            "1. Пополните счет в <b>USDT (TRC-20)</b>.\n"
            "2. Нажмите <b>«🚀 Запустить разгон»</b>.\n"
            "3. По завершении торговой сессии заберите депозит и всю прибыль.\n\n"
            "🛡 <b>0% комиссии платформы.</b> Вся прибыль — только ваша.\n\n"
            "<i>Выберите действие в меню ниже:</i>"
        ),
        "uz": (
            "<b>RAZGON ZONE</b>\n"
            "Kripto-aktivlarni algoritmik razgon qilish platformasi.\n\n"
            "Assalomu alaykum, <b>{name}</b>. Bozor hisob-kitoblari va aniq texnologiya. "
            "Yashirin shartlarsiz va ortiqcha qiyinchiliklarsiz avtomatlashtirilgan savdo.\n\n"
            "💵 <b>Mavjud balans:</b> <code>{balance:.2f} USDT</code>\n"
            "{trading_info}\n"
            "<b>Qanday ishlaydi:</b>\n"
            "1. <b>USDT (TRC-20)</b> orqali hisobingizni to'ldiring.\n"
            "2. <b>«🚀 Razgonni boshlash»</b> tugmasini bosing.\n"
            "3. Sessiya yakunlangach, depozit va barcha sof foydani oling.\n\n"
            "🛡 <b>0% platforma komissiyasi.</b> Barcha foyda — 100% sizniki.\n\n"
            "<i>Quyidagi menyu orqali boshqaring:</i>"
        )
    },

    # Language selection
    "choose_language": {
        "ru": "🌐 <b>Выберите язык интерфейса / Tilni tanlang:</b>",
        "uz": "🌐 <b>Tilni tanlang / Выберите язык интерфейса:</b>"
    },
    "language_set": {
        "ru": "✅ Язык интерфейса: <b>Русский</b> 🇷🇺",
        "uz": "✅ Interfeys tili: <b>O'zbekcha</b> 🇺🇿"
    },

    # Cabinet
    "cabinet_info": {
        "ru": (
            "<b>МОЙ БАЛАНС | RAZGON ZONE</b>\n"
            "────────────────────\n"
            "👤 <b>Клиент:</b> {name} (ID: <code>{user_id}</code>)\n"
            "📊 <b>Статус:</b> {status_str}\n\n"
            "💰 <b>Свободный баланс:</b> <code>{balance:.2f} USDT</code>\n"
            "📈 <b>В активном разгоне:</b> <code>{in_trading:.2f} USDT</code>\n"
            "🏆 <b>Всего заработано:</b> <code>{total_profit:.2f} USDT</code>\n"
            "────────────────────\n"
            "🔒 <i>Все выплаты производятся напрямую в сети TRON.</i>"
        ),
        "uz": (
            "<b>MENING HISOBIM | RAZGON ZONE</b>\n"
            "────────────────────\n"
            "👤 <b>Mijoz:</b> {name} (ID: <code>{user_id}</code>)\n"
            "📊 <b>Holat:</b> {status_str}\n\n"
            "💰 <b>Erkin balans:</b> <code>{balance:.2f} USDT</code>\n"
            "📈 <b>Razgonda (ishda):</b> <code>{in_trading:.2f} USDT</code>\n"
            "🏆 <b>Jami ishlangan foyda:</b> <code>{total_profit:.2f} USDT</code>\n"
            "────────────────────\n"
            "🔒 <i>Barcha to'lovlar to'g'ridan-to'g'ri TRON tarmog'ida yuboriladi.</i>"
        )
    },

    # Deposit
    "deposit_info": {
        "ru": (
            "<b>ПОПОЛНЕНИЕ СЧЕТА | USDT (TRC-20)</b>\n"
            "────────────────────\n"
            "📍 <b>Официальный адрес для пополнения:</b>\n"
            "<code>{address}</code>\n\n"
            "⚡ <b>Как пополнить баланс:</b>\n"
            "1. Скопируйте адрес выше или отсканируйте QR-код.\n"
            "2. Отправьте от <b>50 USDT</b> в сети <b>TRON (TRC-20)</b>.\n"
            "3. Нажмите кнопку <b>«⚡ Отправить TxID»</b> ниже и отправьте хеш перевода для моментального зачисления на баланс!\n\n"
            "🔒 <i>Сеть: TRC-20. Отправляйте только USDT.</i>"
        ),
        "uz": (
            "<b>HISOB TO'LDIRISH | USDT (TRC-20)</b>\n"
            "────────────────────\n"
            "📍 <b>Rasmiy to'lov manzili:</b>\n"
            "<code>{address}</code>\n\n"
            "⚡ <b>Hisobni to'ldirish tartibi:</b>\n"
            "1. Yuqoridagi manzilni nusxalang yoki QR-kodni skanerlang.\n"
            "2. <b>TRON (TRC-20)</b> tarmog'ida kamida <b>50 USDT</b> yuboring.\n"
            "3. Mablag'ni tezda balansingizga qo'shish uchun quyidagi <b>«⚡ TxID yuborish»</b> tugmasini bosing va tranzaksiya heshini yuboring!\n\n"
            "🔒 <i>Tarmoq: TRC-20. Faqat USDT yuboring.</i>"
        )
    },

    # Trade launch
    "trade_no_money": {
        "ru": (
            "⚠️ <b>Недостаточно средств для старта разгона.</b>\n\n"
            "Ваш доступный баланс: <b>{balance:.2f} USDT</b>\n"
            "Минимум для входа: <b>50.00 USDT</b>\n\n"
            "Пополните счет через кнопку <b>«📥 Пополнить USDT»</b>."
        ),
        "uz": (
            "⚠️ <b>Razgonni boshlash uchun mablag' yetarli emas.</b>\n\n"
            "Mavjud balansingiz: <b>{balance:.2f} USDT</b>\n"
            "Boshlash uchun minimal summa: <b>50.00 USDT</b>\n\n"
            "Hisobni to'ldirish uchun <b>«📥 USDT to'ldirish»</b> tugmasini bosing."
        )
    },
    "trade_already_running": {
        "ru": (
            "⚠️ <b>У вас уже активен разгон.</b>\n\n"
            "Депозит в работе: <b>{amount:.2f} USDT</b>\n"
            "Торговая сессия сейчас продолжается. Ожидайте итоговый отчет трейдера."
        ),
        "uz": (
            "⚠️ <b>Sizda allaqachon razgon faol.</b>\n\n"
            "Ishdagi depozit: <b>{amount:.2f} USDT</b>\n"
            "Savdo sessiyasi davom etmoqda. Treyderdan yakuniy hisobotni kuting."
        )
    },
    "trade_started": {
        "ru": (
            "🚀 <b>РАЗГОН УСПЕШНО ЗАПУЩЕН</b>\n"
            "────────────────────\n"
            "💵 <b>Депозит в работе:</b> <code>{amount:.2f} USDT</code>\n"
            "⏱ <b>Статус:</b> В ТОРГОВЛЕ (Live)\n"
            "🛡 <b>Комиссия платформы:</b> 0% (вся прибыль ваша)\n\n"
            "Алгоритмы подключены к ликвидности рынка.\n"
            "Вам больше ничего делать не нужно — по завершении торгов вы получите детальный отчет и начисление всей прибыли на баланс."
        ),
        "uz": (
            "🚀 <b>RAZGON MUVAFFAQIYATLI ISHGA TUSHIRILDI</b>\n"
            "────────────────────\n"
            "💵 <b>Ishdagi depozit:</b> <code>{amount:.2f} USDT</code>\n"
            "⏱ <b>Holat:</b> SAVDODA (Live)\n"
            "🛡 <b>Platforma komissiyasi:</b> 0% (barcha foyda sizniki)\n\n"
            "Algoritmlar bozor likvidligiga ulandi.\n"
            "Boshqa hech narsa qilishingiz shart emas — savdo yakunlangach, hisobot taqdim etiladi va barcha sof foyda balansingizga tushadi."
        )
    },
    "trade_stopped": {
        "ru": (
            "🛑 <b>РАЗГОН ОСТАНОВЛЕН</b>\n"
            "────────────────────\n"
            "💵 Депозит <b>{amount:.2f} USDT</b> успешно возвращен на ваш свободный баланс.\n\n"
            "Вы можете вывести средства или запустить разгон заново в любой момент."
        ),
        "uz": (
            "🛑 <b>RAZGON TO'XTATILDI</b>\n"
            "────────────────────\n"
            "💵 <b>{amount:.2f} USDT</b> miqdoridagi depozit erkin balansingizga qaytarildi.\n\n"
            "Mablag'ingizni yechib olishingiz yoki istalgan vaqtda qaytadan razgon boshlashingiz mumkin."
        )
    },

    # Live status
    "status_running": {
        "ru": (
            "📊 <b>СТАТУС РАЗГОНА | В РАБОТЕ</b>\n"
            "────────────────────\n"
            "💵 <b>Сумма депозита:</b> <code>{amount:.2f} USDT</code>\n"
            "⏱ <b>Время старта:</b> <code>{started_at}</code>\n"
            "📈 <b>Состояние:</b> Активная торговая сессия...\n"
            "────────────────────\n"
            "💡 <i>По завершении торговли вы получите официальный отчет с зачислением всей прибыли на баланс.</i>"
        ),
        "uz": (
            "📊 <b>RAZGON HOLATI | JARAYONDA</b>\n"
            "────────────────────\n"
            "💵 <b>Depozit summasi:</b> <code>{amount:.2f} USDT</code>\n"
            "⏱ <b>Boshlangan vaqt:</b> <code>{started_at}</code>\n"
            "📈 <b>Holat:</b> Faol savdo sessiyasi ketmoqda...\n"
            "────────────────────\n"
            "💡 <i>Savdo yakunlangach, barcha sof foyda bilan birga to'liq hisobot balansingizga taqdim etiladi.</i>"
        )
    },
    "status_not_running": {
        "ru": (
            "⚪️ <b>Торговля сейчас не запущена.</b>\n\n"
            "Нажмите <b>«🚀 Запустить разгон»</b>, чтобы начать."
        ),
        "uz": (
            "⚪️ <b>Hozirda faol razgon yo'q.</b>\n\n"
            "Boshlash uchun <b>«🚀 Razgonni boshlash»</b> tugmasini bosing."
        )
    },

    # Final report sent by admin
    "session_report": {
        "ru": (
            "🏁 <b>ТОРГОВАЯ СЕССИЯ УСПЕШНО ЗАВЕРШЕНА</b> 🚀\n"
            "────────────────────\n"
            "💵 <b>Исходный депозит:</b> <code>{deposit:.2f} USDT</code>\n"
            "📈 <b>Чистая прибыль:</b> <code>+{profit:.2f} USDT</code> (<b>+{pnl_pct:.1f}%</b>)\n"
            "🛡 <b>Комиссия платформы:</b> <code>0.00 USDT (0%)</code>\n"
            "────────────────────\n"
            "💰 <b>ИТОГО ЗАЧИСЛЕНО НА БАЛАНС:</b> <code>{total:.2f} USDT</code> ✅\n"
            "{note}\n"
            "────────────────────\n"
            "🎉 <i>Средства на балансе. Вы можете заказать вывод или запустить новый разгон.</i>"
        ),
        "uz": (
            "🏁 <b>SAVDO SESSIYASI MUVAFFAQIYATLI YAKUNLANDI</b> 🚀\n"
            "────────────────────\n"
            "💵 <b>Boshlang'ich depozit:</b> <code>{deposit:.2f} USDT</code>\n"
            "📈 <b>Sof foyda:</b> <code>+{profit:.2f} USDT</code> (<b>+{pnl_pct:.1f}%</b>)\n"
            "🛡 <b>Platforma komissiyasi:</b> <code>0.00 USDT (0%)</code>\n"
            "────────────────────\n"
            "💰 <b>JAMI BALANSGA O'TKAZILDI:</b> <code>{total:.2f} USDT</code> ✅\n"
            "{note}\n"
            "────────────────────\n"
            "🎉 <i>Mablag' balansingizda mavjud. Pulni yechib olishingiz yoki yangi razgon boshlashingiz mumkin.</i>"
        )
    },

    # Withdrawal
    "withdraw_prompt_amount": {
        "ru": (
            "📤 <b>ВЫВОД СРЕДСТВ | USDT (TRC-20)</b>\n\n"
            "Доступно к выводу: <b>{balance:.2f} USDT</b>\n"
            "Минимальная сумма: <b>10.00 USDT</b>\n\n"
            "Введите сумму для вывода:"
        ),
        "uz": (
            "📤 <b>PUL CHIQARISH | USDT (TRC-20)</b>\n\n"
            "Yechib olish uchun mavjud: <b>{balance:.2f} USDT</b>\n"
            "Minimal summa: <b>10.00 USDT</b>\n\n"
            "Yechib olmoqchi bo'lgan summani kiriting:"
        )
    },
    "withdraw_prompt_address": {
        "ru": (
            "Сумма к выводу: <b>{amount:.2f} USDT</b>\n\n"
            "Отправьте ваш адрес кошелька <b>TRON (TRC-20)</b>:\n"
            "<i>(Пример: T...)</i>"
        ),
        "uz": (
            "Yechilayotgan summa: <b>{amount:.2f} USDT</b>\n\n"
            "Mablag'ni qabul qilish uchun <b>TRON (TRC-20)</b> hamyon manzilingizni yuboring:\n"
            "<i>(Misol: T...)</i>"
        )
    },
    "withdraw_success": {
        "ru": (
            "✅ <b>Заявка на вывод #{wdr_id} принята</b>\n\n"
            "💵 Сумма: <b>{amount:.2f} USDT</b>\n"
            "📍 Адрес выплаты: <code>{address}</code>\n\n"
            "Выплата отправляется в течение 15–60 минут после подтверждения безопасности."
        ),
        "uz": (
            "✅ <b>Chiqarish uchun #{wdr_id}-ariza qabul qilindi</b>\n\n"
            "💵 Summa: <b>{amount:.2f} USDT</b>\n"
            "📍 To'lov manzili: <code>{address}</code>\n\n"
            "Mablag' 15–60 daqiqa ichida xavfsizlik tekshiruvidan so'ng yuboriladi."
        )
    },

    # About (Apple-style minimalism & focus)
    "about": {
        "ru": (
            "<b>RAZGON ZONE</b>\n"
            "Алгоритмический трейдинг нового поколения.\n"
            "────────────────────\n\n"
            "<b>Простота. Скорость. Прозрачность.</b>\n\n"
            "Мы устранили всё лишнее: сложные графики, запутанные настройки и скрытые комиссии. "
            "Алгоритмы отслеживают импульсы рынка в реальном времени, а вы контролируете процесс в одно касание.\n\n"
            "<b>Наши принципы:</b>\n"
            "• <b>0% комиссии платформы.</b> Вся заработанная прибыль принадлежит вам.\n"
            "• <b>В один клик.</b> Депозит ➔ Запуск ➔ Точный отчет и фиксация прибыли.\n"
            "• <b>Персональный TRC-20 адрес.</b> Мгновенное автозачисление в сети TRON.\n"
            "• <b>Полная прозрачность.</b> Финальный отчет с точным PnL по каждой сессии.\n\n"
            "💬 Поддержка: @RazgonZoneSupport"
        ),
        "uz": (
            "<b>RAZGON ZONE</b>\n"
            "Yangi avlod algoritmik treydingi.\n"
            "────────────────────\n\n"
            "<b>Oddiylik. Tezlik. Shaffoflik.</b>\n\n"
            "Biz barcha ortiqcha narsalarni olib tashladik: murakkab grafiklar, chalkash sozlamalar va yashirin to'lovlar. "
            "Algoritmlar bozor harakatlarini real vaqtda tahlil qiladi, siz esa jarayonni birgina tugma orqali boshqarasiz.\n\n"
            "<b>Bizning prinsiplarimiz:</b>\n"
            "• <b>0% platforma komissiyasi.</b> Barcha sof foyda 100% sizniki.\n"
            "• <b>Birgina bosishda.</b> Depozit ➔ Start ➔ Aniq hisobot va foydani olish.\n"
            "• <b>Shaxsiy TRC-20 manzil.</b> TRON tarmog'ida bir zumda avtomatik to'ldirish.\n"
            "• <b>To'liq shaffoflik.</b> Har bir sessiya bo'yicha aniq PnL hisoboti.\n\n"
            "💬 Qo'llab-quvvatlash: @RazgonZoneSupport"
        )
    }
}

def tr(key: str, lang: str = "ru", **kwargs) -> str:
    """Helper to retrieve translated and formatted string"""
    lang_dict = TEXTS.get(key, {})
    template = lang_dict.get(lang, lang_dict.get("ru", key))
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template
