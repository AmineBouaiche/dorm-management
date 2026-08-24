from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


def test_student_dashboard_and_account_routes_are_served() -> None:
    with TestClient(app) as client:
        dashboard = client.get("/dashboard")
        account = client.get("/account")

    assert dashboard.status_code == 200
    assert "Current accommodation" in dashboard.text
    assert account.status_code == 200
    assert "Manage your account information" in account.text


def test_my_bookings_and_booking_detail_routes_are_served() -> None:
    with TestClient(app) as client:
        bookings = client.get("/bookings")
        detail = client.get("/bookings/42")

    assert bookings.status_code == 200
    assert "My bookings" in bookings.text
    assert detail.status_code == 200
    assert "data-cancel-dialog" in detail.text


def test_student_dashboard_prioritises_current_or_upcoming_non_cancelled_booking() -> None:
    source = (FRONTEND / "js" / "pages" / "dashboard.js").read_text(encoding="utf-8")

    assert 'booking.status !== "cancelled"' in source
    assert "booking.end_date >= today" in source
    assert "aActive" in source


def test_booking_detail_uses_real_cancel_endpoint_and_submission_lock() -> None:
    client_source = (FRONTEND / "js" / "api" / "client.js").read_text(encoding="utf-8")
    detail_source = (FRONTEND / "js" / "pages" / "booking-detail.js").read_text(encoding="utf-8")

    assert 'apiRequest(`/bookings/${bookingId}/cancel`' in client_source
    assert "confirmButton.disabled = true" in detail_source
    assert 'confirmButton.textContent = "Cancelling..."' in detail_source
    assert 'renderBooking("Booking cancelled.")' in detail_source


def test_account_page_supports_student_and_admin_identity_without_editing() -> None:
    source = (FRONTEND / "js" / "pages" / "account.js").read_text(encoding="utf-8")

    assert "student.student_id" in source
    assert "Administrator" in source
    assert "signOut" in source
    assert "PATCH" not in source
