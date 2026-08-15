def test_root_returns_disclaimer(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "disclaimer" in body
    assert "no constituye asesoramiento" in body["disclaimer"].lower()


def test_health_endpoint_reports_status(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert "database" in body
    assert "checked_at" in body
