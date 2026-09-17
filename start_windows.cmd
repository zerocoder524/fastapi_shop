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
    echo Copy .env.example to .env and configure it first.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Starting FastAPI Shop...
echo Swagger: http://127.0.0.1:8000/docs
echo.
uvicorn app.main:app --reload
