import datetime


def test_create_link_returns_short_code(client):
    resp = client.post("/links", json={"long_url": "https://example.com/some/long/path"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["long_url"] == "https://example.com/some/long/path"
    assert len(body["short_code"]) > 0


def test_redirect_follows_to_long_url(client):
    create = client.post("/links", json={"long_url": "https://example.com/target"})
    short_code = create.json()["short_code"]

    resp = client.get(f"/{short_code}", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "https://example.com/target"


def test_unknown_short_code_returns_404(client):
    resp = client.get("/does-not-exist", follow_redirects=False)
    assert resp.status_code == 404


def test_custom_alias_is_honored(client):
    resp = client.post(
        "/links", json={"long_url": "https://example.com", "custom_alias": "my-link"}
    )
    assert resp.status_code == 201
    assert resp.json()["short_code"] == "my-link"


def test_duplicate_custom_alias_rejected(client):
    client.post("/links", json={"long_url": "https://example.com/a", "custom_alias": "taken"})
    resp = client.post(
        "/links", json={"long_url": "https://example.com/b", "custom_alias": "taken"}
    )
    assert resp.status_code == 409


def test_expired_link_returns_410(client):
    past = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).isoformat()
    create = client.post(
        "/links", json={"long_url": "https://example.com", "expires_at": past}
    )
    short_code = create.json()["short_code"]
    resp = client.get(f"/{short_code}", follow_redirects=False)
    assert resp.status_code == 410


def test_deactivated_link_requires_owner(client):
    client.post("/auth/register", json={"email": "alice@example.com", "password": "hunter22"})
    login = client.post(
        "/auth/login", data={"username": "alice@example.com", "password": "hunter22"}
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post(
        "/links", json={"long_url": "https://example.com"}, headers=headers
    )
    short_code = create.json()["short_code"]

    # Anonymous user cannot delete
    resp = client.delete(f"/links/{short_code}")
    assert resp.status_code == 401

    # Owner can deactivate
    resp = client.delete(f"/links/{short_code}", headers=headers)
    assert resp.status_code == 204

    redirect_resp = client.get(f"/{short_code}", follow_redirects=False)
    assert redirect_resp.status_code == 410


def test_click_is_logged_and_shows_in_analytics(client):
    create = client.post("/links", json={"long_url": "https://example.com"})
    short_code = create.json()["short_code"]

    client.get(f"/{short_code}", follow_redirects=False)
    client.get(f"/{short_code}", follow_redirects=False)

    resp = client.get(f"/links/{short_code}/analytics")
    assert resp.status_code == 200
    assert resp.json()["total_clicks"] == 2
