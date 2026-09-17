from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...models import Order, User
from ...schemas import OrderCreate, OrderRead
from ...security import get_current_user
from ...services.order_service import (
    DuplicateProductError,
    InsufficientStockError,
    OrderPersistenceError,
    ProductsUnavailableError,
    create_order as create_order_service,
    list_orders_for_user,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    data: OrderCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Order:
    try:
        return create_order_service(db=db, user_id=current_user.id, data=data)
    except DuplicateProductError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ProductsUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Products not found or inactive", "product_ids": exc.product_ids},
        ) from exc
    except InsufficientStockError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Insufficient stock", "items": exc.items},
        ) from exc
    except OrderPersistenceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create order") from exc


@router.get("/me", response_model=list[OrderRead])
def my_orders(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Order]:
    return list_orders_for_user(db=db, user_id=current_user.id)
