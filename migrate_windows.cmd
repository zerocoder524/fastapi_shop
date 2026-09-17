@echo off
setlocal
cd /d C:\Users\Asus\Documents\GitHub\fastapi_shop

if not exist .venv\Scripts\activate.bat (
    echo Virtual environment not found.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

alembic upgrade head
if errorlevel 1 (
    echo Migration failed.
    pause
    exit /b 1
)

alembic current
pause
