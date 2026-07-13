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


def test_briefing_endpoint_derives_fx_state_from_usd_jpy():
    response = client.get("/briefing?usd_jpy=156.2")

    assert response.status_code == 200
    data = response.json()
    assert data["fx_state"] == "weak yen"


def test_briefing_endpoint_derives_market_state_from_change_pct():
    response = client.get("/briefing?market_change_pct=1.2")

    assert response.status_code == 200
    data = response.json()
    assert data["market_state"] == "bullish"


def test_briefing_endpoint_uses_fetched_usd_jpy(monkeypatch):
    monkeypatch.setattr("src.app.fetch_usd_jpy_rate", lambda: 144.8)

    response = client.get("/briefing")

    assert response.status_code == 200
    data = response.json()
    assert data["fx_state"] == "strong yen"


def test_briefing_endpoint_uses_fetched_market_change_pct(monkeypatch):
    monkeypatch.setattr("src.app.fetch_nikkei_change_pct", lambda: -1.1)

    response = client.get("/briefing")

    assert response.status_code == 200
    data = response.json()
    assert data["market_state"] == "bearish"
