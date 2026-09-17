from fastapi import FastAPI

from .api.router import api_router

app = FastAPI(
    title="FastAPI Shop",
    version="0.3.0",
    description="FastAPI Shop: PostgreSQL, SQLAlchemy, JWT and Alembic migrations.",
)

app.include_router(api_router)


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {
        "message": "FastAPI Shop is running",
        "docs": "/docs",
    }
