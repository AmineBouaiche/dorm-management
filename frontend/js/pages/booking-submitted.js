import { ApiError, listMyBookings } from "../api/client.js";
import { requireAuthentication } from "../auth/guards.js";
import { renderPrimaryNavigation } from "../components/navigation.js";

const page = document.querySelector("[data-submitted-page]");
const content = document.querySelector("[data-submitted-content]");
const errorBox = document.querySelector("[data-submitted-error]");
const errorText = document.querySelector("[data-submitted-error-text]");
const bookingId = Number(new URLSearchParams(window.location.search).get("booking_id"));

const user = await requireAuthentication({ role: "student" });
if (user && page) {
  renderPrimaryNavigation({ currentPath: "/rooms", role: "student" });
  page.hidden = false;
  await loadBooking();
}

function money(value) {
  return new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(Number(value));
}
function humanDate(value) {
  return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`));
}

async function loadBooking() {
  if (!Number.isInteger(bookingId) || bookingId <= 0) {
    showError("The booking reference is invalid.");
    return;
  }
  try {
    const bookings = await listMyBookings();
    const booking = bookings.find((item) => item.id === bookingId);
    if (!booking) { showError("This booking could not be found in your account."); return; }
    renderBooking(booking);
  } catch (error) {
    showError(error instanceof ApiError ? error.message : "Try again.");
  }
}

function showError(message) {
  content.innerHTML = "";
  errorText.textContent = message;
  errorBox.hidden = false;
}

function renderBooking(booking) {
  content.innerHTML = `
    <div class="status status--warning">Pending</div>
    <h2 class="submitted-booking__title">${booking.room.building.name}, Room ${booking.room.room_number}</h2>
    <dl class="detail-list">
      <dt>Arrival</dt><dd>${humanDate(booking.start_date)}</dd>
      <dt>Departure</dt><dd>${humanDate(booking.end_date)}</dd>
      <dt>Total</dt><dd>${money(booking.amount)}</dd>
      <dt>Status</dt><dd>Pending</dd>
    </dl>
    <p class="text-secondary">An administrator must confirm the request before it becomes a confirmed accommodation booking.</p>
    <div class="form-actions">
      <a class="button button--secondary" href="/rooms">Browse rooms</a>
      <a class="button button--primary" href="/bookings">View my bookings</a>
    </div>`;
}
