@echo off
setlocal
cd /d C:\Users\Asus\Documents\GitHub\fastapi_shop

echo ==========================================
echo FastAPI Shop - initial Windows setup
echo ==========================================

if not exist .venv (
    echo [1/4] Creating virtual environment...
    py -3.12 -m venv .venv
) else (
    echo [1/4] Virtual environment already exists.
)

echo [2/4] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [3/4] Upgrading pip...
python -m pip install --upgrade pip

echo [4/4] Installing dependencies...
pip install -r requirements.txt

if not exist .env (
    copy .env.example .env >nul
    echo.
    echo Created .env from .env.example
    echo IMPORTANT: edit .env and set PostgreSQL password and SECRET_KEY.
) else (
    echo.
    echo .env already exists.
)

echo.
echo Setup complete.
echo 1. Create PostgreSQL database fastapi_shop
echo 2. Edit .env
echo 3. Run start_windows.cmd
echo.
pause
