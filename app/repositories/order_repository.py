from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import Order, OrderItem


def add(db: Session, order: Order) -> None:
    db.add(order)


def list_by_user(db: Session, user_id: int) -> list[Order]:
    return list(
        db.scalars(
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product)
            )
            .where(Order.user_id == user_id)
            .order_by(Order.id.desc())
        )
    )
