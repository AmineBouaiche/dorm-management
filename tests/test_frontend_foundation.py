from fastapi.testclient import TestClient

from app.main import app


def test_frontend_root_is_served() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "Residence" in response.text


def test_style_guide_is_served() -> None:
    with TestClient(app) as client:
        response = client.get("/style-guide")

    assert response.status_code == 200
    assert "Frontend foundation" in response.text


def test_design_tokens_are_served() -> None:
    with TestClient(app) as client:
        response = client.get("/static/css/tokens.css")

    assert response.status_code == 200
    assert "--color-primary: #0018a8" in response.text
    assert '--font-family-primary: "Source Sans 3"' in response.text
