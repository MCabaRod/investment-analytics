def _create_asset(client, **overrides):
    payload = {
        "name": "Microsoft Corporation",
        "asset_type": "stock",
        "isin": "US5949181045",
        "ticker": "MSFT",
        "exchange": "NASDAQ",
        "currency": "USD",
    }
    payload.update(overrides)
    response = client.post("/api/assets", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_and_get_asset(client):
    created = _create_asset(client)
    asset_id = created["id"]

    response = client.get(f"/api/assets/{asset_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["ticker"] == "MSFT"
    assert body["isin"] == "US5949181045"


def test_duplicate_isin_is_rejected(client):
    _create_asset(client)
    response = client.post(
        "/api/assets",
        json={
            "name": "Microsoft Corp (duplicado)",
            "asset_type": "stock",
            "isin": "US5949181045",
        },
    )
    assert response.status_code == 409


def test_search_by_partial_name_ticker_and_isin(client):
    _create_asset(client)
    _create_asset(
        client,
        name="NVIDIA Corporation",
        isin="US67066G1040",
        ticker="NVDA",
    )

    by_name = client.get("/api/assets/search", params={"q": "micro"})
    assert by_name.status_code == 200
    assert any(r["ticker"] == "MSFT" for r in by_name.json())

    by_ticker = client.get("/api/assets/search", params={"q": "NVDA"})
    assert any(r["ticker"] == "NVDA" for r in by_ticker.json())

    by_isin = client.get("/api/assets/search", params={"q": "US5949181045"})
    assert any(r["isin"] == "US5949181045" for r in by_isin.json())


def test_update_asset_marks_featured(client):
    created = _create_asset(client)
    response = client.patch(
        f"/api/assets/{created['id']}", json={"is_featured": True, "featured_order": 1}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_featured"] is True
    assert body["featured_order"] == 1


def test_list_only_featured(client):
    a = _create_asset(client)
    b = _create_asset(client, name="Apple Inc.", isin="US0378331005", ticker="AAPL")
    client.patch(f"/api/assets/{a['id']}", json={"is_featured": True, "featured_order": 2})
    client.patch(f"/api/assets/{b['id']}", json={"is_featured": True, "featured_order": 1})

    response = client.get("/api/assets", params={"featured": True})
    assert response.status_code == 200
    tickers = [r["ticker"] for r in response.json()]
    assert tickers == ["AAPL", "MSFT"]  # respeta featured_order


def test_delete_asset(client):
    created = _create_asset(client)
    response = client.delete(f"/api/assets/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/assets/{created['id']}").status_code == 404
