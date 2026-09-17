def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "new@example.com",
            "full_name": "New User",
            "password": "strongpassword123",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["full_name"] == "New User"
    assert "hashed_password" not in body


def test_duplicate_registration_returns_409(client):
    payload = {
        "email": "duplicate@example.com",
        "full_name": "Duplicate User",
        "password": "strongpassword123",
    }

    assert client.post("/auth/register", json=payload).status_code == 201
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "User with this email already exists"


def test_login_returns_bearer_token(client):
    client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "full_name": "Login User",
            "password": "strongpassword123",
        },
    )

    response = client.post(
        "/auth/token",
        data={
            "username": "login@example.com",
            "password": "strongpassword123",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


def test_login_with_wrong_password_returns_401(client):
    client.post(
        "/auth/register",
        json={
            "email": "wrong-password@example.com",
            "full_name": "Wrong Password",
            "password": "strongpassword123",
        },
    )

    response = client.post(
        "/auth/token",
        data={
            "username": "wrong-password@example.com",
            "password": "incorrect-password",
        },
    )

    assert response.status_code == 401
