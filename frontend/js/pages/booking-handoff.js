import { ApiError, createBooking, getRoom, listAvailableRooms } from "../api/client.js";
import { requireAuthentication } from "../auth/guards.js";
import { renderPrimaryNavigation } from "../components/navigation.js";

const page = document.querySelector("[data-confirm-page]");
const content = document.querySelector("[data-confirm-content]");
const errorBox = document.querySelector("[data-confirm-error]");
const errorText = document.querySelector("[data-confirm-error-text]");
const roomLink = document.querySelector("[data-room-link]");
const params = new URLSearchParams(window.location.search);
const roomId = params.get("room_id");
const start = params.get("start");
const end = params.get("end");

const user = await requireAuthentication({ role: "student" });
if (user && page) {
  renderPrimaryNavigation({ currentPath: "/rooms", role: "student" });
  page.hidden = false;
  await initialise();
}

function money(value) {
  return new Intl.NumberFormat("en-GB", {
    style: "currency", currency: "GBP", minimumFractionDigits: 0, maximumFractionDigits: 2,
  }).format(Number(value));
}

function humanDate(value) {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric", month: "long", year: "numeric", timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));
}

function weeksBetween(a, b) {
  const days = (Date.parse(`${b}T00:00:00Z`) - Date.parse(`${a}T00:00:00Z`)) / 86400000;
  return Math.ceil(days / 7);
}

function showError(message) {
  errorText.textContent = message;
  errorBox.hidden = false;
}

async function initialise() {
  if (!roomId || !start || !end || start >= end) {
    content.innerHTML = '<div class="empty-state"><h2>Booking details are incomplete</h2><p>Return to room search and select valid stay dates.</p><a class="button button--primary" href="/rooms">Browse rooms</a></div>';
    return;
  }

  const backQuery = new URLSearchParams({ start, end });
  roomLink.href = `/rooms/${roomId}?${backQuery}`;

  try {
    const [room, availableRooms] = await Promise.all([
      getRoom(roomId),
      listAvailableRooms(start, end),
    ]);
    const available = availableRooms.some((candidate) => candidate.id === room.id);
    renderSummary(room, available);
  } catch (error) {
    content.innerHTML = "";
    showError(error instanceof ApiError ? error.message : "Try again.");
  }
}

function renderSummary(room, available) {
  const weeks = weeksBetween(start, end);
  const estimatedTotal = Number(room.weekly_rate) * weeks;
  const canSubmit = available;

  content.innerHTML = `
    <section class="confirmation-section">
      <h2>Accommodation</h2>
      <dl class="detail-list">
        <dt>Residence</dt><dd>${room.building.name}</dd>
        <dt>Room</dt><dd>${room.room_number}</dd>
        <dt>Room type</dt><dd>${room.room_type.charAt(0).toUpperCase() + room.room_type.slice(1)}</dd>
        <dt>Capacity</dt><dd>${room.capacity}</dd>
        <dt>Weekly rate</dt><dd>${money(room.weekly_rate)}</dd>
      </dl>
    </section>
    <section class="confirmation-section">
      <h2>Stay</h2>
      <dl class="detail-list">
        <dt>Arrival</dt><dd>${humanDate(start)}</dd>
        <dt>Departure</dt><dd>${humanDate(end)}</dd>
        <dt>Billable duration</dt><dd>${weeks} ${weeks === 1 ? "week" : "weeks"}</dd>
      </dl>
    </section>
    <section class="confirmation-total">
      <span>Total</span><strong>${money(estimatedTotal)}</strong>
    </section>
    ${canSubmit ? "" : '<div class="message message--error"><strong>This room is no longer available for the selected dates.</strong></div>'}
    <div class="form-actions">
      <a class="button button--secondary" href="${roomLink.href}">Back</a>
      ${canSubmit ? '<button class="button button--primary" type="button" data-submit-booking>Confirm booking</button>' : '<a class="button button--primary" href="/rooms">Find another room</a>'}
    </div>`;

  const submitButton = document.querySelector("[data-submit-booking]");
  if (submitButton) submitButton.addEventListener("click", () => submitBooking(submitButton));
}

async function submitBooking(button) {
  if (button.disabled) return;
  button.disabled = true;
  button.textContent = "Confirming...";
  errorBox.hidden = true;

  try {
    const booking = await createBooking({
      room_id: Number(roomId),
      start_date: start,
      end_date: end,
    });
    window.location.assign(`/booking/submitted?booking_id=${booking.id}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      if (error.message.toLowerCase().includes("student")) {
        showError("You already have a booking that overlaps these dates.");
      } else {
        showError("This room is no longer available for the selected dates.");
      }
    } else if (error instanceof ApiError) {
      showError(error.message);
    } else {
      showError("The booking could not be submitted. Try again.");
    }
    button.disabled = false;
    button.textContent = "Confirm booking";
  }
}
