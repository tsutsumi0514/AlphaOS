import pytest

from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def stub_external_sources(monkeypatch):
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_usd_jpy_rate", lambda: 156.2)
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_nikkei_change_pct", lambda: 1.2)
    monkeypatch.setattr(
        "src.collectors.briefing_inputs.fetch_watchlist_status",
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
    monkeypatch.setattr(
        "src.collectors.briefing_inputs.fetch_latest_market_news",
        lambda: {
            "title": "日経平均、寄り付き後に上昇",
            "source": "Google News",
            "url": "https://example.com/news",
        },
    )
    monkeypatch.setattr(
        "src.agents.chairman_ai.build_learning_summary",
        lambda: {
            "status": "insufficient",
            "sample_size": 0,
            "accuracy": None,
            "notes": ["No matched outcomes yet."],
        },
    )
    monkeypatch.setattr("src.app.record_briefing_snapshot", lambda briefing, source: None)


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
    assert "briefing_id" in data
    assert "learning_summary" in data
    assert "decision_ai" in data


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
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_usd_jpy_rate", lambda: 144.8)

    response = client.get("/briefing")

    assert response.status_code == 200
    data = response.json()
    assert data["fx_state"] == "strong yen"


def test_briefing_endpoint_uses_fetched_market_change_pct(monkeypatch):
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_nikkei_change_pct", lambda: -1.1)

    response = client.get("/briefing")

    assert response.status_code == 200
    data = response.json()
    assert data["market_state"] == "bearish"


def test_briefing_endpoint_uses_fetched_watchlist_status(monkeypatch):
    monkeypatch.setattr(
        "src.collectors.briefing_inputs.fetch_watchlist_status",
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
        "src.collectors.briefing_inputs.fetch_watchlist_status",
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
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_usd_jpy_rate", lambda: 144.0)
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_nikkei_change_pct", lambda: -1.2)
    monkeypatch.setattr(
        "src.collectors.briefing_inputs.fetch_watchlist_status",
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


def test_homepage_returns_html_briefing():
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AlphaOS Morning Briefing" in response.text
    assert "Risk Alerts" in response.text
    assert "Reasons" in response.text
    assert "Evidence" in response.text
    assert "Decision AI" in response.text
    assert "Learning" in response.text
    assert "Confidence" in response.text
    assert "Review history" in response.text


def test_homepage_survives_fetch_failures(monkeypatch):
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_usd_jpy_rate", lambda: (_ for _ in ()).throw(RuntimeError("fx down")))
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_nikkei_change_pct", lambda: (_ for _ in ()).throw(RuntimeError("market down")))
    monkeypatch.setattr(
        "src.collectors.briefing_inputs.fetch_watchlist_status",
        lambda symbols: (_ for _ in ()).throw(RuntimeError("watchlist down")),
    )
    monkeypatch.setattr(
        "src.collectors.briefing_inputs.fetch_latest_market_news",
        lambda: (_ for _ in ()).throw(RuntimeError("news down")),
    )

    response = client.get("/")

    assert response.status_code == 200
    assert "Market overview is not ready yet." in response.text
    assert "None" in response.text


def test_history_endpoint_returns_recent_records(monkeypatch):
    monkeypatch.setattr(
        "src.app.load_briefing_history",
        lambda: [
            {"briefing_id": "one", "recorded_at": "2026-07-14T00:00:00Z"},
            {"briefing_id": "two", "recorded_at": "2026-07-14T01:00:00Z"},
        ],
    )

    response = client.get("/history?limit=1")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["records"]) == 1
    assert data["records"][0]["briefing_id"] == "two"


def test_history_view_returns_html(monkeypatch):
    monkeypatch.setattr(
        "src.app.load_briefing_history",
        lambda: [
            {
                "briefing_id": "one",
                "recorded_at": "2026-07-14T00:00:00Z",
                "briefing": {
                    "headline": "alpha",
                    "market_state": "bullish",
                    "fx_state": "weak yen",
                    "confidence": "high",
                    "risk_alerts": ["risk"],
                    "key_changes": ["change"],
                    "reasons": ["reason"],
                },
            }
        ],
    )
    monkeypatch.setattr(
        "src.app.build_learning_summary",
        lambda: {
            "status": "strong",
            "sample_size": 1,
            "accuracy": 1.0,
            "weighted_accuracy": 1.0,
            "notes": ["Recent forecast accuracy is stable."],
            "periods": {"all": {"total": 1}},
        },
    )

    response = client.get("/history/view")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AlphaOS Briefing Archive" in response.text
    assert "Review history" not in response.text
    assert "Back to briefing" in response.text
    assert "alpha" in response.text


def test_outcome_endpoint_records_result(monkeypatch):
    monkeypatch.setattr("src.app.record_market_outcome", lambda briefing_id, outcome: {"briefing_id": briefing_id, "outcome": outcome})
    monkeypatch.setattr(
        "src.app.build_learning_summary",
        lambda: {"status": "strong", "sample_size": 1, "accuracy": 1.0, "notes": ["Recent forecast accuracy is stable."]},
    )

    response = client.post(
        "/outcome",
        json={
            "briefing_id": "alpha",
            "outcome": {
                "market_change_pct": 1.2,
                "usd_jpy": 156.2,
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"
    assert data["briefing_id"] == "alpha"
    assert data["learning_summary"]["status"] == "strong"


def test_learning_endpoint_returns_summary(monkeypatch):
    monkeypatch.setattr(
        "src.app.build_learning_summary",
        lambda: {
            "status": "moderate",
            "sample_size": 3,
            "accuracy": 0.67,
            "weighted_accuracy": 0.67,
            "notes": ["Recent forecast accuracy is mixed."],
            "periods": {"all": {"total": 3}},
        },
    )

    response = client.get("/learning")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "moderate"
    assert data["sample_size"] == 3
    assert "periods" in data


def test_backtest_endpoint_scores_payload():
    response = client.post(
        "/backtest",
        json={
            "history": [
                {
                    "briefing_id": "alpha",
                    "briefing": {
                        "market_state": "bullish",
                        "fx_state": "weak yen",
                        "watchlist_status": [
                            {"symbol": "7203.T", "status": "strong"}
                        ],
                    },
                }
            ],
            "outcomes": {
                "alpha": {
                    "market_change_pct": 1.2,
                    "usd_jpy": 156.2,
                    "watchlist_status": [
                        {"symbol": "7203.T", "change_pct": 2.4}
                    ],
                }
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["accuracy"] == 1.0
    assert data["results"][0]["briefing_id"] == "alpha"


def test_simulate_endpoint_returns_result(monkeypatch):
    monkeypatch.setattr(
        "src.app.run_replay_simulation",
        lambda lookback_trading_days, symbols, calibrate=True: {
            "mode": "replay",
            "sample_size": 2,
            "summary": {"total": 2, "accuracy": 1.0, "weighted_accuracy": 1.0},
            "results": [
                {"briefing_date": "2026-07-10", "outcome_date": "2026-07-11", "result": {"accuracy": 1.0}},
                {"briefing_date": "2026-07-11", "outcome_date": "2026-07-12", "result": {"accuracy": 1.0}},
            ],
            "notes": ["ok"],
        },
    )

    response = client.post("/simulate", json={"lookback_trading_days": 2})

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "replay"
    assert data["sample_size"] == 2
