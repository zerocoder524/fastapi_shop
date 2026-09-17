import jwt
from sqlalchemy.exc import SQLAlchemyError

from app import security
from app.services import auth_service, order_service, product_service


def test_root_health_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "FastAPI Shop is running",
        "docs": "/docs",
    }


def test_invalid_jwt_returns_401(client):
    response = client.get(
        "/orders/me",
        headers={"Authorization": "Bearer definitely-not-a-valid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_jwt_without_subject_returns_401(client):
    token = jwt.encode(
        {"purpose": "test"},
        security.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )

    response = client.get(
        "/orders/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_valid_jwt_for_missing_user_returns_401(client):
    token = security.create_access_token("missing@example.com")

    response = client.get(
        "/orders/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_register_database_error_returns_500(
    client,
    monkeypatch,
):
    def fail_add(db, user):
        raise SQLAlchemyError("forced registration failure")

    monkeypatch.setattr(auth_service.user_repository, "add", fail_add)

    response = client.post(
        "/auth/register",
        json={
            "email": "db-error@example.com",
            "full_name": "DB Error",
            "password": "strongpassword123",
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Could not register user"


def test_create_product_database_error_returns_500_and_rolls_back(
    client,
    auth_headers,
    monkeypatch,
):
    def fail_add(db, product):
        raise SQLAlchemyError("forced product failure")

    monkeypatch.setattr(product_service.product_repository, "add", fail_add)

    response = client.post(
        "/products",
        headers=auth_headers,
        json={
            "name": "Database failure bouquet",
            "description": "Must not be committed",
            "price": 2500,
            "stock_quantity": 4,
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Could not create product"
    assert client.get("/products").json() == []


def test_order_for_missing_product_returns_404(
    client,
    auth_headers,
):
    response = client.post(
        "/orders",
        headers=auth_headers,
        json={
            "items": [
                {
                    "product_id": 999999,
                    "quantity": 1,
                }
            ]
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == {
        "message": "Products not found or inactive",
        "product_ids": [999999],
    }


def test_order_database_error_returns_500_and_restores_stock(
    client,
    auth_headers,
    monkeypatch,
):
    product_response = client.post(
        "/products",
        headers=auth_headers,
        json={
            "name": "Rollback bouquet",
            "description": "Stock must survive a database failure",
            "price": 3900,
            "stock_quantity": 5,
        },
    )
    assert product_response.status_code == 201
    product_id = product_response.json()["id"]

    def fail_add(db, order):
        raise SQLAlchemyError("forced order failure")

    monkeypatch.setattr(order_service.order_repository, "add", fail_add)

    response = client.post(
        "/orders",
        headers=auth_headers,
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                }
            ]
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Could not create order"

    products = client.get("/products").json()
    product = next(
        item for item in products
        if item["id"] == product_id
    )
    assert product["stock_quantity"] == 5

    orders_response = client.get(
        "/orders/me",
        headers=auth_headers,
    )
    assert orders_response.status_code == 200
    assert orders_response.json() == []
