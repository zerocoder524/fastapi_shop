# FastAPI Shop

Backend интернет-магазина на **FastAPI + PostgreSQL + SQLAlchemy 2 + JWT**.

Рабочая папка проекта:

```text
C:\Users\Asus\Documents\GitHub\fastapi_shop
```

## Развёртывание на Windows 11

### 1. Перейти в каталог проекта

```cmd
cd /d C:\Users\Asus\Documents\GitHub\fastapi_shop
```

### 2. Создать виртуальное окружение

```cmd
py -3.12 -m venv .venv
.venv\Scripts\activate
```

После активации:

```text
(.venv) C:\Users\Asus\Documents\GitHub\fastapi_shop>
```

### 3. Установить зависимости

```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Создать PostgreSQL-базу

```sql
CREATE DATABASE fastapi_shop;
```

### 5. Создать `.env`

```cmd
copy .env.example .env
```

Откройте `.env` и укажите:

```env
DATABASE_URL=postgresql+psycopg://postgres:ВАШ_ПАРОЛЬ@localhost:5432/fastapi_shop
SECRET_KEY=ВАШ_СЕКРЕТНЫЙ_КЛЮЧ
```

Сгенерировать `SECRET_KEY`:

```cmd
python -c "import secrets; print(secrets.token_hex(32))"
```

`.env` находится в `.gitignore` и не должен попадать в GitHub.

### 6. Запустить сервер

```cmd
uvicorn app.main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Быстрый запуск

В проекте есть:

```text
setup_windows.cmd
start_windows.cmd
```

Первая установка:

```cmd
cd /d C:\Users\Asus\Documents\GitHub\fastapi_shop
setup_windows.cmd
```

После этого:

1. создайте базу `fastapi_shop`;
2. откройте `.env`;
3. укажите пароль PostgreSQL;
4. укажите `SECRET_KEY`.

Затем:

```cmd
start_windows.cmd
```

## Проверка API

### Регистрация

`POST /auth/register`

```json
{
  "email": "user@example.com",
  "full_name": "Иван Иванов",
  "password": "strongpassword123"
}
```

### Вход

`POST /auth/token`

В Swagger:

```text
username = user@example.com
password = strongpassword123
```

После получения JWT нажмите **Authorize**.

### Создать товар

`POST /products`

```json
{
  "name": "Букет белых роз",
  "description": "15 белых роз",
  "price": 3500
}
```

### Каталог

`GET /products`

### Создать заказ

`POST /orders`

```json
{
  "items": [
    {
      "product_id": 1,
      "quantity": 2
    }
  ]
}
```

### Свои заказы

`GET /orders/me`

## Структура проекта

```text
fastapi_shop/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── routes.py
│   ├── schemas.py
│   └── security.py
│
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── setup_windows.cmd
└── start_windows.cmd
```

При первом запуске таблицы создаются автоматически через:

```python
Base.metadata.create_all(bind=engine)
```

Следующий этап — миграции Alembic.

## Git

Если репозиторий ещё не создан:

```cmd
cd /d C:\Users\Asus\Documents\GitHub\fastapi_shop
git init
git add .
git status
git commit -m "Initial FastAPI Shop backend"
```

Проверьте, что `.env` не появился среди файлов коммита.


---

# Database migrations: Alembic

Проект использует Alembic для версионирования схемы PostgreSQL.

Для **существующей** базы, в которой уже есть `users`, `products`,
`orders`, `order_items`, один раз выполните:

```cmd
baseline_existing_db.cmd
```

или вручную:

```cmd
.venv\Scripts\activate
pip install -r requirements.txt
alembic stamp 0001_initial
alembic current
alembic check
```

После baseline все будущие изменения схемы оформляются миграциями:

```cmd
alembic revision --autogenerate -m "описание изменения"
alembic upgrade head
```

Для **новой пустой** базы:

```cmd
alembic upgrade head
```

Подробнее: `ALEMBIC_SETUP.md`.


---

# Migration 0002 — Product stock

Migration `0002_add_stock_quantity` adds:

```text
products.stock_quantity INTEGER NOT NULL DEFAULT 0
```

Apply:

```cmd
alembic upgrade head
alembic current
alembic check
```

Existing products are preserved and receive `stock_quantity = 0`.

API product create/read schemas also include `stock_quantity`.


---

# Складская логика заказов

`POST /orders` теперь проверяет остатки `stock_quantity`, блокирует товарные строки
через `SELECT ... FOR UPDATE`, списывает остатки и создаёт заказ в одной транзакции.

При недостаточном остатке возвращается `409 Conflict`.
При ошибке выполняется `ROLLBACK`.
Новая Alembic migration не требуется, так как схема БД не меняется.

Подробнее: `STOCK_ORDER_LOGIC.md`.


---

# Order service layer

Order creation and warehouse rules were moved from `app/routes.py` to:

```text
app/services/order_service.py
```

The route now handles HTTP concerns only, while the service owns product locking,
stock validation, stock reduction, order creation, COMMIT and ROLLBACK.

No database migration is required for this refactor.

See `ORDER_SERVICE_REFACTOR.md`.


---

# Services and repositories

Application logic is now separated into:

```text
routes -> services -> repositories -> SQLAlchemy/PostgreSQL
```

Added:

```text
app/services/auth_service.py
app/services/product_service.py
app/repositories/user_repository.py
app/repositories/product_repository.py
app/repositories/order_repository.py
```

`order_service.py` now also uses repositories instead of direct SQL queries.

No Alembic migration is needed because the database schema did not change.

See `SERVICES_REPOSITORIES_REFACTOR.md`.


---

# Modular API routes

The former monolithic route module has been split into:

```text
app/api/routes/auth.py
app/api/routes/products.py
app/api/routes/orders.py
```

`app/api/router.py` is the shared router aggregator, and `app/main.py` includes only `api_router`.
No Alembic migration is required.
