from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


def test_login_and_registration_pages_are_served() -> None:
    with TestClient(app) as client:
        login = client.get("/login")
        register = client.get("/register")

    assert login.status_code == 200
    assert "Sign in" in login.text
    assert 'data-login-form' in login.text
    assert register.status_code == 200
    assert "Create your account" in register.text
    assert 'data-register-form' in register.text


def test_protected_session_checkpoints_are_served() -> None:
    with TestClient(app) as client:
        student = client.get("/session")
        admin = client.get("/admin/session")

    assert student.status_code == 200
    assert "Authentication verified" in student.text
    assert admin.status_code == 200
    assert "Administration access verified" in admin.text


def test_auth_frontend_uses_tab_scoped_token_storage() -> None:
    source = (FRONTEND / "js" / "auth" / "session.js").read_text(encoding="utf-8")

    assert "sessionStorage" in source
    assert "localStorage" not in source
    assert 'residence.access_token' in source


def test_api_client_attaches_bearer_token_and_handles_401() -> None:
    source = (FRONTEND / "js" / "api" / "client.js").read_text(encoding="utf-8")

    assert 'Authorization' in source
    assert 'Bearer ${token}' in source
    assert "response.status === 401" in source


def test_registration_does_not_accept_admin_role_from_client() -> None:
    source = (FRONTEND / "js" / "pages" / "register.js").read_text(encoding="utf-8")

    assert "role:" not in source
    assert "student_id" in source


def test_logout_redirect_and_message_markup() -> None:
    session_js = (FRONTEND / "js" / "auth" / "session.js").read_text(encoding="utf-8")
    login_js = (FRONTEND / "js" / "pages" / "login.js").read_text(encoding="utf-8")
    login_html = (FRONTEND / "auth" / "login.html").read_text(encoding="utf-8")

    assert "?signed_out=1" in session_js
    assert 'params.get("signed_out") === "1"' in login_js
    assert "You have been signed out." in login_html
