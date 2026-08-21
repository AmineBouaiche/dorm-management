import { ApiError, listAvailableRooms, listRooms } from "../api/client.js";
import { requireAuthentication } from "../auth/guards.js";
import { renderPrimaryNavigation } from "../components/navigation.js";

const page = document.querySelector("[data-room-page]");
const form = document.querySelector("[data-room-search]");
const results = document.querySelector("[data-room-results]");
const count = document.querySelector("[data-result-count]");
const note = document.querySelector("[data-availability-note]");
const empty = document.querySelector("[data-empty-state]");
const errorState = document.querySelector("[data-error-state]");
const errorText = document.querySelector("[data-error-text]");
const buildingFilter = document.querySelector("[data-building-filter]");
const searchError = document.querySelector("[data-search-error]");
let rooms = [];

const user = await requireAuthentication({ role: "student" });
if (user && page) {
  renderPrimaryNavigation({ currentPath: "/rooms", role: "student" });
  page.hidden = false;
  await loadInitial();
}

function money(value) { return new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(Number(value)); }
function title(value) { return value ? value.charAt(0).toUpperCase() + value.slice(1) : ""; }
function imageFor(room) { return room.building.image_url || "/static/assets/residences/north-hall.svg"; }
function queryDates() { const data = new FormData(form); return { start: String(data.get("start_date") || ""), end: String(data.get("end_date") || "") }; }

function populateBuildings(items) {
  const current = buildingFilter.value;
  const buildings = [...new Map(items.map((room) => [room.building.id, room.building])).values()].sort((a,b) => a.name.localeCompare(b.name));
  buildingFilter.innerHTML = '<option value="">Any residence</option>' + buildings.map((building) => `<option value="${building.id}">${building.name}</option>`).join("");
  buildingFilter.value = current;
}

function filterRooms(items) {
  const data = new FormData(form);
  const type = String(data.get("room_type") || "");
  const building = String(data.get("building_id") || "");
  return items.filter((room) => (!type || room.room_type === type) && (!building || String(room.building_id) === building));
}

function roomCard(room) {
  const { start, end } = queryDates();
  const params = new URLSearchParams();
  if (start && end) { params.set("start", start); params.set("end", end); }
  const href = `/rooms/${room.id}${params.size ? `?${params}` : ""}`;
  return `<article class="card room-card"><img class="room-card__image" src="${imageFor(room)}" alt="Representative view of ${room.building.name}"/><div class="card__body"><p class="card__eyebrow">${room.building.name}</p><h2 class="room-card__title">Room ${room.room_number}</h2><div class="room-card__meta"><span>${title(room.room_type)}</span><span class="room-card__price">${money(room.weekly_rate)} / week</span></div><div class="room-card__action"><a class="text-link" href="${href}">View room</a></div></div></article>`;
}

function render(items, dated = false) {
  const filtered = filterRooms(items);
  results.innerHTML = filtered.map(roomCard).join("");
  count.textContent = `${filtered.length} ${filtered.length === 1 ? "room" : "rooms"}${dated ? " available" : ""}`;
  note.textContent = dated ? "Availability is confirmed for the selected dates." : "Choose dates and search to confirm availability.";
  empty.hidden = filtered.length > 0;
  errorState.hidden = true;
}

async function loadInitial() {
  try {
    rooms = await listRooms();
    populateBuildings(rooms);
    render(rooms, false);
  } catch (error) { showError(error); }
}

function showError(error) {
  results.innerHTML = ""; count.textContent = "Rooms unavailable"; empty.hidden = true; errorState.hidden = false;
  errorText.textContent = error instanceof ApiError ? error.message : "Try again.";
}

form?.addEventListener("submit", async (event) => {
  event.preventDefault(); searchError.hidden = true;
  const { start, end } = queryDates();
  if (!start || !end) { searchError.textContent = "Choose both arrival and departure dates."; searchError.hidden = false; return; }
  if (start >= end) { searchError.textContent = "Departure must be after arrival."; searchError.hidden = false; return; }
  const button = form.querySelector("[data-search-button]"); button.disabled = true; button.textContent = "Searching...";
  try { rooms = await listAvailableRooms(start, end); populateBuildings(rooms); render(rooms, true); }
  catch (error) { showError(error); }
  finally { button.disabled = false; button.textContent = "Search"; }
});

form?.querySelectorAll('[name="room_type"], [name="building_id"]').forEach((control) => control.addEventListener("change", () => render(rooms, Boolean(queryDates().start && queryDates().end))));
document.querySelector("[data-retry]")?.addEventListener("click", loadInitial);
