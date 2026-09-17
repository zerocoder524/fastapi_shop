# Alembic: подключение к существующей FastAPI Shop database

Проект расположен:

C:\Users\Asus\Documents\GitHub\fastapi_shop

Текущая PostgreSQL database уже содержит таблицы:

- users
- products
- orders
- order_items

и данные в них. Поэтому первая миграция является **baseline**.

## ВАЖНО

Для уже существующей базы НЕ запускайте первым:

    alembic upgrade head

Иначе initial migration попытается повторно создать существующие таблицы.

Вместо этого один раз выполните:

    alembic stamp 0001_initial

`stamp` не выполняет DDL из migration. Он создаёт/обновляет только
служебную таблицу `alembic_version` и отмечает существующую схему
как revision `0001_initial`.

## Пошагово для текущей базы

Остановить Uvicorn: Ctrl+C

Перейти в проект:

    cd /d C:\Users\Asus\Documents\GitHub\fastapi_shop

Активировать окружение:

    .venv\Scripts\activate

Обновить зависимости:

    pip install -r requirements.txt

Посмотреть текущий статус:

    alembic current

Для ещё не подключённой к Alembic базы revision обычно не будет указан.

Поставить baseline:

    alembic stamp 0001_initial

Проверить:

    alembic current

Ожидается:

    0001_initial (head)

Сверить SQLAlchemy models с реальной database:

    alembic check

Ожидается сообщение о том, что новых upgrade operations не обнаружено.

После этого:

    uvicorn app.main:app --reload

## Упрощённый вариант

Выполнить один раз:

    baseline_existing_db.cmd

Скрипт устанавливает Alembic, ставит baseline и запускает `alembic check`.

## Будущие изменения схемы

Например, после добавления поля `stock_quantity` в Product:

    alembic revision --autogenerate -m "add stock quantity to products"

Обязательно просмотреть созданный migration file.

Применить:

    alembic upgrade head

Или:

    migrate_windows.cmd

Откатить последнюю migration:

    alembic downgrade -1

История:

    alembic history

Текущая revision:

    alembic current

Проверка на незамигрированные изменения:

    alembic check

## Новая пустая database

Для новой пустой PostgreSQL database baseline ставить через `stamp` не надо.

Создайте пустую database, настройте `.env`, затем:

    alembic upgrade head

Initial migration сама создаст четыре таблицы и индексы.

## Что изменилось в приложении

Из `app/main.py` удалён:

    Base.metadata.create_all(bind=engine)

Теперь Uvicorn не меняет схему базы при запуске.
Схемой управляет только Alembic.
