from sqlalchemy.exc import SQLAlchemyError

from app.services import stock_service


def create_product(
    client,
    auth_headers,
    *,
    name: str = "Stock bouquet",
    stock_quantity: int = 0,
) -> dict:
    response = client.post(
        "/products",
        headers=auth_headers,
        json={
            "name": name,
            "description": "Stock test product",
            "price": 3000,
            "stock_quantity": stock_quantity,
        },
    )
    assert response.status_code == 201
    return response.json()


def product_by_id(client, product_id: int) -> dict:
    response = client.get("/products")
    assert response.status_code == 200
    return next(
        product
        for product in response.json()
        if product["id"] == product_id
    )


def test_replenish_stock_requires_authentication(client):
    response = client.post(
        "/products/1/stock/replenish",
        json={"quantity": 5},
    )

    assert response.status_code == 401


def test_replenish_stock_increases_balance_and_records_movement(
    client,
    auth_headers,
):
    product = create_product(
        client,
        auth_headers,
        stock_quantity=5,
    )

    response = client.post(
        f"/products/{product['id']}/stock/replenish",
        headers=auth_headers,
        json={
            "quantity": 7,
            "note": "Supplier delivery",
        },
    )

    assert response.status_code == 201
    movement = response.json()
    assert movement["product_id"] == product["id"]
    assert movement["order_id"] is None
    assert movement["movement_type"] == "replenishment"
    assert movement["quantity_change"] == 7
    assert movement["balance_after"] == 12
    assert movement["note"] == "Supplier delivery"

    product_after = product_by_id(client, product["id"])
    assert product_after["stock_quantity"] == 12

    history_response = client.get(
        f"/products/{product['id']}/stock/movements",
        headers=auth_headers,
    )
    assert history_response.status_code == 200

    history = history_response.json()
    assert len(history) == 2
    assert history[0]["movement_type"] == "replenishment"
    assert history[0]["quantity_change"] == 7
    assert history[0]["balance_after"] == 12
    assert history[1]["movement_type"] == "initial"
    assert history[1]["quantity_change"] == 5
    assert history[1]["balance_after"] == 5


def test_product_patch_rejects_direct_stock_change(
    client,
    auth_headers,
):
    product = create_product(
        client,
        auth_headers,
        stock_quantity=5,
    )

    response = client.patch(
        f"/products/{product['id']}",
        headers=auth_headers,
        json={"stock_quantity": 99},
    )

    assert response.status_code == 422
    assert product_by_id(client, product["id"])["stock_quantity"] == 5


def test_replenish_quantity_must_be_positive(
    client,
    auth_headers,
):
    product = create_product(client, auth_headers)

    response = client.post(
        f"/products/{product['id']}/stock/replenish",
        headers=auth_headers,
        json={"quantity": 0},
    )

    assert response.status_code == 422


def test_replenish_missing_product_returns_404(
    client,
    auth_headers,
):
    response = client.post(
        "/products/999999/stock/replenish",
        headers=auth_headers,
        json={"quantity": 5},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found or inactive"


def test_replenish_inactive_product_returns_404(
    client,
    auth_headers,
):
    product = create_product(client, auth_headers)

    delete_response = client.delete(
        f"/products/{product['id']}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204

    response = client.post(
        f"/products/{product['id']}/stock/replenish",
        headers=auth_headers,
        json={"quantity": 5},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found or inactive"


def test_stock_movements_require_authentication(
    client,
    auth_headers,
):
    product = create_product(client, auth_headers)

    response = client.get(
        f"/products/{product['id']}/stock/movements",
    )

    assert response.status_code == 401


def test_stock_movements_missing_product_returns_404(
    client,
    auth_headers,
):
    response = client.get(
        "/products/999999/stock/movements",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_order_records_negative_stock_movement(
    client,
    auth_headers,
):
    product = create_product(
        client,
        auth_headers,
        stock_quantity=10,
    )

    order_response = client.post(
        "/orders",
        headers=auth_headers,
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 3,
                }
            ]
        },
    )
    assert order_response.status_code == 201
    order = order_response.json()

    history_response = client.get(
        f"/products/{product['id']}/stock/movements",
        headers=auth_headers,
    )
    assert history_response.status_code == 200

    history = history_response.json()
    order_movement = next(
        movement
        for movement in history
        if movement["movement_type"] == "order"
    )

    assert order_movement["order_id"] == order["id"]
    assert order_movement["quantity_change"] == -3
    assert order_movement["balance_after"] == 7


def test_replenish_database_error_rolls_back_stock(
    client,
    auth_headers,
    monkeypatch,
):
    product = create_product(
        client,
        auth_headers,
        stock_quantity=0,
    )

    def fail_add(db, movement):
        raise SQLAlchemyError("forced stock movement failure")

    monkeypatch.setattr(
        stock_service.stock_movement_repository,
        "add",
        fail_add,
    )

    response = client.post(
        f"/products/{product['id']}/stock/replenish",
        headers=auth_headers,
        json={"quantity": 4},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Could not replenish stock"
    assert product_by_id(client, product["id"])["stock_quantity"] == 0
