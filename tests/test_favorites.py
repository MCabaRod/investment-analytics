def _create_asset(client):
    payload = {
        "name": "Microsoft Corporation",
        "asset_type": "stock",
        "isin": "US5949181045",
        "ticker": "MSFT",
        "exchange": "NASDAQ",
        "currency": "USD",
    }
    response = client.post("/api/assets", json=payload)
    return response.json()


def test_add_list_and_remove_favorite(client):
    asset = _create_asset(client)

    add_response = client.post("/api/favorites", json={"asset_id": asset["id"]})
    assert add_response.status_code == 201
    assert add_response.json()["asset"]["ticker"] == "MSFT"

    list_response = client.get("/api/favorites")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    remove_response = client.delete(f"/api/favorites/{asset['id']}")
    assert remove_response.status_code == 204
    assert client.get("/api/favorites").json() == []


def test_add_favorite_twice_is_idempotent(client):
    asset = _create_asset(client)
    client.post("/api/favorites", json={"asset_id": asset["id"]})
    client.post("/api/favorites", json={"asset_id": asset["id"]})
    assert len(client.get("/api/favorites").json()) == 1


def test_favorite_unknown_asset_returns_404(client):
    response = client.post("/api/favorites", json={"asset_id": 999})
    assert response.status_code == 404
