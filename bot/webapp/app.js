// Razgon Zone — High-Frequency Trading Terminal Logic
(function() {
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
    try {
      tg.setHeaderColor('#080B10');
      tg.setBackgroundColor('#080B10');
    } catch (e) {}
  }

  // State
  let userId = null;
  let userName = "Трейдер";
  let isTrading = false;
  let currentSpeed = 0;
  let targetSpeed = 0;
  let pnlHistory = [0, 0.4, 0.8, 1.3, 1.9, 2.7, 3.2, 4.1];
  let selectedMode = "optimal";
  let activeSession = null;

  // Detect user from Telegram initData or fallback
  if (tg?.initDataUnsafe?.user) {
    userId = tg.initDataUnsafe.user.id;
    userName = tg.initDataUnsafe.user.first_name || "Трейдер";
  } else {
    const urlParams = new URLSearchParams(window.location.search);
    userId = urlParams.get('user_id') || 10001;
    userName = urlParams.get('name') || "Демо Трейдер";
  }

  // DOM Elements
  const elUserName = document.getElementById("userName");
  const elModeBadge = document.getElementById("modeBadge");
  const elSpeedValue = document.getElementById("speedValue");
  const elFreeBalance = document.getElementById("freeBalance");
  const elTradingBalance = document.getElementById("tradingBalance");
  const elCurrentProfit = document.getElementById("currentProfit");
  const elPnlPercent = document.getElementById("pnlPercent");
  const elTotalProfit = document.getElementById("totalProfit");
  const elActionBtn = document.getElementById("mainActionBtn");
  const elActionBtnText = document.getElementById("actionBtnText");
  const elDealsList = document.getElementById("dealsList");

  // Modals
  const modeModal = document.getElementById("modeModal");
  const depositModal = document.getElementById("depositModal");
  const depositBtn = document.getElementById("depositBtn");
  const withdrawBtn = document.getElementById("withdrawBtn");
  const closeModeModal = document.getElementById("closeModeModal");
  const closeDepositModal = document.getElementById("closeDepositModal");
  const confirmLaunchBtn = document.getElementById("confirmLaunchBtn");
  const tradeAmountInput = document.getElementById("tradeAmountInput");
  const walletInput = document.getElementById("walletInput");
  const copyWalletBtn = document.getElementById("copyWalletBtn");
  const depQrImage = document.getElementById("depQrImage");

  elUserName.textContent = userName;

  function triggerHaptic(type = "medium") {
    if (tg?.HapticFeedback) {
      if (type === "heavy") tg.HapticFeedback.impactOccurred("heavy");
      else if (type === "success") tg.HapticFeedback.notificationOccurred("success");
      else tg.HapticFeedback.impactOccurred("light");
    }
  }

  // Setup Canvas Gauge
  const gaugeCanvas = document.getElementById("gaugeCanvas");
  const gaugeCtx = gaugeCanvas.getContext("2d");

  function drawGauge(speed) {
    const w = gaugeCanvas.width;
    const h = gaugeCanvas.height;
    const cx = w / 2;
    const cy = h - 20;
    const radius = 95;

    gaugeCtx.clearRect(0, 0, w, h);

    // Background Arc
    gaugeCtx.beginPath();
    gaugeCtx.arc(cx, cy, radius, Math.PI, 0, false);
    gaugeCtx.lineWidth = 14;
    gaugeCtx.strokeStyle = "rgba(255, 255, 255, 0.08)";
    gaugeCtx.lineCap = "round";
    gaugeCtx.stroke();

    // Active Glowing Arc
    const progressAngle = Math.PI + (speed / 100) * Math.PI;
    const grad = gaugeCtx.createLinearGradient(0, cy, w, cy);
    grad.addColorStop(0, "#00F0FF");
    grad.addColorStop(0.5, "#00FFA3");
    grad.addColorStop(1, "#FF0055");

    gaugeCtx.beginPath();
    gaugeCtx.arc(cx, cy, radius, Math.PI, progressAngle, false);
    gaugeCtx.lineWidth = 14;
    gaugeCtx.strokeStyle = grad;
    gaugeCtx.lineCap = "round";
    gaugeCtx.shadowColor = "#00FFA3";
    gaugeCtx.shadowBlur = 12;
    gaugeCtx.stroke();
    gaugeCtx.shadowBlur = 0;

    // Needle
    const needleAngle = Math.PI + (speed / 100) * Math.PI;
    const nx = cx + Math.cos(needleAngle) * (radius - 16);
    const ny = cy + Math.sin(needleAngle) * (radius - 16);

    gaugeCtx.beginPath();
    gaugeCtx.moveTo(cx, cy);
    gaugeCtx.lineTo(nx, ny);
    gaugeCtx.lineWidth = 3;
    gaugeCtx.strokeStyle = "#FFFFFF";
    gaugeCtx.shadowColor = "#FFFFFF";
    gaugeCtx.shadowBlur = 8;
    gaugeCtx.stroke();
    gaugeCtx.shadowBlur = 0;

    // Center pivot
    gaugeCtx.beginPath();
    gaugeCtx.arc(cx, cy, 6, 0, Math.PI * 2);
    gaugeCtx.fillStyle = "#00FFA3";
    gaugeCtx.fill();
  }

  // Setup Canvas Live Chart
  const pnlCanvas = document.getElementById("pnlChart");
  const pnlCtx = pnlCanvas.getContext("2d");

  function drawChart() {
    const w = pnlCanvas.width;
    const h = pnlCanvas.height;
    pnlCtx.clearRect(0, 0, w, h);

    if (pnlHistory.length < 2) return;

    const maxVal = Math.max(...pnlHistory, 1.0) * 1.15;
    const minVal = 0;
    const stepX = w / (pnlHistory.length - 1);

    // Draw area fill
    pnlCtx.beginPath();
    pnlCtx.moveTo(0, h);
    pnlHistory.forEach((val, i) => {
      const x = i * stepX;
      const y = h - ((val - minVal) / (maxVal - minVal)) * (h - 20) - 10;
      if (i === 0) pnlCtx.lineTo(x, y);
      else pnlCtx.lineTo(x, y);
    });
    pnlCtx.lineTo(w, h);
    pnlCtx.closePath();

    const areaGrad = pnlCtx.createLinearGradient(0, 0, 0, h);
    areaGrad.addColorStop(0, "rgba(0, 255, 163, 0.25)");
    areaGrad.addColorStop(1, "rgba(0, 255, 163, 0.0)");
    pnlCtx.fillStyle = areaGrad;
    pnlCtx.fill();

    // Draw glowing line
    pnlCtx.beginPath();
    pnlHistory.forEach((val, i) => {
      const x = i * stepX;
      const y = h - ((val - minVal) / (maxVal - minVal)) * (h - 20) - 10;
      if (i === 0) pnlCtx.moveTo(x, y);
      else pnlCtx.lineTo(x, y);
    });
    pnlCtx.lineWidth = 2.5;
    pnlCtx.strokeStyle = "#00FFA3";
    pnlCtx.shadowColor = "#00FFA3";
    pnlCtx.shadowBlur = 10;
    pnlCtx.stroke();
    pnlCtx.shadowBlur = 0;
  }

  // Animation Loop for gauge
  function animateGauge() {
    currentSpeed += (targetSpeed - currentSpeed) * 0.1;
    drawGauge(currentSpeed);
    elSpeedValue.innerHTML = `${Math.round(currentSpeed)}<span class="unit">%</span>`;
    requestAnimationFrame(animateGauge);
  }
  animateGauge();

  // API Integration: Fetch live status
  async function syncStatus() {
    try {
      const res = await fetch(`/api/status?user_id=${userId}`);
      if (!res.ok) return;
      const data = await res.json();

      elFreeBalance.textContent = `${data.user.balance.toFixed(2)} `;
      elTradingBalance.textContent = `${data.user.in_trading_balance.toFixed(2)} `;
      elTotalProfit.textContent = `${data.user.total_profit.toFixed(2)} `;

      if (data.session && data.session.active) {
        isTrading = true;
        activeSession = data.session;
        targetSpeed = data.session.speed_val || 75;
        elModeBadge.textContent = `🟢 ${data.session.mode_title}`;
        elModeBadge.classList.add("active-mode");

        elCurrentProfit.textContent = `+${data.session.profit.toFixed(2)} USDT`;
        elPnlPercent.textContent = `+${data.session.pnl_percent.toFixed(2)}%`;

        elActionBtn.classList.add("stop-mode");
        elActionBtnText.textContent = "🛑 ОСТАНОВИТЬ И ЗАФИКСИРОВАТЬ";

        // Update chart points
        pnlHistory.push(data.session.profit);
        if (pnlHistory.length > 16) pnlHistory.shift();
        drawChart();

        // Render deals
        if (data.session.deals && data.session.deals.length > 0) {
          elDealsList.innerHTML = data.session.deals.map(d => `
            <div class="deal-item">
              <div class="deal-pair"><span class="deal-dot green"></span>${d.pair} (${d.side})</div>
              <div class="deal-pnl green">+$${d.pnl_amount.toFixed(2)} (+${d.pnl_percent}%)</div>
            </div>
          `).join('');
        }
      } else {
        isTrading = false;
        activeSession = null;
        targetSpeed = 0;
        elModeBadge.textContent = "⚪️ Ожидание старта";
        elModeBadge.classList.remove("active-mode");

        elCurrentProfit.textContent = "+0.00 USDT";
        elPnlPercent.textContent = "+0.00%";

        elActionBtn.classList.remove("stop-mode");
        elActionBtnText.textContent = "⚡ НАЧАТЬ РАЗГОН";
      }
    } catch (err) {
      console.warn("Sync error:", err);
    }
  }

  // Periodic polling every 3s
  setInterval(syncStatus, 3000);
  syncStatus();

  // Mode Selection logic
  document.querySelectorAll(".mode-item").forEach(item => {
    item.addEventListener("click", () => {
      document.querySelectorAll(".mode-item").forEach(m => m.classList.remove("active"));
      item.classList.add("active");
      selectedMode = item.dataset.mode;
      triggerHaptic("light");
    });
  });

  // Action Button (Start / Stop)
  elActionBtn.addEventListener("click", () => {
    triggerHaptic("heavy");
    if (isTrading) {
      // Prompt stop confirmation
      if (confirm("Остановить торговлю и зафиксировать прибыль на баланс?")) {
        stopTrading();
      }
    } else {
      modeModal.classList.add("open");
    }
  });

  closeModeModal.addEventListener("click", () => modeModal.classList.remove("open"));

  confirmLaunchBtn.addEventListener("click", async () => {
    const amount = parseFloat(tradeAmountInput.value);
    if (!amount || amount < 40) {
      alert("Минимальная сумма входа — 40 USDT.");
      return;
    }

    triggerHaptic("heavy");
    confirmLaunchBtn.textContent = "ЗАПУСК...";
    try {
      const res = await fetch("/api/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, mode: selectedMode, amount })
      });
      const data = await res.json();
      if (data.ok) {
        modeModal.classList.remove("open");
        triggerHaptic("success");
        syncStatus();
      } else {
        alert(data.error || "Ошибка запуска. Проверьте свободный баланс.");
      }
    } catch (e) {
      alert("Сетевая ошибка при запуске");
    } finally {
      confirmLaunchBtn.textContent = "🚀 ПОДТВЕРДИТЬ И ЗАПУСТИТЬ";
    }
  });

  async function stopTrading() {
    try {
      const res = await fetch("/api/stop", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId })
      });
      const data = await res.json();
      if (data.ok) {
        triggerHaptic("success");
        alert(`🏁 Торговля остановлена!\nЗафиксировано прибыли: +${data.result.net_profit.toFixed(2)} USDT.\nВсего возвращено на баланс: ${data.result.total_returned.toFixed(2)} USDT.`);
        syncStatus();
      } else {
        alert(data.error || "Не удалось остановить сессию");
      }
    } catch (e) {
      alert("Сетевая ошибка при остановке");
    }
  }

  // Modals for Deposit & Withdraw
  depositBtn.addEventListener("click", async () => {
    triggerHaptic("light");
    depositModal.classList.add("open");
    try {
      const res = await fetch(`/api/deposit-info?user_id=${userId}`);
      const data = await res.json();
      walletInput.value = data.address;
      depQrImage.src = `/api/qr?text=${encodeURIComponent(data.address)}`;
    } catch (e) {}
  });

  closeDepositModal.addEventListener("click", () => depositModal.classList.remove("open"));

  copyWalletBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(walletInput.value);
    copyWalletBtn.textContent = "Скопировано!";
    triggerHaptic("success");
    setTimeout(() => copyWalletBtn.textContent = "Копировать", 2000);
  });

  withdrawBtn.addEventListener("click", () => {
    triggerHaptic("light");
    alert("Для вывода средств перейдите в чат бота и нажмите кнопку «📤 Вывод средств».");
  });

  // Initial dummy chart render
  drawChart();
})();
