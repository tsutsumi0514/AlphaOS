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
            "weighted_accuracy": None,
            "notes": ["No matched outcomes yet."],
            "periods": {"all": {"total": 0}},
        },
    )
    monkeypatch.setattr("src.app.record_briefing_snapshot", lambda briefing, source: None)
    monkeypatch.setattr("src.app.record_market_outcome", lambda briefing_id, outcome: {"briefing_id": briefing_id, "outcome": outcome})


def test_v3_briefing_contract():
    response = client.get("/briefing")

    assert response.status_code == 200
    data = response.json()
    assert data["briefing_id"]
    assert data["learning_summary"]["periods"]["all"]["total"] == 0
    assert data["confidence"] in {"low", "medium", "high"}
    assert "evidence" in data
    assert "risk_alerts" in data


def test_v3_review_surface_contract():
    history_response = client.get("/history")
    learning_response = client.get("/learning")
    backtest_response = client.post("/backtest", json={"history": [], "outcomes": {}})
    outcome_response = client.post(
        "/outcome",
        json={"briefing_id": "alpha", "outcome": {"market_change_pct": 1.2}},
    )
    view_response = client.get("/history/view")

    assert history_response.status_code == 200
    assert learning_response.status_code == 200
    assert backtest_response.status_code == 200
    assert outcome_response.status_code == 200
    assert view_response.status_code == 200
