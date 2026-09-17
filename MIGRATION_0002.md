# Migration 0002: stock_quantity

This migration adds the integer field `stock_quantity` to `products`.

Existing products are preserved. Because the migration uses a database
server default of `0`, every existing product receives:

    stock_quantity = 0

The field is:

- integer;
- NOT NULL;
- default 0;
- validated by Pydantic as >= 0.

## Before applying

The current database revision must be:

    0001_initial (head)

Stop Uvicorn with Ctrl+C.

## Apply

From:

    C:\Users\Asus\Documents\GitHub\fastapi_shop

run:

    .venv\Scripts\activate
    alembic current
    alembic history
    alembic upgrade head
    alembic current
    alembic check

Expected current revision after upgrade:

    0002_add_stock_quantity (head)

Expected `alembic check`:

    No new upgrade operations detected.

## Verify in PostgreSQL

Run:

    SELECT id, name, price, stock_quantity
    FROM products
    ORDER BY id;

The existing product(s) should remain, with stock_quantity = 0.

Check the Alembic revision:

    SELECT * FROM alembic_version;

Expected:

    0002_add_stock_quantity

## Verify API

Restart:

    uvicorn app.main:app --reload

GET /products now includes:

    "stock_quantity": 0

POST /products accepts, for example:

    {
      "name": "Букет красных роз",
      "description": "15 красных роз",
      "price": 3900,
      "stock_quantity": 12
    }

## Rollback

For learning/testing only:

    alembic downgrade -1

This returns the database to `0001_initial` and removes the
`stock_quantity` column. Any values stored in that column are lost on rollback.
