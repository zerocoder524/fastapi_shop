@echo off
setlocal
cd /d C:\Users\Asus\Documents\GitHub\fastapi_shop

if not exist .venv\Scripts\activate.bat (
    echo Virtual environment not found.
    echo Run setup_windows.cmd first.
    pause
    exit /b 1
)

if not exist .env (
    echo .env file not found.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Installing/updating dependencies...
pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo IMPORTANT:
echo This command is for the EXISTING database whose four tables already exist.
echo It DOES NOT run 0001_initial. It only records the baseline revision.
echo.

alembic stamp 0001_initial
if errorlevel 1 goto :error

echo.
echo Current Alembic revision:
alembic current
if errorlevel 1 goto :error

echo.
echo Checking ORM metadata against the current database...
alembic check
if errorlevel 1 goto :error

echo.
echo Baseline completed successfully.
echo Existing users, products, orders and order_items were not recreated.
pause
exit /b 0

:error
echo.
echo Alembic baseline failed. Review the message above.
pause
exit /b 1
