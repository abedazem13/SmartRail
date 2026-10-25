"use strict";

/* Platform entrance screen.
 *
 * Renders the view model from /api/platform exactly as it arrives. The server
 * has already decided what each carriage may say and in what order, so this
 * file sorts nothing, ranks nothing and highlights no carriage as a choice.
 * Everything it adds is positional: which zone this particular screen stands
 * at, read from the URL (?zone=F), which is the screen's installed location
 * and has nothing to do with seat counts.
 */

const $ = (id) => document.getElementById(id);
const POLL_MS = 1000;

/* Builds an element from text rather than markup: nothing from the server is
 * ever parsed as HTML. */
function element(tag, className, text, child) {
  const node = document.createElement(tag);
  node.className = className;
  node.append(text);
  if (child) node.append(child);
  return node;
}

const here = new URLSearchParams(window.location.search).get("zone");
let built = "";            // carriage ids currently drawn, to avoid rebuilding
let drawn = "";            // last payload drawn, to avoid repainting
let version = 0;

function buildTrain(cars) {
  const train = $("train");
  const zones = $("zones");
  train.replaceChildren();
  zones.replaceChildren();

  for (const car of cars) {
    const item = document.createElement("li");
    item.className = "car unknown";
    item.id = `car-${car.id}`;
    // Position is the carriage's place in the train, not a rank. It is part of
    // the accessible name so a screen reader hears the map, not a list order.
    item.innerHTML = `
      <p class="car-id">CAR ${car.id}</p>
      <p class="car-state" id="state-${car.id}"></p>
      <p class="car-detail" id="detail-${car.id}">Waiting for data</p>`;
    train.append(item);

    const zone = document.createElement("li");
    zone.className = "zone";
    zone.id = `zone-${car.id}`;
    zone.innerHTML = `<strong>${car.zone}</strong>`;
    zones.append(zone);
  }

  if (here) {
    const marker = $(`zone-${here}`) || [...zones.children]
      .find((node) => node.textContent.trim() === here);
    if (marker) {
      marker.classList.add("is-here");
      $("here-text").textContent = "You are here";
      // Moved under its own zone letter, so the marker points at a place on
      // the platform rather than at the middle of the picture.
      marker.append($("here"));
      $("here").hidden = false;
      $("installed").textContent = `Platform screen at Zone ${here}`;
    }
  }
}

function render(view) {
  const ids = view.cars.map((car) => car.id).join("");
  if (ids !== built) {
    buildTrain(view.cars);
    built = ids;
    drawn = "";
  }

  const fingerprint = JSON.stringify(view);
  if (fingerprint === drawn) return;
  drawn = fingerprint;

  $("banner").textContent = view.banner;
  $("banner").classList.toggle("is-spread", view.mode === "spread");
  $("banner").classList.remove("is-stale");
  $("train").classList.toggle("is-spread", view.mode === "spread");
  $("offline").hidden = true;

  for (const car of view.cars) {
    const node = $(`car-${car.id}`);
    node.className = `car ${car.state}`;
    // A count is set as numerals with a small unit; a phrase is set as words.
    // Both come from the server: this picks the typesetting, not the wording.
    $(`state-${car.id}`).replaceChildren(car.figure
      ? element("span", "car-figure", car.figure,
                element("span", "car-unit", car.unit))
      : element("span", "car-phrase", car.headline));
    $(`detail-${car.id}`).textContent = car.detail;
    $(`detail-${car.id}`).hidden = !car.detail;
    node.setAttribute("aria-label",
      `Car ${car.id}, zone ${car.zone}, position ${car.position + 1} from the ` +
      `front. ${car.headline}.${car.detail ? ` ${car.detail}.` : ""}`);
  }

  $("free-total").textContent = view.totals.confirmed_free;
  $("unknown-total").textContent = view.totals.unknown;
  $("unknown-note").hidden = view.totals.unknown === 0;
}

function stale() {
  $("offline").hidden = false;
  $("banner").classList.add("is-stale");
  drawn = "";
}

async function poll() {
  const mine = ++version;
  const abort = new AbortController();
  const timer = setTimeout(() => abort.abort(), 2500);
  try {
    const response = await fetch("/api/platform", {
      signal: abort.signal, cache: "no-store",
    });
    const view = await response.json();
    if (!response.ok) throw new Error(view.error || "Request failed");
    if (mine === version) render(view);
  } catch {
    if (mine === version) stale();
  } finally {
    clearTimeout(timer);
    setTimeout(poll, POLL_MS);
  }
}

poll();
