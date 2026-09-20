# Feature: stock movements

## Что добавлено

- `POST /products/{product_id}/stock/replenish` — отдельное пополнение остатка.
- `GET /products/{product_id}/stock/movements` — история движения остатка.
- `PATCH /products/{product_id}` больше не принимает `stock_quantity`; прямое изменение остатка возвращает `422`.
- Новая таблица `stock_movements` хранит:
  - `product_id`
  - `order_id` (если движение связано с заказом)
  - `movement_type`
  - `quantity_change`
  - `balance_after`
  - `note`
  - `created_at`
- Создание товара с начальным остатком фиксирует движение `initial`.
- Заказ фиксирует отрицательное движение `order` в той же транзакции, что и уменьшение остатка.
- Пополнение фиксирует положительное движение `replenishment` в той же транзакции.
- Миграция `0003_create_stock_movements` создаёт начальную запись `opening_balance` для уже существующих товаров, чтобы история имела явную точку отсчёта.

## Применение в отдельной feature-ветке

```cmd
cd /d C:\Users\Asus\Documents\GitHub\fastapi_shop
git checkout main
git pull
git checkout -b feature/stock-movements
```

Распаковать содержимое patch-архива в корень проекта с заменой файлов.

Затем:

```cmd
.venv\Scripts\activate
python -m compileall app alembic tests
alembic upgrade head
alembic current
alembic check
pytest --cov=app --cov-report=term-missing --cov-fail-under=95
```

Ожидаемый Alembic head:

```text
0003_create_stock_movements (head)
```

## Ручная проверка Swagger

1. Авторизоваться.
2. Создать товар, например с `stock_quantity = 5`.
3. Выполнить:

```http
POST /products/{id}/stock/replenish
```

```json
{
  "quantity": 7,
  "note": "Поставка от поставщика"
}
```

Ожидается `201` и `balance_after = 12`.

4. Проверить историю:

```http
GET /products/{id}/stock/movements
```

5. Создать заказ на 3 единицы и снова запросить историю. Должно появиться движение:

```text
movement_type = order
quantity_change = -3
balance_after = 9
order_id = <id заказа>
```

6. Попытка изменить остаток через PATCH:

```json
{
  "stock_quantity": 100
}
```

должна вернуть `422`.

## Git

После успешных проверок:

```cmd
git status
git add .
git commit -m "Add stock replenishment and movement history"
git push -u origin feature/stock-movements
```

Далее создать Pull Request `feature/stock-movements -> main` и дождаться зелёного `pytest`.
