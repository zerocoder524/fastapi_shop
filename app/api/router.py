from fastapi import APIRouter

from .routes.auth import router as auth_router
from .routes.orders import router as orders_router
from .routes.products import router as products_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(products_router)
api_router.include_router(orders_router)
