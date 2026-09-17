from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Product


def list_active(db: Session) -> list[Product]:
    return list(
        db.scalars(
            select(Product)
            .where(Product.is_active.is_(True))
            .order_by(Product.id)
        )
    )


def get_active_by_ids_for_update(
    db: Session,
    product_ids: list[int],
) -> list[Product]:
    """Load active products and lock their rows until COMMIT/ROLLBACK."""
    return list(
        db.scalars(
            select(Product)
            .where(
                Product.id.in_(product_ids),
                Product.is_active.is_(True),
            )
            .order_by(Product.id)
            .with_for_update()
        )
    )


def add(db: Session, product: Product) -> None:
    db.add(product)
