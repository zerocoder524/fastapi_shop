from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models import Product
from ..repositories import product_repository
from ..schemas import ProductCreate


class ProductServiceError(Exception):
    """Base exception for product service failures."""


class ProductPersistenceError(ProductServiceError):
    pass


def list_products(*, db: Session) -> list[Product]:
    return product_repository.list_active(db)


def create_product(
    *,
    db: Session,
    data: ProductCreate,
) -> Product:
    product = Product(
        name=data.name,
        description=data.description,
        price=data.price,
        stock_quantity=data.stock_quantity,
    )

    try:
        product_repository.add(db, product)
        db.commit()
        db.refresh(product)
        return product
    except SQLAlchemyError as exc:
        db.rollback()
        raise ProductPersistenceError(
            "Could not create product"
        ) from exc
