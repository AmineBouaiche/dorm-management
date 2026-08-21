import { ApiError, listMyBookings } from "../api/client.js";
import { requireAuthentication } from "../auth/guards.js";
import { renderPrimaryNavigation } from "../components/navigation.js";

const page = document.querySelector("[data-dashboard-page]");
const bookingHost = document.querySelector("[data-dashboard-booking]");
const welcome = document.querySelector("[data-welcome]");

const user = await requireAuthentication({ role: "student" });
if (user && page) {
  renderPrimaryNavigation({ currentPath: "/", role: "student" });
  const firstName = user.student?.first_name || "Student";
  welcome.textContent = `Welcome, ${firstName}. Manage your accommodation and booking.`;
  page.hidden = false;
  await loadDashboard();
}

function money(value) {
  return new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(Number(value));
}

function humanDate(value) {
  return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`));
}

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function relevantBooking(bookings) {
  const today = todayIso();
  const candidates = bookings
    .filter((booking) => booking.status !== "cancelled" && booking.end_date >= today)
    .sort((a, b) => {
      const aActive = a.start_date <= today && a.end_date >= today;
      const bActive = b.start_date <= today && b.end_date >= today;
      if (aActive !== bActive) return aActive ? -1 : 1;
      return a.start_date.localeCompare(b.start_date);
    });
  return candidates[0] || null;
}

function statusMarkup(status) {
  const modifier = status === "confirmed" ? "success" : status === "pending" ? "warning" : "error";
  const label = status.charAt(0).toUpperCase() + status.slice(1);
  return `<span class="status status--${modifier}">${label}</span>`;
}

function renderEmpty() {
  bookingHost.innerHTML = `
    <section class="panel empty-state student-empty-state">
      <h2>No current accommodation</h2>
      <p>You do not currently have an active or upcoming accommodation booking.</p>
      <a class="button button--primary" href="/rooms">Browse available rooms</a>
    </section>`;
}

function renderBooking(booking) {
  bookingHost.innerHTML = `
    <article class="panel dashboard-booking">
      <div class="dashboard-booking__top">
        <div>
          <p class="card__eyebrow">${booking.room.building.name}</p>
          <h2>Room ${booking.room.room_number}</h2>
        </div>
        ${statusMarkup(booking.status)}
      </div>
      <p>${booking.room.room_type.charAt(0).toUpperCase() + booking.room.room_type.slice(1)} room</p>
      <p class="text-secondary">${humanDate(booking.start_date)} to ${humanDate(booking.end_date)}</p>
      <div class="dashboard-booking__bottom">
        <strong>${money(booking.room.weekly_rate)} / week</strong>
        <a class="text-link" href="/bookings/${booking.id}">View booking</a>
      </div>
    </article>`;
}

async function loadDashboard() {
  try {
    const bookings = await listMyBookings();
    const booking = relevantBooking(bookings);
    if (booking) renderBooking(booking); else renderEmpty();
  } catch (error) {
    const message = error instanceof ApiError ? error.message : "Try again.";
    bookingHost.innerHTML = `<div class="message message--error"><strong>We could not load your accommodation.</strong><p>${message}</p></div>`;
  }
}
