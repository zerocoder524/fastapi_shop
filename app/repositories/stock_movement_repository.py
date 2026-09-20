from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import StockMovement


def add(db: Session, movement: StockMovement) -> None:
    db.add(movement)


def list_by_product(
    db: Session,
    product_id: int,
) -> list[StockMovement]:
    return list(
        db.scalars(
            select(StockMovement)
            .where(StockMovement.product_id == product_id)
            .order_by(StockMovement.id.desc())
        )
    )
