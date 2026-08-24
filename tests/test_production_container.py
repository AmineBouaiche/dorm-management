from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_uses_non_root_runtime_and_healthcheck() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.13-slim AS builder" in dockerfile
    assert "FROM python:3.13-slim AS runtime" in dockerfile
    assert "USER app" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "ENVIRONMENT=production" in dockerfile


def test_production_image_contains_migrations_and_entrypoint() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    entrypoint = (ROOT / "scripts" / "docker-entrypoint.sh").read_text(encoding="utf-8")

    assert "COPY migrations ./migrations" in dockerfile
    assert "COPY alembic.ini ./alembic.ini" in dockerfile
    assert "alembic upgrade head" in entrypoint
    assert "exec uvicorn app.main:app" in entrypoint


def test_compose_exposes_production_profile_without_hardcoded_secret() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert 'profiles: ["production"]' in compose
    assert 'JWT_SECRET_KEY: ${JWT_SECRET_KEY:?' in compose
    assert 'DATABASE_URL: postgresql+psycopg://dorm:dorm@db:5432/dorm_management' in compose


def test_ci_builds_production_container() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "Build production container" in workflow
    assert "docker build --tag dorm-management:ci ." in workflow


def test_runtime_files_are_root_owned_and_not_writable_by_app_user() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    assert "chown -R root:app /app" in dockerfile
    assert "chmod -R a-w /app" in dockerfile


def test_production_uvicorn_disables_server_header() -> None:
    entrypoint = Path("scripts/docker-entrypoint.sh").read_text(encoding="utf-8")
    assert "--no-server-header" in entrypoint


def test_entrypoint_uses_platform_port() -> None:
    entrypoint = Path("scripts/docker-entrypoint.sh").read_text(encoding="utf-8")
    assert '"${PORT:-8000}"' in entrypoint
