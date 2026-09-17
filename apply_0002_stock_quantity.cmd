@echo off
setlocal
cd /d C:\Users\Asus\Documents\GitHub\fastapi_shop

if not exist .venv\Scripts\activate.bat (
    echo Virtual environment not found.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Current revision:
alembic current
if errorlevel 1 goto :error

echo.
echo Applying migration 0002_add_stock_quantity...
alembic upgrade head
if errorlevel 1 goto :error

echo.
echo New revision:
alembic current
if errorlevel 1 goto :error

echo.
echo Checking models vs database:
alembic check
if errorlevel 1 goto :error

echo.
echo Migration 0002 completed successfully.
pause
exit /b 0

:error
echo.
echo Migration failed. Review the output above.
pause
exit /b 1
