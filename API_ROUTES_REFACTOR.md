# API routes refactor

The monolithic `app/routes.py` has been split into:

```text
app/
└── api/
    ├── __init__.py
    ├── router.py
    └── routes/
        ├── __init__.py
        ├── auth.py
        ├── products.py
        └── orders.py
```

`app/api/router.py` combines all domain routers through one `APIRouter`.
`app/main.py` includes only `api_router`.

The old `app/routes.py` is now only a compatibility shim and contains no endpoint logic.

Public API paths are unchanged:
- `POST /auth/register`
- `POST /auth/token`
- `GET /products`
- `POST /products`
- `POST /orders`
- `GET /orders/me`

No database schema changed, so no new Alembic migration is required.

Checks:

```cmd
alembic current
alembic check
uvicorn app.main:app --reload
```

Expected database state:

```text
0002_add_stock_quantity (head)
No new upgrade operations detected.
```
