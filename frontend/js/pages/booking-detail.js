import { ApiError, cancelBooking, listMyBookings } from "../api/client.js";
import { requireAuthentication } from "../auth/guards.js";
import { renderPrimaryNavigation } from "../components/navigation.js";

const page = document.querySelector("[data-booking-detail-page]");
const content = document.querySelector("[data-booking-detail-content]");
const errorBox = document.querySelector("[data-booking-detail-error]");
const errorText = document.querySelector("[data-booking-detail-error-text]");
const dialog = document.querySelector("[data-cancel-dialog]");
const cancelSummary = document.querySelector("[data-cancel-summary]");
const keepButton = document.querySelector("[data-keep-booking]");
const confirmButton = document.querySelector("[data-confirm-cancel]");
const bookingId = Number(window.location.pathname.split("/").filter(Boolean).at(-1));
let booking = null;

const user = await requireAuthentication({ role: "student" });
if (user && page) {
  renderPrimaryNavigation({ currentPath: "/bookings", role: "student" });
  page.hidden = false;
  await loadBooking();
}

function money(value) { return new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(Number(value)); }
function humanDate(value) { return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`)); }
function statusMarkup(status) {
  const modifier = status === "confirmed" ? "success" : status === "pending" ? "warning" : "error";
  return `<span class="status status--${modifier}">${status.charAt(0).toUpperCase() + status.slice(1)}</span>`;
}
function billableWeeks(start, end) {
  const days = (Date.parse(`${end}T00:00:00Z`) - Date.parse(`${start}T00:00:00Z`)) / 86400000;
  return Math.ceil(days / 7);
}

async function loadBooking() {
  if (!Number.isInteger(bookingId) || bookingId <= 0) { showError("The booking reference is invalid."); return; }
  try {
    const bookings = await listMyBookings();
    booking = bookings.find((item) => item.id === bookingId) || null;
    if (!booking) { showError("This booking could not be found in your account."); return; }
    renderBooking();
  } catch (error) { showError(error instanceof ApiError ? error.message : "Try again."); }
}

function showError(message) {
  content.innerHTML = "";
  errorText.textContent = message;
  errorBox.hidden = false;
}

function renderBooking(successMessage = "") {
  errorBox.hidden = true;
  const weeks = billableWeeks(booking.start_date, booking.end_date);
  const today = new Date().toISOString().slice(0, 10);
  const cancellable = booking.status !== "cancelled" && booking.end_date >= today;
  content.innerHTML = `
    ${successMessage ? `<div class="message message--success"><strong>${successMessage}</strong></div>` : ""}
    <header class="booking-detail-header"><div><p class="card__eyebrow">Booking #${booking.id}</p><h1>${booking.room.building.name}, Room ${booking.room.room_number}</h1></div>${statusMarkup(booking.status)}</header>
    <section class="section"><h2>Accommodation</h2><dl class="detail-list">
      <dt>Room</dt><dd>${booking.room.room_number}</dd><dt>Residence</dt><dd>${booking.room.building.name}</dd><dt>Room type</dt><dd>${booking.room.room_type.charAt(0).toUpperCase() + booking.room.room_type.slice(1)}</dd><dt>Weekly rate</dt><dd>${money(booking.room.weekly_rate)}</dd>
    </dl></section>
    <section class="section"><h2>Stay</h2><dl class="detail-list">
      <dt>Arrival</dt><dd>${humanDate(booking.start_date)}</dd><dt>Departure</dt><dd>${humanDate(booking.end_date)}</dd><dt>Billable duration</dt><dd>${weeks} ${weeks === 1 ? "week" : "weeks"}</dd>
    </dl></section>
    <section class="booking-detail-total"><span>Total</span><strong>${money(booking.amount)}</strong></section>
    ${cancellable ? '<div class="booking-detail-actions"><button class="button button--danger-outline" type="button" data-open-cancel>Cancel booking</button></div>' : ""}`;
  content.querySelector("[data-open-cancel]")?.addEventListener("click", openDialog);
}

function openDialog() {
  cancelSummary.textContent = `${booking.room.building.name}, Room ${booking.room.room_number}. ${humanDate(booking.start_date)} to ${humanDate(booking.end_date)}.`;
  dialog.hidden = false;
  confirmButton.focus();
}
function closeDialog() { dialog.hidden = true; }
keepButton?.addEventListener("click", closeDialog);
dialog?.addEventListener("click", (event) => { if (event.target === dialog) closeDialog(); });
document.addEventListener("keydown", (event) => { if (event.key === "Escape" && dialog && !dialog.hidden) closeDialog(); });

confirmButton?.addEventListener("click", async () => {
  if (!booking || confirmButton.disabled) return;
  confirmButton.disabled = true;
  confirmButton.textContent = "Cancelling...";
  try {
    booking = await cancelBooking(booking.id);
    closeDialog();
    renderBooking("Booking cancelled.");
  } catch (error) {
    closeDialog();
    showError(error instanceof ApiError ? error.message : "The booking could not be cancelled. Try again.");
  } finally {
    confirmButton.disabled = false;
    confirmButton.textContent = "Cancel booking";
  }
});
