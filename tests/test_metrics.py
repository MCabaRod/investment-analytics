import datetime as dt
from decimal import Decimal

from app.models.price_history import PriceHistory


def _create_asset(client):
    payload = {
        "name": "Microsoft Corporation",
        "asset_type": "stock",
        "isin": "US5949181045",
        "ticker": "MSFT",
        "exchange": "NASDAQ",
        "currency": "USD",
    }
    return client.post("/api/assets", json=payload).json()


def test_metrics_without_history_returns_nulls_not_errors(client):
    asset = _create_asset(client)
    response = client.get(f"/api/assets/{asset['id']}/metrics")
    assert response.status_code == 200
    body = response.json()
    assert body["data_points"] == 0
    assert body["ytd_return"] is None
    assert body["note"] is not None


def test_metrics_with_history_computes_returns_and_risk(client, db_session):
    asset = _create_asset(client)

    base_date = dt.date(2025, 1, 1)
    for i in range(60):
        db_session.add(
            PriceHistory(
                asset_id=asset["id"],
                date=base_date + dt.timedelta(days=i),
                close=Decimal(100 + i),
                source="test",
                retrieved_at=dt.datetime.now(dt.timezone.utc),
            )
        )
    db_session.commit()

    response = client.get(f"/api/assets/{asset['id']}/metrics")
    assert response.status_code == 200
    body = response.json()
    assert body["data_points"] == 60
    assert body["return_since_inception"] is not None
    assert body["volatility_annualized"] is not None
    assert body["max_drawdown"] is not None
    assert body["risk_free_rate_used"] == 0.02
