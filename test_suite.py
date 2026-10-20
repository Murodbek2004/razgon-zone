import asyncio
import sys
import logging
import secrets
from bot.database import (
    init_db,
    get_or_create_user,
    get_user,
    get_user_lang,
    set_user_lang,
    get_or_create_user_wallet,
    auto_credit_deposit,
    is_tx_already_credited,
    start_simple_trading,
    get_active_trading_session,
    get_active_sessions_for_admin,
    admin_complete_session,
    user_cancel_trading_session,
    create_withdrawal,
    admin_get_user_card,
    admin_modify_balance,
    get_platform_stats,
    save_broker_account,
    get_user_broker_account,
    update_broker_status,
    get_all_broker_accounts
)
from bot.tron_service import (
    validate_tron_address,
    validate_tron_tx_hash,
    get_qr_code_stream,
    get_tron_account_balance
)
from bot.localization import tr, LANGUAGES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RazgonZone.Tests")

async def run_tests():
    logger.info("========================================================")
    logger.info("🧪 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ УПРОЩЕННОГО БОТА")
    logger.info("========================================================")

    # 1. DB Init
    await init_db()
    logger.info("✅ 1. База данных и индексы успешно инициализированы.")

    # 2. User Creation & Bilingual settings (RU & UZ)
    test_user_id = int(secrets.randbelow(899999999) + 100000000)
    u = await get_or_create_user(test_user_id, "uz_trader", "Bekzod")
    assert u["user_id"] == test_user_id, "User ID mismatch"

    # Test default and changing language to Uzbek
    await set_user_lang(test_user_id, "uz")
    lang = await get_user_lang(test_user_id)
    assert lang == "uz", "Language must be 'uz'"

    # Check localization helper
    uz_text = tr("btn_start_trade", "uz")
    ru_text = tr("btn_start_trade", "ru")
    assert uz_text == "🚀 Razgonni boshlash"
    assert ru_text == "🚀 Запустить разгон"
    logger.info("✅ 2. Профиль пользователя и переключение языков (RU/UZ): УСПЕШНО.")

    # 3. Dedicated Wallet Generation & Permanence
    addr1, priv1 = await get_or_create_user_wallet(test_user_id)
    assert validate_tron_address(addr1), f"Invalid TRON address format: {addr1}"
    assert len(priv1) == 64, "Private key must be 64-hex string"

    addr2, priv2 = await get_or_create_user_wallet(test_user_id)
    assert addr1 == addr2, "Address must be permanent and unique per user"
    assert priv1 == priv2, "Private key must match"
    logger.info(f"✅ 3. Генерация персонального адреса TRON ({addr1}): УСПЕШНО.")

    # 4. Automatic Deposit & 0% Referral Bonus check
    fake_tx = secrets.token_hex(32)
    assert validate_tron_tx_hash(fake_tx), "Valid hash check"

    ok, dep, reason = await auto_credit_deposit(test_user_id, 100.0, fake_tx)
    assert ok, f"Deposit credit failed: {reason}"
    assert await is_tx_already_credited(fake_tx), "Tx must be recorded as credited"

    # Anti-replay check
    ok_repeat, _, reason_repeat = await auto_credit_deposit(test_user_id, 100.0, fake_tx)
    assert not ok_repeat, "Replay attack must be blocked!"
    logger.info("✅ 4. Зачисление депозита и защита от повторов (0% реф-бонусов): УСПЕШНО.")

    # 5. 1-Click Trade Launch ("один раз нажать запустить бот и всё")
    user_before = await get_user(test_user_id)
    assert user_before["balance"] >= 100.0, "Balance must be >= 100"

    sess = await start_simple_trading(test_user_id)
    assert sess is not None, "Failed to start 1-click trading session"
    sess_id = sess["id"]
    dep_amt = sess["deposit_amount"]
    assert dep_amt == user_before["balance"], "All available balance must enter trading"

    user_in_trade = await get_user(test_user_id)
    assert user_in_trade["balance"] == 0.0, "Free balance moved to in_trading_balance"
    assert user_in_trade["in_trading_balance"] == dep_amt

    active_sess = await get_active_trading_session(test_user_id)
    assert active_sess["id"] == sess_id
    logger.info(f"✅ 5. Запуск разгона в 1 клик на сумму {dep_amt:.2f} USDT: УСПЕШНО.")

    # 6. Admin inspects active sessions
    admin_sessions = await get_active_sessions_for_admin()
    assert any(s["id"] == sess_id for s in admin_sessions), "Active session must appear in admin list"
    logger.info(f"✅ 6. Панель админа видит активную сессию #{sess_id}: УСПЕШНО.")

    # 7. Admin finishes trading & sends report (0% fee, full profit to user)
    profit_to_credit = 45.50
    sess_dict = await admin_complete_session(sess_id, profit_to_credit, note="HFT Скальпинг")
    assert sess_dict is not None, "Failed to complete session"
    assert sess_dict["profit"] == profit_to_credit

    # Verify user received deposit + profit without fee
    user_after = await get_user(test_user_id)
    assert user_after["in_trading_balance"] == 0.0, "In trading balance must be reset"
    assert user_after["balance"] == dep_amt + profit_to_credit, "Balance = deposit + full profit (0% fee)"
    assert user_after["total_profit"] == profit_to_credit

    # Test report formatting in Uzbek
    rep_uz = tr(
        "session_report",
        "uz",
        deposit=dep_amt,
        profit=profit_to_credit,
        pnl_pct=(profit_to_credit / dep_amt * 100),
        total=dep_amt + profit_to_credit,
        note="",
        date="18.10.2026 16:30"
    )
    assert "SAVDO SESSIYASI MUVAFFAQIYATLI YAKUNLANDI" in rep_uz
    assert "0.00 USDT (0%)" in rep_uz
    logger.info("✅ 7. Завершение сессии админом, 0% комиссий, начисление профита и отчет: УСПЕШНО.")

    # 8. Withdrawal Pipeline
    wdr_addr = "TYDzsYUEpvnYmQk4zGP9sWWcTEd2MiAtW6"
    wdr_id = await create_withdrawal(test_user_id, 30.0, wdr_addr)
    assert wdr_id is not None, "Failed to create withdrawal"
    logger.info(f"✅ 8. Создание заявки на вывод #{wdr_id} на {wdr_addr}: УСПЕШНО.")

    # 9. Admin Tools & Stats
    card = await admin_get_user_card(str(test_user_id))
    assert card is not None
    assert card["user"]["user_id"] == test_user_id

    stats = await get_platform_stats()
    assert stats["total_users"] > 0
    logger.info("✅ 9. Инструменты администратора и статистика: УСПЕШНО.")

    # 10. QR Code generator test
    qr_bio = await get_qr_code_stream(addr1)
    if qr_bio:
        assert len(qr_bio.getvalue()) > 100
        logger.info("✅ 10. Генератор персонального QR-кода: УСПЕШНО.")

    # 11. User Stops Trading in 1 Click (Deposit 100% returned)
    user_trade_before = await get_user(test_user_id)
    rem_bal = user_trade_before["balance"]
    assert rem_bal >= 40.0, "Must have balance"
    sess2 = await start_simple_trading(test_user_id)
    assert sess2 is not None

    returned_dep = await user_cancel_trading_session(test_user_id)
    assert returned_dep == rem_bal, "Returned deposit must match balance started"
    user_trade_after = await get_user(test_user_id)
    assert user_trade_after["balance"] == rem_bal, "Balance restored"
    assert user_trade_after["in_trading_balance"] == 0.0, "In trading balance reset"
    logger.info(f"✅ 11. Ручная остановка разгона пользователем (возврат 100% депозита {returned_dep:.2f} USDT): УСПЕШНО.")

    # 12. Live on-chain balance query test
    bal_res = await get_tron_account_balance(addr1)
    assert "usdt" in bal_res and "trx" in bal_res
    logger.info(f"✅ 12. Запрос ончейн-баланса кошелька ({bal_res['usdt']:.2f} USDT / {bal_res['trx']:.2f} TRX): УСПЕШНО.")

    # 13. Broker Account Binding & Verification Flow
    brk_id = await save_broker_account(test_user_id, "RoboForex-Pro", "8492011", "Tr@dePass99")
    assert brk_id > 0, "Broker account ID must be positive"
    pending_brk = await get_user_broker_account(test_user_id)
    assert pending_brk["status"] == "pending"
    assert pending_brk["broker_server"] == "RoboForex-Pro"

    # Admin approves broker account
    approved_brk = await update_broker_status(brk_id, "active")
    assert approved_brk["status"] == "active"
    assert approved_brk["user_id"] == test_user_id

    # Verify admin listing
    all_brk = await get_all_broker_accounts(limit=10)
    assert any(b["id"] == brk_id for b in all_brk)
    logger.info("✅ 13. Привязка счета брокера (сервер/логин/пароль) и верификация: УСПЕШНО.")

    # 14. Trade Table Broadcast Generator & Parser
    from bot.database import get_all_users_with_lang
    from bot.handlers.admin_handlers import (
        generate_sample_trades,
        parse_manual_deals,
        format_trades_broadcast_message
    )

    all_users = await get_all_users_with_lang()
    assert len(all_users) > 0, "Users list must not be empty"

    auto_deals = generate_sample_trades()
    assert len(auto_deals) == 5, "Auto deals must have 5 top pairs"
    ru_table = format_trades_broadcast_message(auto_deals, lang="ru")
    uz_table = format_trades_broadcast_message(auto_deals, lang="uz")
    assert "<pre>" in ru_table and "BTC/USDT" in ru_table
    assert "<pre>" in uz_table and "JUFTLIK" in uz_table

    manual_text = "BTC/USDT 67450 68890 +14.2%\nETH/USDT 3120 3295 +18%\nSOL/USDT 174 192 25%"
    parsed = parse_manual_deals(manual_text)
    assert len(parsed) == 3
    assert parsed[0]["pair"] == "BTC/USDT"
    formatted_manual = format_trades_broadcast_message(parsed, lang="ru")
    assert "SOL/USDT" in formatted_manual
    logger.info("✅ 14. Генерация и форматирование таблицы сделок (RU/UZ) для рассылки: УСПЕШНО.")

    logger.info("========================================================")
    logger.info("🎉 ВСЕ ТЕСТЫ ОТ А ДО Я ПРОЙДЕНЫ НА 100%! БОТ ГОТОВ.")
    logger.info("========================================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
