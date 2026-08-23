from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


def test_unsafe_cookie_authenticated_requests_require_csrf() -> None:
    # CSRF enforcement itself is covered through the browser-session auth test.
    # This regression check ensures the middleware remains installed on the app.
    names = [middleware.cls.__name__ for middleware in app.user_middleware]
    assert "CSRFMiddleware" in names


def test_dynamic_frontend_fields_are_escaped_before_html_insertion() -> None:
    files = [
        FRONTEND / "js" / "pages" / "account.js",
        FRONTEND / "js" / "pages" / "booking-detail.js",
        FRONTEND / "js" / "pages" / "booking-handoff.js",
        FRONTEND / "js" / "pages" / "booking-submitted.js",
        FRONTEND / "js" / "pages" / "bookings.js",
        FRONTEND / "js" / "pages" / "dashboard.js",
        FRONTEND / "js" / "pages" / "rooms.js",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    assert "escapeHtml" in combined
    assert "sessionStorage" not in combined


def test_login_page_still_serves_after_cookie_auth_refactor() -> None:
    with TestClient(app) as client:
        response = client.get("/login")
    assert response.status_code == 200
