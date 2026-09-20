from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models import StockMovement
from ..repositories import product_repository, stock_movement_repository
from ..schemas import StockAdjustment, StockReplenish


class StockServiceError(Exception):
    """Base exception for stock business-logic failures."""


class StockProductNotFoundError(StockServiceError):
    pass


class StockPersistenceError(StockServiceError):
    pass


class StockNoAdjustmentNeededError(StockServiceError):
    pass


def replenish_stock(
    *,
    db: Session,
    product_id: int,
    data: StockReplenish,
) -> StockMovement:
    """Increase stock and write an audit movement in one transaction."""

    try:
        product = product_repository.get_active_by_id_for_update(
            db,
            product_id,
        )

        if product is None:
            raise StockProductNotFoundError("Product not found or inactive")

        product.stock_quantity += data.quantity

        movement = StockMovement(
            product=product,
            movement_type="replenishment",
            quantity_change=data.quantity,
            balance_after=product.stock_quantity,
            note=data.note,
        )
        stock_movement_repository.add(db, movement)

        db.commit()
        db.refresh(movement)
        return movement

    except StockServiceError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise StockPersistenceError(
            "Could not replenish stock"
        ) from exc


def adjust_stock(
    *,
    db: Session,
    product_id: int,
    data: StockAdjustment,
) -> StockMovement:
    """Set stock to the counted quantity and record the discrepancy atomically."""

    try:
        product = product_repository.get_active_by_id_for_update(
            db,
            product_id,
        )

        if product is None:
            raise StockProductNotFoundError("Product not found or inactive")

        quantity_change = data.actual_quantity - product.stock_quantity

        if quantity_change == 0:
            raise StockNoAdjustmentNeededError(
                "Stock already matches actual quantity"
            )

        product.stock_quantity = data.actual_quantity

        movement = StockMovement(
            product=product,
            movement_type="adjustment",
            quantity_change=quantity_change,
            balance_after=product.stock_quantity,
            note=data.note,
        )
        stock_movement_repository.add(db, movement)

        db.commit()
        db.refresh(movement)
        return movement

    except StockServiceError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise StockPersistenceError(
            "Could not adjust stock"
        ) from exc


def list_stock_movements(
    *,
    db: Session,
    product_id: int,
) -> list[StockMovement]:
    product = product_repository.get_by_id(db, product_id)

    if product is None:
        raise StockProductNotFoundError("Product not found")

    return stock_movement_repository.list_by_product(db, product_id)
