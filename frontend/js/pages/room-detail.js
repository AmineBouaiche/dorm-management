import { ApiError, getRoom, listAvailableRooms } from "../api/client.js";
import { requireAuthentication } from "../auth/guards.js";
import { renderPrimaryNavigation } from "../components/navigation.js";

const page = document.querySelector("[data-room-detail-page]");
const errorBox = document.querySelector("[data-room-detail-error]");
const params = new URLSearchParams(window.location.search);
const roomId = window.location.pathname.split("/").filter(Boolean).at(-1);
const start = params.get("start"); const end = params.get("end");
const user = await requireAuthentication({ role: "student" });
if (user) { renderPrimaryNavigation({ currentPath: "/rooms", role: "student" }); await loadRoom(); }

function money(value) { return new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(Number(value)); }
function title(value) { return value.charAt(0).toUpperCase() + value.slice(1); }
function humanDate(value) { return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`)); }
function weeksBetween(a,b) { return Math.ceil((Date.parse(`${b}T00:00:00Z`) - Date.parse(`${a}T00:00:00Z`)) / 86400000 / 7); }

async function loadRoom() {
  try {
    const room = await getRoom(roomId);
    let available = null;
    if (start && end && start < end) {
      const availableRooms = await listAvailableRooms(start, end);
      available = availableRooms.some((candidate) => candidate.id === room.id);
    }
    render(room, available);
  } catch (error) {
    errorBox.hidden = false;
    document.querySelector("[data-detail-error-text]").textContent = error instanceof ApiError ? error.message : "Try again.";
  }
}

function render(room, available) {
  const image = room.building.image_url || "/static/assets/residences/north-hall.svg";
  document.querySelector("[data-breadcrumb-residence]").textContent = room.building.name;
  document.querySelector("[data-breadcrumb-room]").textContent = room.room_number;
  document.querySelector("[data-building-name]").textContent = room.building.name;
  document.querySelector("[data-room-name]").textContent = `Room ${room.room_number}`;
  document.querySelector("[data-building-image]").src = image;
  document.querySelector("[data-building-image]").alt = `Representative view of ${room.building.name}`;
  document.querySelector("[data-room-type]").textContent = `${title(room.room_type)} room`;
  document.querySelector("[data-capacity]").textContent = String(room.capacity);
  document.querySelector("[data-residence]").textContent = room.building.name;
  document.querySelector("[data-address]").textContent = room.building.address;
  document.querySelector("[data-weekly-rate]").textContent = `${money(room.weekly_rate)} per week`;

  const summary = document.querySelector("[data-stay-summary]"); const action = document.querySelector("[data-book-action]");
  if (start && end && start < end) {
    const weeks = weeksBetween(start,end); const total = Number(room.weekly_rate) * weeks;
    summary.innerHTML = `<dl class="detail-list"><dt>Arrival</dt><dd>${humanDate(start)}</dd><dt>Departure</dt><dd>${humanDate(end)}</dd><dt>Weekly rate</dt><dd>${money(room.weekly_rate)}</dd><dt>Estimated total</dt><dd>${money(total)}</dd></dl>${available === false ? '<div class="message message--error"><strong>This room is no longer available for the selected dates.</strong></div>' : '<div class="status status--success">Available for these dates</div>'}`;
    if (available) {
      const next = new URLSearchParams({ room_id: room.id, start, end }); action.href = `/booking/confirm?${next}`; action.textContent = "Book this room"; action.classList.add("button--primary"); action.classList.remove("button--secondary");
    } else { action.href = `/rooms?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`; action.textContent = "Find another room"; }
  }
  page.hidden = false;
}
