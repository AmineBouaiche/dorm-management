from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


def test_public_landing_page_is_served_at_root() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "Find your place in Bristol" in response.text
    assert "Browse accommodation" in response.text
    assert "Bristol Floating Harbour" in response.text
    assert 'href="/login"' in response.text
    assert 'href="/register"' in response.text


def test_student_dashboard_has_dedicated_route() -> None:
    with TestClient(app) as client:
        response = client.get("/dashboard")

    assert response.status_code == 200
    assert "Current accommodation" in response.text


def test_authenticated_student_routes_target_dashboard_not_landing_page() -> None:
    config = (FRONTEND / "js" / "config.js").read_text(encoding="utf-8")
    navigation = (FRONTEND / "js" / "components" / "navigation.js").read_text(encoding="utf-8")
    dashboard = (FRONTEND / "js" / "pages" / "dashboard.js").read_text(encoding="utf-8")

    assert 'landing: "/"' in config
    assert 'home: "/dashboard"' in config
    assert '{ label: "Dashboard", href: "/dashboard" }' in navigation
    assert 'currentPath: "/dashboard"' in dashboard


def test_landing_page_uses_existing_design_tokens_and_restricted_image_source() -> None:
    landing = (FRONTEND / "index.html").read_text(encoding="utf-8")
    css = (FRONTEND / "css" / "landing.css").read_text(encoding="utf-8")
    headers = (Path(__file__).resolve().parent.parent / "app" / "core" / "security_headers.py").read_text(encoding="utf-8")

    assert '/static/css/tokens.css' in landing
    assert '/static/css/landing.css' in landing
    assert 'upload.wikimedia.org' in landing
    assert 'https://upload.wikimedia.org' in headers
    assert "linear-gradient" not in css
    assert "radial-gradient" not in css
    assert "#0018a8" not in css
