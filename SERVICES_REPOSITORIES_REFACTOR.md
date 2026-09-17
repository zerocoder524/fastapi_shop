# Services + Repositories refactor

The project now has three layers around application behavior:

```text
HTTP / FastAPI routes
        ↓
services/
        ↓
repositories/
        ↓
SQLAlchemy / PostgreSQL
```

## services/

### `auth_service.py`
Owns:
- user registration;
- password hashing;
- authentication;
- JWT token creation;
- transaction handling for registration.

### `product_service.py`
Owns:
- product creation;
- product listing orchestration;
- transaction handling for writes.

### `order_service.py`
Owns:
- duplicate-product validation;
- stock validation;
- stock reduction;
- order creation;
- COMMIT / ROLLBACK.

## repositories/

### `user_repository.py`
Owns SQLAlchemy queries for users:
- `get_by_email()`;
- `add()`.

### `product_repository.py`
Owns product queries:
- active products list;
- locked product lookup via `SELECT ... FOR UPDATE`;
- `add()`.

### `order_repository.py`
Owns order queries:
- `add()`;
- orders by user with eager loading.

## routes.py

Routes now:
- receive HTTP input;
- call services;
- map service exceptions to HTTP status codes;
- do not contain SQLAlchemy `select()` queries.

## security.py

JWT validation stays in the security dependency, but its user lookup is now
delegated to `user_repository`.

## Database / Alembic

No schema changes were made. No new migration is required.

After installing this patch:

```cmd
alembic current
alembic check
```

Expected:

```text
0002_add_stock_quantity (head)
No new upgrade operations detected.
```

## Smoke tests

Re-test:
- POST /auth/register
- POST /auth/token
- GET /products
- POST /products
- POST /orders
- GET /orders/me

API contracts are intentionally unchanged.
