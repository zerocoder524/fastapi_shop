from app.models import Product


def test_products_list_is_public_and_initially_empty(client):
    response = client.get("/products")

    assert response.status_code == 200
    assert response.json() == []


def test_create_product_requires_authentication(client):
    response = client.post(
        "/products",
        json={
            "name": "Protected bouquet",
            "description": "Authentication required",
            "price": 1000,
            "stock_quantity": 5,
        },
    )

    assert response.status_code == 401


def test_create_and_list_product(client, auth_headers):
    create_response = client.post(
        "/products",
        headers=auth_headers,
        json={
            "name": "Букет красных роз",
            "description": "15 красных роз",
            "price": 3900,
            "stock_quantity": 12,
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "Букет красных роз"
    assert created["stock_quantity"] == 12
    assert created["is_active"] is True

    list_response = client.get("/products")
    assert list_response.status_code == 200

    products = list_response.json()
    assert len(products) == 1
    assert products[0]["id"] == created["id"]
    assert products[0]["stock_quantity"] == 12


def test_update_product(client, auth_headers):
    created_response = client.post(
        "/products",
        headers=auth_headers,
        json={
            "name": "Update bouquet",
            "description": "Before update",
            "price": 2000,
            "stock_quantity": 10,
        },
    )

    assert created_response.status_code == 201
    created = created_response.json()

    response = client.patch(
        f"/products/{created['id']}",
        headers=auth_headers,
        json={
            "price": 2500,
        },
    )

    assert response.status_code == 200

    product = response.json()
    assert product["id"] == created["id"]
    assert product["name"] == "Update bouquet"
    assert product["description"] == "Before update"
    assert product["price"] == "2500.00"
    assert product["stock_quantity"] == 10
    assert product["is_active"] is True


def test_update_missing_product_returns_404(
    client,
    auth_headers,
):
    response = client.patch(
        "/products/999999",
        headers=auth_headers,
        json={
            "price": 2500,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_update_product_requires_authentication(client):
    response = client.patch(
        "/products/1",
        json={
            "price": 2500,
        },
    )

    assert response.status_code == 401


def test_soft_delete_product(
    client,
    auth_headers,
    db_session,
):
    created_response = client.post(
        "/products",
        headers=auth_headers,
        json={
            "name": "Delete bouquet",
            "description": "Soft delete test",
            "price": 3000,
            "stock_quantity": 7,
        },
    )

    assert created_response.status_code == 201
    created = created_response.json()

    response = client.delete(
        f"/products/{created['id']}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    products_response = client.get("/products")
    assert products_response.status_code == 200

    products = products_response.json()
    assert all(
        product["id"] != created["id"]
        for product in products
    )

    db_session.expire_all()

    stored_product = db_session.get(
        Product,
        created["id"],
    )

    assert stored_product is not None
    assert stored_product.is_active is False
    assert stored_product.stock_quantity == 7


def test_delete_missing_product_returns_404(
    client,
    auth_headers,
):
    response = client.delete(
        "/products/999999",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_delete_product_requires_authentication(client):
    response = client.delete("/products/1")

    assert response.status_code == 401
