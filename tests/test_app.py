import pytest

from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def stub_latest_news(monkeypatch):
    monkeypatch.setattr(
        "src.app.fetch_latest_market_news",
        lambda: {
            "title": "日経平均、寄り付き後に上昇",
            "source": "Google News",
            "url": "https://example.com/news",
        },
    )


def test_briefing_endpoint_returns_expected_keys():
    response = client.get("/briefing")

    assert response.status_code == 200
    data = response.json()
    assert "headline" in data
    assert "market_state" in data
    assert "fx_state" in data
    assert "news_item" in data
    assert "watchlist_status" in data
    assert "risk_alerts" in data
    assert "key_changes" in data
    assert "reasons" in data
    assert "evidence" in data
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
        lambda symbols: [
            {
                "symbol": symbol,
                "price": 2810.0,
                "change_pct": 2.4,
                "status": "strong",
            }
            for symbol in symbols
        ],
    )

    response = client.get("/briefing")

    assert response.status_code == 200
    data = response.json()
    assert data["watchlist_status"][0]["symbol"] == "7203.T"
    assert data["watchlist_status"][0]["status"] == "strong"
    assert len(data["watchlist_status"]) == 3


def test_briefing_endpoint_uses_fetched_news():
    response = client.get("/briefing")

    assert response.status_code == 200
    data = response.json()
    assert data["news_item"]["title"] == "日経平均、寄り付き後に上昇"
    assert "News: 日経平均、寄り付き後に上昇 (Google News)." in data["key_changes"]


def test_briefing_endpoint_accepts_watchlist_symbol(monkeypatch):
    monkeypatch.setattr(
        "src.app.fetch_watchlist_status",
        lambda symbols: [
            {
                "symbol": symbols[0],
                "price": 9800.0,
                "change_pct": -2.1,
                "status": "weak",
            },
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
        lambda symbols: [
            {
                "symbol": symbols[0],
                "price": 2700.0,
                "change_pct": -2.4,
                "status": "weak",
            },
            {
                "symbol": symbols[1],
                "price": 2820.0,
                "change_pct": 0.4,
                "status": "steady",
            },
            {
                "symbol": symbols[2],
                "price": 9800.0,
                "change_pct": 2.1,
                "status": "strong",
            },
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
    assert data["headline"] == "Nikkei is under pressure. yen is strong. 7203.T is weak."
    assert "7203.T is weakening versus the previous close." in data["reasons"]
    assert "6758.T is moving within a normal daily range." in data["reasons"]
    assert "9984.T is rising strongly versus the previous close." in data["reasons"]
    assert data["evidence"]
    assert data["confidence"] == "high"
