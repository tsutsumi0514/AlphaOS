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
    assert "reasons" in data
    assert "confidence" in data


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
    assert "Nikkei momentum is positive today." in data["key_changes"]


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


def test_briefing_endpoint_uses_fetched_watchlist_status(monkeypatch):
    monkeypatch.setattr(
        "src.app.fetch_watchlist_status",
        lambda symbol: [
            {
                "symbol": symbol,
                "price": 2810.0,
                "change_pct": 2.4,
                "status": "strong",
            }
        ],
    )

    response = client.get("/briefing")

    assert response.status_code == 200
    data = response.json()
    assert data["watchlist_status"][0]["symbol"] == "7203.T"
    assert data["watchlist_status"][0]["status"] == "strong"


def test_briefing_endpoint_accepts_watchlist_symbol(monkeypatch):
    monkeypatch.setattr(
        "src.app.fetch_watchlist_status",
        lambda symbol: [
            {
                "symbol": symbol,
                "price": 9800.0,
                "change_pct": -2.1,
                "status": "weak",
            }
        ],
    )

    response = client.get("/briefing?watchlist_symbol=9984.T")

    assert response.status_code == 200
    data = response.json()
    assert data["watchlist_status"][0]["symbol"] == "9984.T"
    assert data["watchlist_status"][0]["status"] == "weak"
    assert "9984.T is weakening on the watchlist." in data["key_changes"]


def test_briefing_endpoint_generates_risk_alerts(monkeypatch):
    monkeypatch.setattr("src.app.fetch_usd_jpy_rate", lambda: 144.0)
    monkeypatch.setattr("src.app.fetch_nikkei_change_pct", lambda: -1.2)
    monkeypatch.setattr(
        "src.app.fetch_watchlist_status",
        lambda symbol: [
            {
                "symbol": symbol,
                "price": 2700.0,
                "change_pct": -2.4,
                "status": "weak",
            }
        ],
    )

    response = client.get("/briefing")

    assert response.status_code == 200
    data = response.json()
    assert "Market tone is bearish. Keep new positions small." in data["risk_alerts"]
    assert "Strong yen may pressure export-related names." in data["risk_alerts"]
    assert "Both market and currency conditions are risk-off." in data["risk_alerts"]
    assert "Nikkei day-over-day change is negative." in data["reasons"]
    assert "USD/JPY is in a strong-yen range." in data["reasons"]
    assert data["confidence"] == "high"
