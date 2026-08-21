import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.core.security import create_access_token, decode_access_token
from app.main import create_app


def test_security_headers_are_attached() -> None:
    application = create_app()
    with TestClient(application) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_production_rejects_placeholder_jwt_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret_key="replace-with-a-long-random-secret")


def test_production_disables_api_docs_and_style_guide() -> None:
    production_settings = Settings(
        environment="production",
        jwt_secret_key="a-unique-production-secret-that-is-long-enough-12345",
    )
    application = create_app(production_settings)

    with TestClient(application) as client:
        docs = client.get("/docs")
        openapi = client.get("/openapi.json")
        style_guide = client.get("/style-guide")
        health = client.get("/health")

    assert docs.status_code == 404
    assert openapi.status_code == 404
    assert style_guide.status_code == 404
    assert health.status_code == 200


def test_access_tokens_include_required_identity_claims() -> None:
    token = create_access_token(42)
    assert decode_access_token(token) == 42


def test_development_csp_allows_swagger_assets_only() -> None:
    development_app = create_app(Settings(environment="development"))
    production_app = create_app(
        Settings(
            environment="production",
            jwt_secret_key="a-unique-production-secret-that-is-long-enough-12345",
        )
    )

    with TestClient(development_app) as client:
        development_csp = client.get("/health").headers["content-security-policy"]
    with TestClient(production_app) as client:
        production_csp = client.get("/health").headers["content-security-policy"]

    assert "https://cdn.jsdelivr.net" in development_csp
    assert "'unsafe-inline'" in development_csp
    assert "https://cdn.jsdelivr.net" not in production_csp
    assert "'unsafe-inline'" not in production_csp
