import { ApiError, listMyBookings } from "../api/client.js";
import { requireAuthentication } from "../auth/guards.js";
import { renderPrimaryNavigation } from "../components/navigation.js";

const page = document.querySelector("[data-bookings-page]");
const content = document.querySelector("[data-bookings-content]");
const errorBox = document.querySelector("[data-bookings-error]");
const errorText = document.querySelector("[data-bookings-error-text]");

const user = await requireAuthentication({ role: "student" });
if (user && page) {
  renderPrimaryNavigation({ currentPath: "/bookings", role: "student" });
  page.hidden = false;
  await loadBookings();
}

function money(value) {
  return new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(Number(value));
}
function humanDate(value) {
  return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`));
}
function statusMarkup(status) {
  const modifier = status === "confirmed" ? "success" : status === "pending" ? "warning" : "error";
  return `<span class="status status--${modifier}">${status.charAt(0).toUpperCase() + status.slice(1)}</span>`;
}
function bookingCard(booking) {
  return `<article class="panel booking-card">
    <div class="booking-card__top"><div><p class="card__eyebrow">${booking.room.building.name}</p><h3>Room ${booking.room.room_number}</h3></div>${statusMarkup(booking.status)}</div>
    <p class="text-secondary">${humanDate(booking.start_date)} to ${humanDate(booking.end_date)}</p>
    <p>${money(booking.room.weekly_rate)} / week</p>
    <div class="booking-card__action"><a class="text-link" href="/bookings/${booking.id}">View details</a></div>
  </article>`;
}
function section(title, items) {
  if (!items.length) return "";
  return `<section class="booking-group"><h2>${title}</h2><div class="booking-list">${items.map(bookingCard).join("")}</div></section>`;
}

async function loadBookings() {
  try {
    const bookings = await listMyBookings();
    const today = new Date().toISOString().slice(0, 10);
    const current = bookings.filter((b) => b.status !== "cancelled" && b.end_date >= today).sort((a,b) => a.start_date.localeCompare(b.start_date));
    const previous = bookings.filter((b) => b.status === "cancelled" || b.end_date < today).sort((a,b) => b.start_date.localeCompare(a.start_date));
    if (!bookings.length) {
      content.innerHTML = `<section class="panel empty-state student-empty-state"><h2>No bookings yet</h2><p>Your accommodation bookings will appear here.</p><a class="button button--primary" href="/rooms">Browse rooms</a></section>`;
      return;
    }
    content.innerHTML = `${section("Current", current)}${section("Previous", previous)}`;
  } catch (error) {
    content.innerHTML = "";
    errorText.textContent = error instanceof ApiError ? error.message : "Try again.";
    errorBox.hidden = false;
  }
}
