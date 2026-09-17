from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models import Order, OrderItem
from ..repositories import order_repository, product_repository
from ..schemas import OrderCreate


class OrderServiceError(Exception):
    """Base exception for order business-logic failures."""


class DuplicateProductError(OrderServiceError):
    pass


class ProductsUnavailableError(OrderServiceError):
    def __init__(self, product_ids: list[int]) -> None:
        self.product_ids = product_ids
        super().__init__(f"Products not found or inactive: {product_ids}")


class InsufficientStockError(OrderServiceError):
    def __init__(self, items: list[dict[str, int | str]]) -> None:
        self.items = items
        super().__init__("Insufficient stock")


class OrderPersistenceError(OrderServiceError):
    pass


def create_order(
    *,
    db: Session,
    user_id: int,
    data: OrderCreate,
) -> Order:
    """Create an order and reduce stock atomically."""

    product_ids = [item.product_id for item in data.items]

    if len(product_ids) != len(set(product_ids)):
        raise DuplicateProductError(
            "Each product may appear only once in an order"
        )

    try:
        products = product_repository.get_active_by_ids_for_update(
            db,
            product_ids,
        )
        products_by_id = {product.id: product for product in products}

        missing_ids = [
            product_id
            for product_id in product_ids
            if product_id not in products_by_id
        ]
        if missing_ids:
            raise ProductsUnavailableError(missing_ids)

        shortages: list[dict[str, int | str]] = []
        for item in data.items:
            product = products_by_id[item.product_id]
            if product.stock_quantity < item.quantity:
                shortages.append(
                    {
                        "product_id": product.id,
                        "name": product.name,
                        "requested": item.quantity,
                        "available": product.stock_quantity,
                    }
                )

        if shortages:
            raise InsufficientStockError(shortages)

        order = Order(user_id=user_id)

        for item in data.items:
            product = products_by_id[item.product_id]
            product.stock_quantity -= item.quantity

            order.items.append(
                OrderItem(
                    product=product,
                    quantity=item.quantity,
                    unit_price=product.price,
                )
            )

        order_repository.add(db, order)
        db.commit()
        return order

    except OrderServiceError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise OrderPersistenceError("Could not create order") from exc
    except Exception:
        db.rollback()
        raise


def list_orders_for_user(
    *,
    db: Session,
    user_id: int,
) -> list[Order]:
    return order_repository.list_by_user(db, user_id)
