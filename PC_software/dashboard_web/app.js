"use strict";

const controlsView = window.location.pathname === "/controls";
const $ = (id) => document.getElementById(id);
const labels = {
  available: "Seats available",
  filling: "About to be full",
  full: "Full · no free seats",
  unknown: "Availability incomplete",
};
const stateNames = { E: "Free", O: "Occupied", U: "Unknown" };
const stateCodes = { E: "EMPTY", O: "OCCUPIED", U: "UNKNOWN" };
let snapshot = null;
let online = false;
let busy = false;
let requestVersion = 0;
// Last states string drawn per car, so only changed seats are repainted.
let drawn = {};
let cars = [];
let seatsPerCar = 0;
let realSeats = [];

function text(id, value) {
  if ($(id).textContent !== value) $(id).textContent = value;
}

// The seat map is only built in the controls view: 1296 elements are too much
// detail for a platform display, which shows per-car availability instead.
function buildCars(carIds, perCar, sensorSeats) {
  cars = carIds;
  seatsPerCar = perCar;
  realSeats = sensorSeats;
  drawn = {};
  $("cars").replaceChildren();
  $("platform-track").replaceChildren();
  for (const car of carIds) {
    const article = document.createElement("article");
    article.id = `car-${car}`;
    article.className = "car unknown";
    article.setAttribute("aria-labelledby", `car-title-${car}`);
    article.innerHTML = `
      <div class="car-header"><h3 id="car-title-${car}">Car ${car}</h3><span class="rank-pill" id="rank-${car}"></span><span class="zone-pill">ZONE ${car}</span></div>
      <div class="seat-count"><strong id="count-${car}">—</strong><span id="count-label-${car}">/ ${perCar} free seats</span></div>
      <div class="availability"><i class="dot"></i><span id="status-${car}">Waiting for data</span></div>
      <div class="occupancy"><div class="occupancy-bar"><i id="bar-${car}"></i></div><span id="pct-${car}">—</span></div>
      ${controlsView ? `<div class="seat-grid" id="seats-${car}" role="group" aria-label="Seats in car ${car}"></div>` : ""}
      <p class="car-footnote" id="note-${car}">Waiting for data</p>`;
    $("cars").append(article);

    const zone = document.createElement("div");
    zone.innerHTML = `<span>ZONE</span><strong>${car}</strong><small id="zone-note-${car}">Car ${car}</small>`;
    zone.id = `zone-${car}`;
    $("platform-track").append(zone);

    if (!controlsView) continue;
    const grid = $(`seats-${car}`);
    const fragment = document.createDocumentFragment();
    for (let n = 1; n <= perCar; n++) {
      const id = `${car}${n}`;
      const cell = document.createElement("button");
      cell.id = `seat-${id}`;
      cell.type = "button";
      cell.className = sensorSeats.includes(id) ? "cell sensor" : "cell";
      cell.dataset.state = "UNKNOWN";
      cell.disabled = true;
      cell.addEventListener("click", () => {
        const state = snapshot?.cars.find((c) => c.id === car)?.states[n - 1];
        if (!online || busy || state === undefined) return;
        mutate(`/api/seats/${id}`, { state: state === "E" ? "OCCUPIED" : "EMPTY" });
      });
      fragment.append(cell);
    }
    grid.append(fragment);
  }
}

// Every simulated seat is clickable; only a live sensor seat is locked, and
// only in hybrid mode. Walking 1296 cells is cheap when nothing changed, so
// this only touches them when the enabled/locked state actually differs.
let cellState = null;

function refreshButtons() {
  if (!controlsView) return;
  document.querySelectorAll("#controls button").forEach((button) => { button.disabled = busy || !online; });
  const enabled = online && !busy;
  const hybrid = snapshot?.mode === "hybrid";
  const key = `${enabled}|${hybrid}|${cars.length}|${seatsPerCar}`;
  if (key === cellState) return;
  for (const car of cars) {
    for (let n = 1; n <= seatsPerCar; n++) {
      const id = `${car}${n}`;
      const cell = $(`seat-${id}`);
      if (!cell) continue;
      const locked = hybrid && realSeats.includes(id);
      cell.disabled = !enabled || locked;
      cell.classList.toggle("locked", locked);
    }
  }
  cellState = key;
}

function paintSeats(car) {
  if (!controlsView) return;
  const previous = drawn[car.id];
  if (previous === car.states) return;
  for (let index = 0; index < car.states.length; index++) {
    const code = car.states[index];
    if (previous && previous[index] === code) continue;
    const id = `${car.id}${index + 1}`;
    const cell = $(`seat-${id}`);
    if (!cell) continue;
    cell.dataset.state = stateCodes[code];
    const sensor = realSeats.includes(id);
    cell.title = `${id}: ${stateNames[code]}${sensor ? " · physical sensor seat" : ""}`;
    cell.setAttribute("aria-label", `${id}: ${stateNames[code]}.${sensor ? " Physical sensor seat." : ""}`);
    cell.setAttribute("aria-pressed", String(code === "O"));
  }
  drawn[car.id] = car.states;
}

function render(data) {
  snapshot = data;
  online = true;
  if (cars.length !== data.cars.length || seatsPerCar !== data.seats_per_car) {
    buildCars(data.cars.map((c) => c.id), data.seats_per_car, data.real_seats);
  }
  $("offline").hidden = true;
  $("hardware-warning").hidden = !data.warnings.length;
  text("hardware-warning", data.warnings.length ? "Sensor warning — verify the hardware before relying on readings: " + data.warnings.join(" · ") : "");
  text("total-free", String(data.free));
  text("total-detail", data.unknown
    ? `${data.total} seats · ${data.unknown} unknown · ${data.occupancy_pct}% occupied`
    : `Across ${data.num_cars} cars · ${data.total} seats · ${data.occupancy_pct}% occupied`);
  text("station-number", String(data.station));
  $("boarding-badge").hidden = !data.boarding;
  $("auto-badge").hidden = !data.auto_interval;
  text("auto-badge", data.auto_interval ? `AUTO · EVERY ${data.auto_interval}s` : "");
  if (controlsView) {
    text("auto-toggle", data.auto_interval ? "Stop auto stops" : "Start auto stops");
    $("auto-toggle").className = data.auto_interval ? "primary-button" : "secondary-button";
  }
  text("guidance-text", data.message);
  text("train-subtitle", `${data.num_cars} cars · ${data.seats_per_car} seats each · ${data.total} total`);
  text("mode-label", data.mode === "hybrid" ? "Hybrid mode" : "Simulation mode");
  text("source-summary", data.mode === "hybrid"
    ? `HYBRID DEMO · ${data.real_seats.length} sensor seats + ${data.total - data.real_seats.length} simulated seats`
    : `SOFTWARE DEMO · All ${data.total} seats simulated`);
  const connectionLabels = { simulation: "Simulation · no hardware needed", connecting: "Opening serial port…",
    disconnected: "ESP32 disconnected · retrying", waiting: "USB open · waiting for fresh seat data",
    calibrating: "Calibrating · keep real seats empty", live: `ESP32 live · ${data.connection.port}` };
  text("connection-text", connectionLabels[data.connection.status] || "Waiting for data");
  $("connection-dot").className = `dot ${["live", "simulation"].includes(data.connection.status) ? "available" : "unknown"}`;

  const recommended = data.recommended || [];
  for (const car of data.cars) {
    const best = recommended.includes(car.id);
    const rank = recommended.indexOf(car.id) + 1;
    $(`car-${car.id}`).className = `car ${car.status}${best ? " best" : ""}`;
    text(`count-${car.id}`, String(car.free));
    text(`count-label-${car.id}`, car.unknown ? `/ ${car.total} confirmed free` : `/ ${car.total} free seats`);
    text(`status-${car.id}`, car.unknown
      ? `${car.unknown} seat${car.unknown === 1 ? "" : "s"} unknown · ${car.free} confirmed free`
      : car.status === "filling" ? `${labels.filling} · only ${car.free} left`
      : labels[car.status]);
    text(`rank-${car.id}`, best ? (rank === 1 ? "BEST CHOICE" : `GOOD CHOICE #${rank}`) : "");
    text(`pct-${car.id}`, `${car.occupancy_pct}% full`);
    $(`bar-${car.id}`).style.width = `${car.occupancy_pct}%`;
    const real = car.seats.filter((s) => s.source === "sensor").length;
    text(`note-${car.id}`, real
      ? `${real} sensor seat${real === 1 ? "" : "s"} · ${car.total - real} simulated · ${car.occupied} occupied`
      : `${car.total} simulated seats · ${car.occupied} occupied`);
    text(`zone-note-${car.id}`, best ? `Board Car ${car.id} here · ${car.free} free`
      : car.status === "full" ? `Car ${car.id} · full` : `Car ${car.id} · ${car.free} free`);
    $(`zone-${car.id}`).className = best ? "best-zone" : "";
    paintSeats(car);
  }

  text("hardware-detail", data.connection.detail);
  text("last-message", data.connection.last_message || "No board messages received.");
  const sensorText = data.cars.flatMap((c) => c.seats).filter((s) => s.source === "sensor");
  for (const id of data.real_seats) {
    let node = $(`diagnostic-${id}`);
    if (!node) {
      node = document.createElement("div");
      node.id = `diagnostic-${id}`;
      $("sensor-details").append(node);
    }
    const seat = sensorText.find((s) => s.id === id);
    node.textContent = seat ? `${id} · sensor ${seat.sensor_id} · ${seat.state} · ${seat.reason}. ` +
      `Last distance: ${seat.distance_cm ?? "—"} cm; noise: ${seat.noise_mv ?? "—"} mV; ` +
      `last reading: ${seat.age_s === null ? "never" : seat.age_s + " s ago"}${seat.pending ? "; confirming change" : ""}.` : `${id} is simulated in this mode.`;
  }
  refreshButtons();
}

function disconnected() {
  online = false;
  $("offline").hidden = false;
  text("total-free", "—");
  text("total-detail", "Availability unavailable");
  text("guidance-text", "Dashboard offline — do not rely on previous counts");
  text("connection-text", "Dashboard server unavailable");
  text("source-summary", "OFFLINE · Previous data is unavailable");
  text("hardware-detail", "Dashboard offline. Sensor diagnostics unavailable.");
  text("last-message", "Dashboard offline — no current board message.");
  text("station-number", "—");
  $("boarding-badge").hidden = true;
  $("auto-badge").hidden = true;
  document.querySelectorAll(".diagnostic-grid > div").forEach((node) => { node.textContent = "Offline — diagnostics unavailable."; });
  $("connection-dot").className = "dot unknown";
  drawn = {};
  for (const car of cars) {
    $(`car-${car}`).className = "car unknown";
    text(`count-${car}`, "—");
    text(`status-${car}`, "Dashboard offline");
    text(`rank-${car}`, "");
    text(`note-${car}`, "Source data unavailable");
    text(`pct-${car}`, "—");
    $(`bar-${car}`).style.width = "0%";
    text(`zone-note-${car}`, "Unavailable");
    $(`zone-${car}`).className = "";
    if (!controlsView) continue;
    for (let n = 1; n <= seatsPerCar; n++) {
      const cell = $(`seat-${car}${n}`);
      cell.dataset.state = "UNKNOWN";
      cell.setAttribute("aria-label", `${car}${n}: unavailable; dashboard offline`);
      cell.setAttribute("aria-pressed", "false");
    }
  }
  refreshButtons();
}

async function api(url, options = {}) {
  const abort = new AbortController();
  const timer = setTimeout(() => abort.abort(), 2500);
  try {
    const response = await fetch(url, { ...options, signal: abort.signal, cache: "no-store" });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
    return data;
  } finally { clearTimeout(timer); }
}

async function mutate(url, body) {
  if (busy) return;
  busy = true;
  const version = ++requestVersion;
  $("error").hidden = true;
  refreshButtons();
  try {
    const data = await api(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });
    if (version === requestVersion) render(data);
  } catch (error) {
    text("error", error.message);
    $("error").hidden = false;
  } finally {
    busy = false;
    refreshButtons();
  }
}

async function poll() {
  if (!busy) {
    const version = ++requestVersion;
    try {
      const data = await api("/api/state");
      if (version === requestVersion) render(data);
    } catch {
      if (version === requestVersion) disconnected();
    }
  }
  setTimeout(poll, 500);
}

async function refreshPorts() {
  try {
    const data = await api("/api/ports");
    $("serial-ports").replaceChildren();
    for (const port of data.ports) {
      const option = document.createElement("option");
      option.value = port.device;
      option.label = port.description;
      $("serial-ports").append(option);
    }
    text("port-help", data.ports.length ? "Detected: " + data.ports.map((p) => `${p.device} (${p.description})`).join(", ") : "No serial ports detected. Simulation mode works without hardware.");
  } catch { text("port-help", "Unable to list ports. Enter the board port manually when the server is available."); }
}

$(controlsView ? "controls-link" : "passenger-link").setAttribute("aria-current", "page");
$("controls").hidden = !controlsView;
if (controlsView) {
  document.title = "SmartRail · Demo controls";
  text("eyebrow", "DEMO CONTROL ROOM");
  text("title", "Set the scene.");
  text("subtitle", "Control simulated seats here. Physical seats follow the ESP32.");
  $("simulation").addEventListener("click", () => mutate("/api/mode", { mode: "simulation", port: "" }));
  $("hybrid").addEventListener("click", () => mutate("/api/mode", { mode: "hybrid", port: $("serial-port").value.trim() }));
  $("refresh-ports").addEventListener("click", refreshPorts);
  $("next-stop").addEventListener("click", () => mutate("/api/next_stop", {}));
  $("auto-toggle").addEventListener("click", () => mutate("/api/auto", {
    interval: snapshot?.auto_interval ? "0" : $("auto-interval").value,
  }));
  $("auto-interval").addEventListener("change", () => {
    if (snapshot?.auto_interval) mutate("/api/auto", { interval: $("auto-interval").value });
  });
  document.querySelectorAll("[data-preset]").forEach((button) => {
    button.addEventListener("click", () => mutate("/api/preset", { name: button.dataset.preset }));
  });
  refreshPorts();
}
$("fullscreen").addEventListener("click", async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await document.documentElement.requestFullscreen();
  } catch {
    text("error", "Fullscreen is unavailable here. Open this page in a regular browser and use F11.");
    $("error").hidden = false;
  }
});
document.addEventListener("fullscreenchange", () => text("fullscreen", document.fullscreenElement ? "⛶ Exit full screen" : "⛶ Full screen"));
poll();
