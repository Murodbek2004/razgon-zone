---
title: Razgon Zone
emoji: 🚀
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

# ⚡ RAZGON ZONE — HFT & Crypto Trading Telegram Platform

Платформа алгоритмического разгона депозитов с приемом **USDT TRC-20**, live-мониторингом торговли, спидометром разгона, фиксацией прибыли в 1 клик и встроенным **Telegram Mini App (Web App)**.

---

## 🚀 Возможности платформы

1. 💎 **Депозиты в USDT (TRC-20):**
   - Персональный кошелек и QR-код для пополнения.
   - Проверка и верификация транзакций по TxID (TronScan).
   - Мгновенный пересчет баланса после подтверждения.

2. 📈 **Алгоритмический разгон баланса:**
   - Три стратегии на выбор:
     - 🛡️ **Safe Run:** +3.5% ~ +8.0% (арбитраж, минимальный риск).
     - ⚡ **Optimal Boost:** +12.0% ~ +25.0% (трендовый скальпинг BTC/ETH/SOL).
     - 🔥 **Turbo Razgon:** +30.0% ~ +75.0% (импульсный памп альткоинов).

3. 📊 **Live Статус торговли:**
   - Отображение текущего депозита, профита (+PnL в USDT и в %), времени в сессии.
   - Лента открытых и закрытых позиций с точками входа и профитом.
   - Спидометр скорости разгона (0–100%).

4. 🛑 **Остановка торговли в 1 клик:**
   - По нажатию «Остановить торговлю» сессия мгновенно закрывается.
   - Прибыль фиксируется на балансе клиента.
   - Генерируется итоговый чек-отчет **«Razgon Report»**.

5. 📤 **Вывод средств:**
   - Заказ вывода на любой кошелек сети TRON (TRC-20).
   - Админ-панель для подтверждения выплат и депозитов.

6. 📱 **Telegram Mini App (Web App):**
   - Неоновый киберпанк интерфейс прямо внутри Telegram.
   - Анимированный спидометр на HTML5 Canvas.
   - График доходности (PnL Curve) в реальном времени.
   - Haptic Feedback (тактильный отклик) при нажатиях.

---

## 🛠 Быстрый запуск на Railway

### Вариант 1. Через Railway CLI (уже установлен на вашей машине):

```bash
# 1. Авторизация в Railway (откроет браузер)
railway login

# 2. Инициализация и привязка нового проекта
railway init

# 3. Деплой бота в облако
railway up
```

### Вариант 2. Через GitHub (автоматический деплой при каждом коммите):

1. Запушьте код в ваш репозиторий GitHub:
   ```bash
   git init
   git add .
   git commit -m "feat: Razgon Zone platform"
   git branch -M main
   git remote add origin https://github.com/ВАШ_АККАУНТ/razgon-zone.git
   git push -u origin main
   ```
2. Откройте [Railway.app](https://railway.com) ➔ Нажмите **«+ New Project»** ➔ Выберите **«Deploy from GitHub repo»**.
3. Выберите ваш репозиторий `razgon-zone`.
4. В разделе **Variables** добавьте:
   - `BOT_TOKEN`: токен вашего бота от [@BotFather](https://t.me/BotFather)
   - `ADMIN_IDS`: ваш числовой Telegram ID (можно узнать у [@userinfobot](https://t.me/userinfobot))
   - `TRON_USDT_WALLET`: ваш реальный TRC-20 кошелек для приема депозитов
   - `WEBAPP_URL`: ссылка на созданный сервис Railway (например `https://razgon-zone.up.railway.app`)
5. Railway автоматически соберет Dockerfile и запустит бота 24/7!

---

## 💻 Локальный запуск (тестирование на ПК)

```bash
# 1. Установка зависимостей
pip install -r requirements.txt

# 2. Скопируйте и заполните переменные
copy .env.example .env
# Отредактируйте .env (укажите BOT_TOKEN)

# 3. Запуск
python main.py
```
Web-терминал будет доступен по адресу: `http://localhost:8080`
