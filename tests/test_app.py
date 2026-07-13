from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


def test_briefing_endpoint_returns_expected_keys():
    response = client.get("/briefing")

    assert response.status_code == 200
    data = response.json()
    assert "market_state" in data
    assert "fx_state" in data
    assert "watchlist_status" in data
    assert "risk_alerts" in data
    assert "key_changes" in data
