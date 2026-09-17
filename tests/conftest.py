import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# The application reads these values at import time.
# Local pytest runs default to an isolated in-memory SQLite database.
# GitHub Actions supplies TEST_DATABASE_URL pointing to PostgreSQL.
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+pysqlite:///:memory:",
)

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault(
    "SECRET_KEY",
    "pytest-only-secret-key-0123456789abcdef",
)
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


if TEST_DATABASE_URL.startswith("sqlite"):
    test_engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    test_engine = create_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
    )

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    # Each test gets a clean database.
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    register_response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "full_name": "Test User",
            "password": "strongpassword123",
        },
    )
    assert register_response.status_code == 201

    token_response = client.post(
        "/auth/token",
        data={
            "username": "user@example.com",
            "password": "strongpassword123",
        },
    )
    assert token_response.status_code == 200

    token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
