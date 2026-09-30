import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
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
from app.models import User  # noqa: E402


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


def register_user(client: TestClient, email: str) -> None:
    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "full_name": "Test User",
            "password": "strongpassword123",
        },
    )
    assert register_response.status_code == 201


def login_headers(client: TestClient, email: str) -> dict[str, str]:
    token_response = client.post(
        "/auth/token",
        data={
            "username": email,
            "password": "strongpassword123",
        },
    )
    assert token_response.status_code == 200

    token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    """Headers of a regular (non-admin) registered user."""
    register_user(client, "user@example.com")
    return login_headers(client, "user@example.com")


@pytest.fixture()
def admin_headers(client: TestClient, db_session: Session) -> dict[str, str]:
    """Headers of a user promoted to administrator directly in the database."""
    register_user(client, "admin@example.com")

    admin = db_session.scalar(
        select(User).where(User.email == "admin@example.com")
    )
    admin.is_admin = True
    db_session.commit()

    return login_headers(client, "admin@example.com")
