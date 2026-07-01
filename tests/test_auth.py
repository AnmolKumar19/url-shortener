def test_register_new_user(client):
    resp = client.post(
        "/auth/register", json={"email": "alice@example.com", "password": "hunter22"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert "hashed_password" not in body  # never leak the hash


def test_cannot_register_duplicate_email(client):
    client.post("/auth/register", json={"email": "alice@example.com", "password": "hunter22"})
    resp = client.post(
        "/auth/register", json={"email": "alice@example.com", "password": "hunter22"}
    )
    assert resp.status_code == 400


def test_password_too_short_rejected(client):
    resp = client.post("/auth/register", json={"email": "bob@example.com", "password": "short"})
    assert resp.status_code == 422


def test_login_success_returns_token(client):
    client.post("/auth/register", json={"email": "alice@example.com", "password": "hunter22"})
    resp = client.post(
        "/auth/login", data={"username": "alice@example.com", "password": "hunter22"}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password_rejected(client):
    client.post("/auth/register", json={"email": "alice@example.com", "password": "hunter22"})
    resp = client.post(
        "/auth/login", data={"username": "alice@example.com", "password": "wrongpass"}
    )
    assert resp.status_code == 401
