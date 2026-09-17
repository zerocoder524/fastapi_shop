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
