# Pytest and GitHub Actions

The project now includes automated API tests and CI.

## Local test installation

From the project root:

```cmd
cd /d C:\Users\Asus\Documents\GitHub\fastapi_shop
.venv\Scripts\activate
pip install -r requirements-dev.txt
```

## Run tests locally

```cmd
pytest
```

With coverage:

```cmd
pytest --cov=app --cov-report=term-missing --cov-fail-under=95
```

Local tests use an isolated in-memory SQLite database by default, so they do
not delete or change data in the normal `fastapi_shop` PostgreSQL database.

To explicitly run the tests against a separate PostgreSQL test database, set:

```cmd
set TEST_DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/fastapi_shop_test
set DATABASE_URL=%TEST_DATABASE_URL%
pytest
```

Never point `TEST_DATABASE_URL` at the production or normal development database:
the test fixture recreates application tables.

## What is tested

### Auth
- registration;
- duplicate registration;
- successful token login;
- invalid password.

### Products
- public product listing;
- authentication requirement for product creation;
- create and read product including `stock_quantity`.

### Orders
- successful order creation;
- stock reduction;
- `/orders/me`;
- zero stock -> 409;
- order quantity greater than stock -> 409;
- atomic rollback for a mixed invalid order;
- duplicate product in one order -> 400.

## GitHub Actions

Workflow:

```text
.github/workflows/tests.yml
```

It runs automatically on:

- every `push`;
- every pull request;
- manual `workflow_dispatch`.

The GitHub Actions job starts a PostgreSQL 18 service, installs Python 3.12 and
the development dependencies, then runs:

```text
alembic upgrade head
alembic check
pytest --cov=app --cov-report=term-missing --cov-fail-under=95
```

This means CI validates both Alembic migrations and the API test suite.


### Edge cases
- invalid JWT;
- JWT without `sub`;
- valid JWT for a user that no longer exists;
- missing product in an order;
- simulated database failures for registration, product creation and order creation;
- rollback of stock after an order persistence failure;
- root health endpoint.

The CI build fails if application coverage drops below 95%.
