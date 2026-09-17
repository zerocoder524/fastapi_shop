def create_product(
    client,
    auth_headers,
    *,
    name: str,
    stock_quantity: int,
    price: int = 3900,
) -> dict:
    response = client.post(
        "/products",
        headers=auth_headers,
        json={
            "name": name,
            "description": f"Test product: {name}",
            "price": price,
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


def test_successful_order_reduces_stock_and_appears_in_my_orders(
    client,
    auth_headers,
):
    product = create_product(
        client,
        auth_headers,
        name="Букет красных роз",
        stock_quantity=12,
    )

    order_response = client.post(
        "/orders",
        headers=auth_headers,
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 2,
                }
            ]
        },
    )

    assert order_response.status_code == 201
    order = order_response.json()
    assert order["status"] == "new"
    assert order["total"] == "7800.00"
    assert order["items"][0]["quantity"] == 2

    product_after = product_by_id(client, product["id"])
    assert product_after["stock_quantity"] == 10

    orders_response = client.get(
        "/orders/me",
        headers=auth_headers,
    )
    assert orders_response.status_code == 200

    orders = orders_response.json()
    assert len(orders) == 1
    assert orders[0]["id"] == order["id"]


def test_zero_stock_returns_409_and_does_not_create_order(
    client,
    auth_headers,
):
    product = create_product(
        client,
        auth_headers,
        name="Букет белых роз",
        stock_quantity=0,
        price=3500,
    )

    response = client.post(
        "/orders",
        headers=auth_headers,
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                }
            ]
        },
    )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["message"] == "Insufficient stock"
    assert detail["items"][0]["available"] == 0

    orders_response = client.get(
        "/orders/me",
        headers=auth_headers,
    )
    assert orders_response.status_code == 200
    assert orders_response.json() == []


def test_quantity_over_stock_returns_409_and_preserves_stock(
    client,
    auth_headers,
):
    product = create_product(
        client,
        auth_headers,
        name="Limited bouquet",
        stock_quantity=10,
    )

    response = client.post(
        "/orders",
        headers=auth_headers,
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 11,
                }
            ]
        },
    )

    assert response.status_code == 409
    assert product_by_id(client, product["id"])["stock_quantity"] == 10


def test_mixed_order_is_atomic_when_one_product_has_no_stock(
    client,
    auth_headers,
):
    unavailable = create_product(
        client,
        auth_headers,
        name="Unavailable bouquet",
        stock_quantity=0,
        price=3500,
    )
    available = create_product(
        client,
        auth_headers,
        name="Available bouquet",
        stock_quantity=10,
        price=3900,
    )

    response = client.post(
        "/orders",
        headers=auth_headers,
        json={
            "items": [
                {
                    "product_id": unavailable["id"],
                    "quantity": 1,
                },
                {
                    "product_id": available["id"],
                    "quantity": 1,
                },
            ]
        },
    )

    assert response.status_code == 409
    assert product_by_id(client, unavailable["id"])["stock_quantity"] == 0
    assert product_by_id(client, available["id"])["stock_quantity"] == 10

    orders_response = client.get(
        "/orders/me",
        headers=auth_headers,
    )
    assert orders_response.status_code == 200
    assert orders_response.json() == []


def test_duplicate_product_in_one_order_returns_400(
    client,
    auth_headers,
):
    product = create_product(
        client,
        auth_headers,
        name="Duplicate test bouquet",
        stock_quantity=10,
    )

    response = client.post(
        "/orders",
        headers=auth_headers,
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                },
                {
                    "product_id": product["id"],
                    "quantity": 2,
                },
            ]
        },
    )

    assert response.status_code == 400
    assert product_by_id(client, product["id"])["stock_quantity"] == 10
