# Stock adjustment / inventory count feature

This feature adds a dedicated inventory adjustment operation without allowing
`stock_quantity` to be edited through the generic product PATCH endpoint.

## Endpoint

`POST /products/{product_id}/stock/adjust`

Example request:

```json
{
  "actual_quantity": 8,
  "note": "Inventory count: three extra units found"
}
```

If the current accounting balance is 5, the service creates a stock movement:

- `movement_type`: `adjustment`
- `quantity_change`: `+3`
- `balance_after`: `8`

If the actual quantity is lower than the accounting balance, `quantity_change`
is negative. An actual quantity of zero is valid.

The note is required so every manual adjustment has an audit reason.

## Business rules

- only authenticated users may adjust stock;
- only active products can be adjusted;
- `actual_quantity` must be between 0 and 100000;
- direct edits of `stock_quantity` through `PATCH /products/{id}` remain forbidden;
- the product row is locked with `SELECT ... FOR UPDATE`;
- balance update and movement creation happen in the same transaction;
- on a database error, the balance is rolled back;
- if actual and accounting quantities already match, the API returns `409 Conflict`
  and does not create a zero-value movement.

## Migration

No new Alembic migration is required. `stock_movements.movement_type` is already
a string column, so the new `adjustment` movement type fits the existing schema.

## Manual verification

1. Start from a product with `stock_quantity = 10`.
2. Call `/stock/adjust` with `actual_quantity = 7`.
3. Expect `quantity_change = -3` and `balance_after = 7`.
4. Verify `GET /products` shows `stock_quantity = 7`.
5. Verify stock movement history contains the `adjustment` record.
6. Call the same endpoint again with `actual_quantity = 7`; expect `409`.

## Automated tests

`tests/test_stock.py` includes tests for positive and negative adjustments, zero
actual stock, validation, missing and inactive products, no-op conflict, auth,
and rollback on database failure.
