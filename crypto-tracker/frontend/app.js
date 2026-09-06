const csvPath = "../data/crypto_data.csv";
let coins = [];
let history = [];
let alerts = JSON.parse(localStorage.getItem("crypto-alerts") || "[]");
const assetColors = ["#c9f269", "#77d6c5", "#f5b97d", "#a8b8ff", "#f28f9d", "#c8a5f5", "#f4df69", "#8ed1f0", "#d4b483", "#9ee493"];

const elements = {
  status: document.querySelector("#status"),
  updated: document.querySelector("#last-updated"),
  assetCount: document.querySelector("#asset-count"),
  leaderName: document.querySelector("#leader-name"),
  leaderPrice: document.querySelector("#leader-price"),
  averageChange: document.querySelector("#average-change"),
  topMover: document.querySelector("#top-mover"),
  topMoverChange: document.querySelector("#top-mover-change"),
  table: document.querySelector("#coin-table"),
  rowCount: document.querySelector("#row-count"),
  search: document.querySelector("#search-input")
  , chartCoin: document.querySelector("#chart-coin")
  , chart: document.querySelector("#price-chart")
  , chartEmpty: document.querySelector("#chart-empty")
  , alertForm: document.querySelector("#alert-form")
  , alertCoin: document.querySelector("#alert-coin")
  , alertMetric: document.querySelector("#alert-metric")
  , alertDirection: document.querySelector("#alert-direction")
  , alertThreshold: document.querySelector("#alert-threshold")
  , alertsList: document.querySelector("#alerts-list")
  , notificationButton: document.querySelector("#notification-button")
};

function parseCsv(text) {
  const rows = text.trim().split(/\r?\n/).map((line) => {
    const fields = [];
    let field = "";
    let quoted = false;
    for (const character of line) {
      if (character === '"') quoted = !quoted;
      else if (character === "," && !quoted) { fields.push(field); field = ""; }
      else field += character;
    }
    fields.push(field);
    return fields;
  });
  const headers = rows.shift();
  return rows.map((row) => Object.fromEntries(headers.map((header, index) => [header, row[index] || ""])));
}

function numberValue(value) {
  const parsed = Number.parseFloat(String(value).replace(/[^\d.-]/g, ""));
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatPrice(value) {
  return `$${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}`;
}

function formatMarketCap(value) {
  const number = Number(value);
  if (number >= 1e12) return `$${(number / 1e12).toFixed(2)}T`;
  if (number >= 1e9) return `$${(number / 1e9).toFixed(2)}B`;
  if (number >= 1e6) return `$${(number / 1e6).toFixed(2)}M`;
  return `$${number.toLocaleString()}`;
}

function colorForAsset(symbol) {
  const index = [...new Set(history.map((coin) => coin.symbol))].indexOf(symbol);
  return assetColors[Math.max(index, 0) % assetColors.length];
}

function latestCapture(rows) {
  const latestTimestamp = rows.reduce((latest, row) => row.timestamp > latest ? row.timestamp : latest, "");
  return rows.filter((row) => row.timestamp === latestTimestamp);
}

function render() {
  const query = elements.search.value.trim().toLowerCase();
  const visibleCoins = coins.filter((coin) => `${coin.name} ${coin.symbol}`.toLowerCase().includes(query));
  elements.table.innerHTML = visibleCoins.length ? visibleCoins.map((coin) => {
    const change = numberValue(coin.change_24h_percent);
    const initials = (coin.symbol || coin.name).slice(0, 3).toUpperCase();
    return `<tr><td><div class="asset-cell" style="--asset-color: ${colorForAsset(coin.symbol)}"><span class="asset-badge">${initials}</span><span>${coin.name}<small class="symbol">${coin.symbol}</small></span></div></td><td>${formatPrice(coin.price_usd)}</td><td class="${change >= 0 ? "positive" : "negative"}">${change >= 0 ? "+" : ""}${change.toFixed(2)}%</td><td>${formatMarketCap(coin.market_cap_usd)}</td><td>${coin.timestamp.slice(11) || "--"}</td></tr>`;
  }).join("") : '<tr><td colspan="5" class="empty-state">No matching assets found.</td></tr>';
  elements.rowCount.textContent = `${visibleCoins.length} visible / ${coins.length} tracked`;
}

function updateSummary() {
  const changes = coins.map((coin) => numberValue(coin.change_24h_percent));
  const leader = coins[0];
  const mover = coins.reduce((best, coin) => numberValue(coin.change_24h_percent) > numberValue(best.change_24h_percent) ? coin : best, coins[0]);
  const average = changes.reduce((sum, change) => sum + change, 0) / (changes.length || 1);
  elements.assetCount.textContent = coins.length;
  elements.leaderName.textContent = leader?.name || "--";
  elements.leaderPrice.textContent = leader ? formatPrice(leader.price_usd) : "--";
  elements.averageChange.textContent = `${average >= 0 ? "+" : ""}${average.toFixed(2)}%`;
  elements.averageChange.className = average >= 0 ? "positive" : "negative";
  elements.topMover.textContent = mover?.symbol || "--";
  elements.topMoverChange.textContent = mover ? `${numberValue(mover.change_24h_percent).toFixed(2)}% today` : "--";
  elements.updated.textContent = coins[0]?.timestamp || "--";
}

function drawChart() {
  const selectedSymbol = elements.chartCoin.value;
  const points = history.filter((coin) => coin.symbol === selectedSymbol);
  const canvas = elements.chart;
  const context = canvas.getContext("2d");
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const scale = window.devicePixelRatio || 1;
  canvas.width = width * scale;
  canvas.height = height * scale;
  context.setTransform(scale, 0, 0, scale, 0, 0);
  context.clearRect(0, 0, width, height);
  elements.chartEmpty.hidden = points.length > 1;
  if (points.length < 2) return;

  const values = points.map((point) => numberValue(point.price_usd));
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const range = maximum - minimum || 1;
  const padding = { top: 24, right: 18, bottom: 34, left: 78 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const labelFont = "11px DM Mono, monospace";
  context.font = labelFont;
  context.lineWidth = 1;
  context.textBaseline = "middle";
  for (let tick = 0; tick <= 4; tick += 1) {
    const ratio = tick / 4;
    const y = padding.top + ratio * plotHeight;
    const value = maximum - ratio * range;
    context.strokeStyle = tick === 4 ? "#b9c6bc" : "#e4e9e3";
    context.beginPath();
    context.moveTo(padding.left, y);
    context.lineTo(width - padding.right, y);
    context.stroke();
    context.fillStyle = "#718078";
    context.textAlign = "right";
    context.fillText(formatPrice(value), padding.left - 10, y);
  }
  context.textBaseline = "top";
  const labelIndexes = [...new Set([0, Math.floor((points.length - 1) / 2), points.length - 1])];
  labelIndexes.forEach((index) => {
    const x = padding.left + (index / (points.length - 1)) * plotWidth;
    context.fillStyle = "#718078";
    context.textAlign = index === 0 ? "left" : index === points.length - 1 ? "right" : "center";
    context.fillText(points[index].timestamp.slice(5, 16), x, height - padding.bottom + 12);
  });
  const coordinates = points.map((point, index) => ({
    x: padding.left + (index / (points.length - 1)) * plotWidth,
    y: padding.top + (1 - (numberValue(point.price_usd) - minimum) / range) * plotHeight
  }));
  context.beginPath();
  coordinates.forEach((point, index) => {
    index ? context.lineTo(point.x, point.y) : context.moveTo(point.x, point.y);
  });
  context.strokeStyle = "#0d6b62";
  context.lineWidth = 2.5;
  context.stroke();
  context.fillStyle = "#c9f269";
  coordinates.forEach((point) => {
    context.beginPath();
    context.arc(point.x, point.y, 3.5, 0, Math.PI * 2);
    context.fill();
    context.strokeStyle = "#0d6b62";
    context.lineWidth = 1.5;
    context.stroke();
  });
  context.fillStyle = "#17211d";
  context.textAlign = "right";
  context.textBaseline = "alphabetic";
  context.font = "500 11px DM Mono, monospace";
  context.fillText(`Latest ${formatPrice(values[values.length - 1])}`, width - padding.right, 13);
}

function updateChartOptions() {
  const symbols = [...new Map(history.map((coin) => [coin.symbol, coin])).values()];
  const current = elements.chartCoin.value;
  elements.chartCoin.innerHTML = symbols.map((coin) => `<option value="${coin.symbol}">${coin.name} (${coin.symbol})</option>`).join("");
  const preferred = symbols.find((coin) => coin.symbol === "BTC")?.symbol || symbols[0]?.symbol || "";
  elements.chartCoin.value = symbols.some((coin) => coin.symbol === current && current !== "CMC20") ? current : preferred;
  drawChart();
}

function saveAlerts() {
  localStorage.setItem("crypto-alerts", JSON.stringify(alerts));
}

function updateAlertOptions() {
  const current = elements.alertCoin.value;
  elements.alertCoin.innerHTML = [...new Map(coins.map((coin) => [coin.symbol, coin])).values()]
    .map((coin) => `<option value="${coin.symbol}">${coin.name} (${coin.symbol})</option>`).join("");
  if (current && [...elements.alertCoin.options].some((option) => option.value === current)) elements.alertCoin.value = current;
}

function formatAlert(alert) {
  const direction = alert.direction === "above" ? "rises above" : "falls below";
  const suffix = alert.metric === "change_24h" ? "%" : "";
  return `${alert.symbol} ${direction} ${alert.threshold}${suffix}`;
}

function renderAlerts() {
  elements.alertsList.innerHTML = alerts.length ? alerts.map((alert) => `<div class="alert-row ${alert.triggered ? "alert-row--triggered" : ""}"><div class="alert-description">${formatAlert(alert)}<small>${alert.triggered ? "Triggered on latest capture" : "Watching latest capture"}</small></div><div class="alert-actions"><button class="alert-toggle" data-alert-id="${alert.id}" type="button">${alert.enabled ? "Pause" : "Resume"}</button><button class="delete-alert" data-delete-id="${alert.id}" type="button">Delete</button></div></div>`).join("") : '<p class="empty-state">No custom alerts yet.</p>';
}

function checkAlerts() {
  alerts.forEach((alert) => {
    const coin = coins.find((item) => item.symbol === alert.symbol);
    if (!coin || !alert.enabled) return;
    const field = alert.metric === "price" ? "price_usd" : "change_24h_percent";
    const value = numberValue(coin[field]);
    const matched = alert.direction === "above" ? value >= alert.threshold : value <= alert.threshold;
    if (matched && !alert.triggered && "Notification" in window && Notification.permission === "granted") {
      new Notification("Crypto tracker alert", { body: `${formatAlert(alert)}. Current value: ${coin[field]}` });
    }
    alert.triggered = matched;
  });
  saveAlerts();
  renderAlerts();
}

async function loadData() {
  elements.status.textContent = "Refreshing feed";
  try {
    const response = await fetch(`${csvPath}?t=${Date.now()}`);
    if (!response.ok) throw new Error("CSV unavailable");
    const rows = parseCsv(await response.text());
    history = rows;
    coins = latestCapture(rows);
    updateSummary();
    render();
    updateChartOptions();
    updateAlertOptions();
    checkAlerts();
    elements.status.textContent = "Feed connected";
  } catch (error) {
    elements.status.textContent = "Feed unavailable";
    elements.table.innerHTML = '<tr><td colspan="5" class="empty-state">Run the scraper first, then refresh this page.</td></tr>';
  }
}

document.querySelector("#refresh-button").addEventListener("click", loadData);
elements.search.addEventListener("input", render);
elements.chartCoin.addEventListener("change", drawChart);
window.addEventListener("resize", drawChart);
elements.alertForm.addEventListener("submit", (event) => {
  event.preventDefault();
  alerts.push({ id: Date.now(), symbol: elements.alertCoin.value, metric: elements.alertMetric.value, direction: elements.alertDirection.value, threshold: Number(elements.alertThreshold.value), enabled: true, triggered: false });
  saveAlerts();
  renderAlerts();
  elements.alertThreshold.value = "";
});
elements.alertsList.addEventListener("click", (event) => {
  const toggleId = event.target.dataset.alertId;
  const deleteId = event.target.dataset.deleteId;
  if (toggleId) alerts = alerts.map((alert) => alert.id === Number(toggleId) ? { ...alert, enabled: !alert.enabled } : alert);
  if (deleteId) alerts = alerts.filter((alert) => alert.id !== Number(deleteId));
  saveAlerts();
  renderAlerts();
});
elements.notificationButton.addEventListener("click", async () => {
  if ("Notification" in window) await Notification.requestPermission();
  elements.notificationButton.textContent = Notification.permission === "granted" ? "Notifications enabled" : "Notifications blocked";
});
renderAlerts();
loadData();
setInterval(loadData, 60000);
