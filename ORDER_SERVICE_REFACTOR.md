# Архитектурный рефакторинг: Order Service

Создание заказа и складская бизнес-логика вынесены из `app/routes.py` в:

    app/services/order_service.py

## Теперь ответственность разделена

### `routes.py`
Отвечает за HTTP:

- получает `OrderCreate`;
- получает текущего пользователя;
- вызывает сервис;
- преобразует сервисные исключения в HTTP-коды.

### `services/order_service.py`
Отвечает за бизнес-логику:

- запрет дублей одного товара в заказе;
- поиск активных товаров;
- `SELECT ... FOR UPDATE`;
- проверка остатков;
- уменьшение `stock_quantity`;
- создание `Order` и `OrderItem`;
- `COMMIT`;
- `ROLLBACK`.

Сервисный слой не импортирует FastAPI и не создаёт `HTTPException`.

## HTTP mapping

- DuplicateProductError -> 400
- ProductsUnavailableError -> 404
- InsufficientStockError -> 409
- OrderPersistenceError -> 500

## Alembic

Новая миграция НЕ требуется.

Схема PostgreSQL не меняется. После копирования патча:

    alembic current
    alembic check

Ожидается:

    0002_add_stock_quantity (head)
    No new upgrade operations detected.

## Smoke test

Запустить:

    uvicorn app.main:app --reload

Затем заново Authorize в Swagger и повторить уже проверенные сценарии:

1. product 1, quantity 1 -> 409
2. product 2, quantity <= stock -> 201, остаток уменьшается
3. quantity > stock -> 409, остаток не меняется
4. смешанный заказ с недоступной позицией -> 409 и полный rollback

Поведение API должно остаться прежним: это архитектурный рефакторинг,
а не изменение контрактов.
