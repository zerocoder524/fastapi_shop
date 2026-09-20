from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models import Product, StockMovement
from ..repositories import product_repository, stock_movement_repository
from ..schemas import ProductCreate, ProductUpdate


class ProductServiceError(Exception):
    """Base exception for product service failures."""


class ProductPersistenceError(ProductServiceError):
    pass


class ProductNotFoundError(ProductServiceError):
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
        db.flush()

        if product.stock_quantity > 0:
            stock_movement_repository.add(
                db,
                StockMovement(
                    product=product,
                    movement_type="initial",
                    quantity_change=product.stock_quantity,
                    balance_after=product.stock_quantity,
                    note="Initial stock",
                ),
            )

        db.commit()
        db.refresh(product)
        return product
    except SQLAlchemyError as exc:
        db.rollback()
        raise ProductPersistenceError(
            "Could not create product"
        ) from exc


def update_product(
    *,
    db: Session,
    product_id: int,
    data: ProductUpdate,
) -> Product:
    product = product_repository.get_by_id(db, product_id)

    if product is None:
        raise ProductNotFoundError("Product not found")

    updates = data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(product, field, value)

    try:
        db.commit()
        db.refresh(product)
        return product
    except SQLAlchemyError as exc:
        db.rollback()
        raise ProductPersistenceError(
            "Could not update product"
        ) from exc


def delete_product(
    *,
    db: Session,
    product_id: int,
) -> None:
    product = product_repository.get_by_id(db, product_id)

    if product is None:
        raise ProductNotFoundError("Product not found")

    product.is_active = False

    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise ProductPersistenceError(
            "Could not delete product"
        ) from exc
