from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...models import StockMovement, User
from ...schemas import StockAdjustment, StockMovementRead, StockReplenish
from ...security import get_current_user
from ...services.stock_service import (
    StockNoAdjustmentNeededError,
    StockPersistenceError,
    StockProductNotFoundError,
    adjust_stock,
    list_stock_movements,
    replenish_stock,
)

router = APIRouter(prefix="/products", tags=["stock"])


@router.post(
    "/{product_id}/stock/replenish",
    response_model=StockMovementRead,
    status_code=status.HTTP_201_CREATED,
)
def replenish_product_stock(
    product_id: int,
    data: StockReplenish,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StockMovement:
    try:
        return replenish_stock(
            db=db,
            product_id=product_id,
            data=data,
        )
    except StockProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except StockPersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not replenish stock",
        ) from exc


@router.post(
    "/{product_id}/stock/adjust",
    response_model=StockMovementRead,
    status_code=status.HTTP_201_CREATED,
)
def adjust_product_stock(
    product_id: int,
    data: StockAdjustment,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StockMovement:
    try:
        return adjust_stock(
            db=db,
            product_id=product_id,
            data=data,
        )
    except StockProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except StockNoAdjustmentNeededError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except StockPersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not adjust stock",
        ) from exc


@router.get(
    "/{product_id}/stock/movements",
    response_model=list[StockMovementRead],
)
def product_stock_movements(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[StockMovement]:
    try:
        return list_stock_movements(
            db=db,
            product_id=product_id,
        )
    except StockProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
