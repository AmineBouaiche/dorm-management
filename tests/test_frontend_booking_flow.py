from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"


def test_booking_flow_pages_are_served() -> None:
    client = TestClient(app)
    assert client.get("/booking/confirm").status_code == 200
    assert client.get("/booking/submitted").status_code == 200
    assert client.get("/bookings").status_code == 200


def test_booking_confirmation_submits_to_real_api() -> None:
    js = (FRONTEND / "js" / "pages" / "booking-handoff.js").read_text(encoding="utf-8")
    client_js = (FRONTEND / "js" / "api" / "client.js").read_text(encoding="utf-8")
    assert "createBooking" in js
    assert 'method: "POST"' in client_js
    assert 'apiRequest("/bookings"' in client_js


def test_booking_confirmation_prevents_duplicate_submission() -> None:
    js = (FRONTEND / "js" / "pages" / "booking-handoff.js").read_text(encoding="utf-8")
    assert "if (button.disabled) return" in js
    assert "button.disabled = true" in js
    assert 'button.textContent = "Confirming..."' in js


def test_booking_confirmation_has_domain_specific_conflict_messages() -> None:
    js = (FRONTEND / "js" / "pages" / "booking-handoff.js").read_text(encoding="utf-8")
    assert "You already have a booking that overlaps these dates." in js
    assert "This room is no longer available for the selected dates." in js


def test_booking_submitted_uses_server_booking_amount_and_pending_state() -> None:
    js = (FRONTEND / "js" / "pages" / "booking-submitted.js").read_text(encoding="utf-8")
    assert "booking.amount" in js
    assert "Pending" in js
    assert "listMyBookings" in js
