"use strict";

const controlsView = window.location.pathname === "/controls";
const $ = (id) => document.getElementById(id);
const labels = { available: "Seats available", limited: "Limited availability", none: "No free seats", unknown: "Availability incomplete" };
let snapshot = null;
let online = false;
let busy = false;
let requestVersion = 0;

function text(id, value) {
  if ($(id).textContent !== value) $(id).textContent = value;
}

function buildCars() {
  for (const car of ["A", "B", "C"]) {
    const article = document.createElement("article");
    article.id = `car-${car}`;
    article.className = "car unknown";
    article.setAttribute("aria-labelledby", `car-title-${car}`);
    article.innerHTML = `
      <div class="car-header"><h3 id="car-title-${car}">Car ${car}</h3><span class="zone-pill">ZONE ${car}</span></div>
      <div class="seat-count"><strong id="count-${car}">—</strong><span id="count-label-${car}">/ 3 free seats</span></div>
      <div class="availability"><i class="dot"></i><span id="status-${car}">Waiting for data</span></div>
      <div class="seat-row" id="seats-${car}"></div>
      <p class="car-footnote" id="note-${car}">Waiting for data</p>`;
    $("cars").append(article);
    for (let n = 1; n <= 3; n++) {
      const id = `${car}${n}`;
      const element = document.createElement(controlsView ? "button" : "div");
      element.id = `seat-${id}`;
      element.className = "seat";
      element.dataset.state = "UNKNOWN";
      if (controlsView) {
        element.type = "button";
        element.disabled = true;
        element.addEventListener("click", () => {
          const seat = snapshot?.cars.flatMap((c) => c.seats).find((s) => s.id === id);
          if (!online || busy || !seat?.editable) return;
          mutate(`/api/seats/${id}`, { state: seat.state === "EMPTY" ? "OCCUPIED" : "EMPTY" });
        });
      }
      element.innerHTML = `<svg aria-hidden="true"><use href="#seat-icon"></use></svg>
        <span class="seat-name">${id}</span><span class="seat-state" id="state-${id}">Unknown</span>
        <span class="seat-source" id="source-${id}">—</span>`;
      $(`seats-${car}`).append(element);
    }
  }
}

function refreshButtons() {
  if (!controlsView) return;
  document.querySelectorAll("#controls button").forEach((button) => { button.disabled = busy || !online; });
  for (const seat of snapshot?.cars.flatMap((c) => c.seats) || []) {
    $(`seat-${seat.id}`).disabled = busy || !online || !seat.editable;
  }
}

function render(data) {
  snapshot = data;
  online = true;
  $("offline").hidden = true;
  $("hardware-warning").hidden = !data.warnings.length;
  text("hardware-warning", data.warnings.length ? "Sensor warning — verify the hardware before relying on readings: " + data.warnings.join(" · ") : "");
  text("total-free", String(data.free));
  text("total-detail", data.unknown ? `9 seats · ${data.unknown} unknown` : "Across 3 cars · 9 seats");
  text("guidance-text", data.message);
  text("mode-label", data.mode === "hybrid" ? "Hybrid mode" : "Simulation mode");
  text("source-summary", data.mode === "hybrid" ? "HYBRID DEMO · 2 sensor seats + 7 simulated seats" : "SOFTWARE DEMO · All 9 seats simulated");
  const connectionLabels = { simulation: "Simulation · no hardware needed", connecting: "Opening serial port…",
    disconnected: "ESP32 disconnected · retrying", waiting: "USB open · waiting for fresh seat data",
    calibrating: "Calibrating · keep real seats empty", live: `ESP32 live · ${data.connection.port}` };
  text("connection-text", connectionLabels[data.connection.status] || "Waiting for data");
  $("connection-dot").className = `dot ${["live", "simulation"].includes(data.connection.status) ? "available" : "unknown"}`;
  for (const car of data.cars) {
    $(`car-${car.id}`).className = `car ${car.status}`;
    text(`count-${car.id}`, String(car.free));
    text(`count-label-${car.id}`, car.unknown ? "/ 3 confirmed free" : "/ 3 free seats");
    text(`status-${car.id}`, car.unknown ? `${car.unknown} seat unknown · ${car.free} confirmed free` : labels[car.status]);
    const real = car.seats.filter((s) => s.source === "sensor").length;
    text(`note-${car.id}`, real ? `${real} sensor seat · ${3 - real} simulated` : "3 simulated seats");
    for (const seat of car.seats) {
      const element = $(`seat-${seat.id}`);
      const state = { EMPTY: "Free", OCCUPIED: "Occupied", UNKNOWN: "Unknown" }[seat.state];
      const source = seat.source === "sensor" ? "Sensor · locked" : "Simulated";
      element.dataset.state = seat.state;
      text(`state-${seat.id}`, state);
      text(`source-${seat.id}`, controlsView ? source : seat.source === "sensor" ? "Sensor" : "Simulated");
      element.setAttribute("aria-label", `${seat.id}: ${state}. ${source}${seat.editable && controlsView ? ". Click to change." : "."}`);
      if (controlsView) element.setAttribute("aria-pressed", String(seat.state === "OCCUPIED"));
      element.title = seat.pending ? "Firmware is confirming a possible state change" : seat.reason;
    }
  }
  text("hardware-detail", data.connection.detail);
  text("last-message", data.connection.last_message || "No board messages received.");
  const sensorText = data.cars.flatMap((c) => c.seats).filter((s) => s.source === "sensor");
  for (const id of ["A1", "B1"]) {
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
  document.querySelectorAll(".diagnostic-grid > div").forEach((node) => { node.textContent = "Offline — diagnostics unavailable."; });
  $("connection-dot").className = "dot unknown";
  for (const car of ["A", "B", "C"]) {
    $(`car-${car}`).className = "car unknown";
    text(`count-${car}`, "—");
    text(`status-${car}`, "Dashboard offline");
    text(`note-${car}`, "Source data unavailable");
    for (let n = 1; n <= 3; n++) {
      $(`seat-${car}${n}`).dataset.state = "UNKNOWN";
      $(`seat-${car}${n}`).setAttribute("aria-label", `${car}${n}: unavailable; dashboard offline`);
      if (controlsView) $(`seat-${car}${n}`).setAttribute("aria-pressed", "false");
      text(`state-${car}${n}`, "Unknown");
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
    const data = await api(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
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

buildCars();
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