import pytest

from app.models import Product, StockMovement, User

from .conftest import login_headers, register_user


def create_product(client, admin_headers, *, stock_quantity: int = 5) -> dict:
    response = client.post(
        "/products",
        headers=admin_headers,
        json={
            "name": "Access control bouquet",
            "description": "Admin access test product",
            "price": 3000,
            "stock_quantity": stock_quantity,
        },
    )
    assert response.status_code == 201
    return response.json()


ADMIN_ENDPOINTS = [
    pytest.param(
        "post",
        "/products",
        {"name": "Forbidden bouquet", "price": 1000, "stock_quantity": 1},
        id="create-product",
    ),
    pytest.param(
        "patch",
        "/products/{product_id}",
        {"price": 1},
        id="update-product",
    ),
    pytest.param(
        "delete",
        "/products/{product_id}",
        None,
        id="delete-product",
    ),
    pytest.param(
        "post",
        "/products/{product_id}/stock/replenish",
        {"quantity": 5},
        id="replenish-stock",
    ),
    pytest.param(
        "post",
        "/products/{product_id}/stock/adjust",
        {"actual_quantity": 0, "note": "Forbidden count"},
        id="adjust-stock",
    ),
    pytest.param(
        "get",
        "/products/{product_id}/stock/movements",
        None,
        id="stock-movements",
    ),
]


@pytest.mark.parametrize(("method", "path", "payload"), ADMIN_ENDPOINTS)
def test_regular_user_gets_403_on_admin_endpoints(
    client,
    auth_headers,
    admin_headers,
    db_session,
    method,
    path,
    payload,
):
    product = create_product(client, admin_headers)
    url = path.format(product_id=product["id"])

    kwargs = {"headers": auth_headers}
    if payload is not None:
        kwargs["json"] = payload

    response = client.request(method.upper(), url, **kwargs)

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"

    # The forbidden request must not change anything.
    db_session.expire_all()
    assert db_session.query(Product).count() == 1
    stored = db_session.get(Product, product["id"])
    assert stored.is_active is True
    assert stored.price == 3000
    assert stored.stock_quantity == 5
    assert db_session.query(StockMovement).count() == 1


@pytest.mark.parametrize(("method", "path", "payload"), ADMIN_ENDPOINTS)
def test_admin_endpoints_require_authentication(
    client,
    admin_headers,
    method,
    path,
    payload,
):
    product = create_product(client, admin_headers)
    url = path.format(product_id=product["id"])

    kwargs = {}
    if payload is not None:
        kwargs["json"] = payload

    response = client.request(method.upper(), url, **kwargs)

    assert response.status_code == 401


def test_admin_can_manage_products_and_stock(client, admin_headers):
    product = create_product(client, admin_headers, stock_quantity=5)
    product_url = f"/products/{product['id']}"

    update_response = client.patch(
        product_url,
        headers=admin_headers,
        json={"price": 3500},
    )
    assert update_response.status_code == 200
    assert update_response.json()["price"] == "3500.00"

    replenish_response = client.post(
        f"{product_url}/stock/replenish",
        headers=admin_headers,
        json={"quantity": 3},
    )
    assert replenish_response.status_code == 201
    assert replenish_response.json()["balance_after"] == 8

    adjust_response = client.post(
        f"{product_url}/stock/adjust",
        headers=admin_headers,
        json={"actual_quantity": 6, "note": "Inventory count"},
    )
    assert adjust_response.status_code == 201
    assert adjust_response.json()["balance_after"] == 6

    movements_response = client.get(
        f"{product_url}/stock/movements",
        headers=admin_headers,
    )
    assert movements_response.status_code == 200
    assert [m["movement_type"] for m in movements_response.json()] == [
        "adjustment",
        "replenishment",
        "initial",
    ]

    delete_response = client.delete(product_url, headers=admin_headers)
    assert delete_response.status_code == 204


def test_new_user_is_not_admin_by_default(client, db_session):
    register_user(client, "regular@example.com")

    user = db_session.query(User).filter_by(email="regular@example.com").one()
    assert user.is_admin is False


def test_registration_cannot_grant_admin_privileges(client, db_session):
    response = client.post(
        "/auth/register",
        json={
            "email": "sneaky@example.com",
            "full_name": "Sneaky User",
            "password": "strongpassword123",
            "is_admin": True,
        },
    )
    assert response.status_code == 201

    user = db_session.query(User).filter_by(email="sneaky@example.com").one()
    assert user.is_admin is False

    headers = login_headers(client, "sneaky@example.com")
    forbidden = client.post(
        "/products",
        headers=headers,
        json={"name": "Sneaky bouquet", "price": 1000},
    )
    assert forbidden.status_code == 403


def test_public_product_list_is_available_to_everyone(
    client,
    auth_headers,
    admin_headers,
):
    product = create_product(client, admin_headers)

    for headers in ({}, auth_headers, admin_headers):
        response = client.get("/products", headers=headers)
        assert response.status_code == 200
        assert [p["id"] for p in response.json()] == [product["id"]]


def test_regular_user_can_order_and_sees_only_own_orders(
    client,
    auth_headers,
    admin_headers,
):
    product = create_product(client, admin_headers, stock_quantity=10)

    register_user(client, "other@example.com")
    other_headers = login_headers(client, "other@example.com")

    own_order = client.post(
        "/orders",
        headers=auth_headers,
        json={"items": [{"product_id": product["id"], "quantity": 1}]},
    )
    assert own_order.status_code == 201

    other_order = client.post(
        "/orders",
        headers=other_headers,
        json={"items": [{"product_id": product["id"], "quantity": 2}]},
    )
    assert other_order.status_code == 201

    own_orders = client.get("/orders/me", headers=auth_headers)
    assert own_orders.status_code == 200
    assert [o["id"] for o in own_orders.json()] == [own_order.json()["id"]]

    other_orders = client.get("/orders/me", headers=other_headers)
    assert other_orders.status_code == 200
    assert [o["id"] for o in other_orders.json()] == [other_order.json()["id"]]
