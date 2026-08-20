from __future__ import annotations

import os
from collections.abc import Generator

# Tests must never run against the persistent development database.
# Set DATABASE_URL before importing application modules because app.db.database
# constructs its SQLAlchemy engine at import time.
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://dorm:dorm@localhost:5433/dorm_management_test",
)

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.database import engine, get_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def migrated_test_database() -> Generator[None, None, None]:
    """Rebuild the dedicated test schema from Alembic migrations once per run."""
    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", str(engine.url))
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
    yield


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    # The outer transaction guarantees that every test leaves the test database
    # exactly as it found it even when application services call session.commit().
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
