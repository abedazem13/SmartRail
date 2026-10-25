"use strict";

/* The phone app.
 *
 * Three things this file deliberately does not do:
 *
 *   * It never fetches the whole train's seat counts. The only state it holds
 *     is this passenger's own assignment. There is nothing here to build a
 *     comparison from, by accident or by a later well-meaning change.
 *   * It does not choose the carriage. The server's dispatcher does, because
 *     the choice depends on what every other passenger has already been told,
 *     and a phone cannot know that.
 *   * It does not ask again on a timer. A new request means a new passenger as
 *     far as the dispatcher is concerned, so the app keeps its ticket and
 *     re-sends it; the same ticket always returns the same carriage.
 */

const $ = (id) => document.getElementById(id);
const TICKET_KEY = "smartrail.ticket";
const ZONE_KEY = "smartrail.zone";

let zones = [];
let position = null;
let assignment = null;
let busy = false;
let tick = null;

/* The ticket is what makes a refresh a refresh and not a second passenger.
 * It is a random id held on the phone; the server stores no identity. */
function ticket() {
  let value = null;
  try { value = window.localStorage.getItem(TICKET_KEY); } catch { /* private mode */ }
  if (!value) {
    value = (window.crypto?.randomUUID?.() ||
             `t${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`)
            .replace(/-/g, "").slice(0, 32);
    try { window.localStorage.setItem(TICKET_KEY, value); } catch { /* ignore */ }
  }
  return value;
}

function newTicket() {
  try { window.localStorage.removeItem(TICKET_KEY); } catch { /* ignore */ }
  return ticket();
}

function remember(zone) {
  try { window.localStorage.setItem(ZONE_KEY, zone); } catch { /* ignore */ }
}

function recall() {
  try { return window.localStorage.getItem(ZONE_KEY); } catch { return null; }
}

/* ----------------------------------------------------------------- step 1 */

function buildPicker(list) {
  zones = list;
  const picker = $("zone-picker");
  picker.replaceChildren();
  for (const zone of list) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "zone-button";
    button.setAttribute("aria-pressed", "false");
    button.dataset.zone = zone.id;
    button.innerHTML = `<strong>${zone.zone}</strong><span>ZONE</span>`;
    button.addEventListener("click", () => select(zone.id));
    picker.append(button);
  }
}

function select(id) {
  if (busy) return;
  position = id;
  remember(id);
  for (const button of $("zone-picker").children) {
    button.setAttribute("aria-pressed", String(button.dataset.zone === id));
  }
  assign(ticket());
}

/* ----------------------------------------------------------------- step 2 */

function show(data) {
  assignment = data;
  $("result-zone").textContent = data.zone;
  $("result-car").textContent = `Car ${data.car} stops here`;
  $("result-walk").textContent = data.walk;

  const spreading = data.reason.startsWith("no confirmed seat");
  $("result-why").classList.toggle("is-spreading", spreading);
  $("result-why").textContent = spreading
    ? "No carriage near you can confirm a free seat right now. This door was "
      + "picked to keep you away from the busiest one."
    : `${data.confirmed_free} seat${data.confirmed_free === 1 ? "" : "s"} `
      + "confirmed free in this carriage when you asked.";

  $("ask").hidden = true;
  $("result").hidden = false;
  startCountdown(data.seconds_left);
}

/* The hold is honest about itself: the carriage was chosen for the crowd that
 * was waiting when the passenger asked, and that crowd changes. */
function startCountdown(seconds) {
  clearInterval(tick);
  let left = seconds;
  const paint = () => {
    const expired = left <= 0;
    $("countdown").classList.toggle("is-expired", expired);
    $("countdown").textContent = expired
      ? "This suggestion has expired. Ask again for an up-to-date carriage."
      : `Held for you for ${Math.floor(left / 60)}:`
        + `${String(left % 60).padStart(2, "0")}`;
    if (expired) clearInterval(tick);
    left -= 1;
  };
  paint();
  tick = setInterval(paint, 1000);
}

function reset() {
  clearInterval(tick);
  assignment = null;
  $("result").hidden = true;
  $("ask").hidden = false;
  $("error").hidden = true;
}

/* ------------------------------------------------------------------- api */

async function api(url, body) {
  const abort = new AbortController();
  const timer = setTimeout(() => abort.abort(), 3000);
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: abort.signal,
      cache: "no-store",
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
    return data;
  } finally { clearTimeout(timer); }
}

function fail(message) {
  $("error").textContent = message;
  $("error").hidden = false;
}

async function assign(id) {
  if (busy || !position) return;
  busy = true;
  $("error").hidden = true;
  $("ask-hint").textContent = "Finding a carriage with room near you…";
  try {
    show(await api("/api/assign", { position, ticket: id }));
  } catch (error) {
    fail(`${error.message} The platform map still works: open it below.`);
  } finally {
    busy = false;
    $("ask-hint").textContent = "Choose a zone to get your carriage.";
  }
}

async function boarded() {
  if (!assignment) return;
  $("boarded").disabled = true;
  try {
    // Handing the slot back lets the dispatcher offer this carriage to the
    // next person, instead of holding it until the assignment expires.
    await api("/api/release", { ticket: assignment.ticket });
  } catch { /* the assignment expires on its own; nothing to recover */ }
  newTicket();
  reset();
  $("boarded").disabled = false;
  $("ask-hint").textContent = "Have a good journey. Choose a zone to ask again.";
}

/* --------------------------------------------------------------- startup */

/* The zone list is the only thing the app reads from the train, and it carries
 * no seat counts: just which zones exist and in what order. */
async function start() {
  try {
    const response = await fetch("/api/platform", { cache: "no-store" });
    const view = await response.json();
    if (!response.ok) throw new Error(view.error || "Request failed");
    buildPicker(view.cars.map((car) => ({ id: car.id, zone: car.zone })));
  } catch {
    fail("Cannot reach the train right now. Pull down to reload once you have "
         + "a connection.");
    return;
  }

  const last = recall();
  if (last && zones.some((zone) => zone.id === last)) {
    // Returning to the app from the same zone should not look like a cold
    // start. The ticket makes this the same request, not a second passenger.
    select(last);
  }
}

/* Changing zone is not boarding: the carriage goes back in the pool so the
 * next person asking from that zone can be sent to it. */
async function changeZone() {
  const held = assignment;
  reset();
  newTicket();
  if (held) {
    try { await api("/api/release", { ticket: held.ticket }); } catch { /* expires anyway */ }
  }
}

$("boarded").addEventListener("click", boarded);
$("again").addEventListener("click", changeZone);
start();
