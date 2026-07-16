import pytest

from fastapi.testclient import TestClient

from src.app import app
from src.opportunity import build_opportunity_candidates
from src.opportunity import evaluate_candidate_pool


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
                "name": symbol,
                "price": 2810.0,
                "change_pct": 2.4,
                "status": "strong" if index == 0 else "steady",
            }
            for index, symbol in enumerate(symbols)
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
    monkeypatch.setattr("src.app.record_briefing_snapshot", lambda briefing, source: None)
    monkeypatch.setattr("src.app.record_news_snapshot", lambda news_item, recorded_at=None: None)


def test_build_opportunity_candidates_ranks_strong_items_first():
    briefing = {
        "market_state": "bullish",
        "fx_state": "weak yen",
        "confidence": "high",
        "risk_alerts": ["Market tone is calm."],
        "watchlist_status": [
            {"symbol": "7203.T", "name": "Toyota", "status": "strong", "change_pct": 2.4},
            {"symbol": "6758.T", "name": "Sony", "status": "steady", "change_pct": 0.4},
        ],
        "decision_ai": {"stance": "supportive", "reason": "Decision support leans constructive."},
        "evidence": [
            {"source": "market", "label": "Nikkei day-over-day change", "value": 1.2},
            {"source": "fx", "label": "USD/JPY", "value": 156.2},
        ],
    }

    candidates = build_opportunity_candidates(briefing)

    assert candidates
    assert candidates[0]["rank"] == 1
    assert candidates[0]["symbol"] == "7203.T"
    assert candidates[0]["status"] == "buy_watch"
    assert candidates[0]["entry_timing"] == "buy_now"
    assert candidates[0]["entry_reason"]
    assert candidates[0]["confidence"] in {"medium", "high"}
    assert isinstance(candidates[0]["counter_evidence"], list)
    assert candidates[0]["liquidity"] == "unknown"


def test_candidate_pool_excludes_weak_thin_candidates():
    briefing = {
        "market_state": "bullish",
        "fx_state": "weak yen",
        "confidence": "high",
        "risk_alerts": ["Market tone is calm."],
        "watchlist_status": [
            {
                "symbol": "0000.T",
                "name": "ThinStock",
                "status": "weak",
                "change_pct": -4.8,
                "volume": 10_000,
            },
            {
                "symbol": "7203.T",
                "name": "Toyota",
                "status": "strong",
                "change_pct": 2.4,
                "volume": 2_000_000,
            },
        ],
        "decision_ai": {"stance": "supportive", "reason": "Decision support leans constructive."},
        "evidence": [
            {"source": "market", "label": "Nikkei day-over-day change", "value": 1.2},
        ],
    }

    pool = evaluate_candidate_pool(briefing, horizon="daytrade")

    assert pool["candidates"]
    assert pool["candidates"][0]["symbol"] == "7203.T"
    assert pool["candidates"][0]["liquidity"] == "high"
    assert pool["candidates"][0]["entry_timing"] == "buy_now"
    assert pool["excluded"]
    assert pool["excluded"][0]["symbol"] == "0000.T"
    assert "tags" in pool["excluded"][0]
    assert "thin_liquidity" in pool["excluded"][0]["tags"] or "risk_off" in pool["excluded"][0]["tags"]
    assert "Liquidity" in pool["excluded"][0]["reason"] or "Confidence" in pool["excluded"][0]["reason"]


def test_candidates_endpoint_returns_ranked_list():
    response = client.get("/candidates?limit=2")

    assert response.status_code == 200
    data = response.json()
    assert data["horizon"] == "swing"
    assert data["count"] == 2
    assert data["candidates"][0]["symbol"] == "7203.T"
    assert data["top_candidate"]["rank"] == 1
    assert "score" in data["candidates"][0]
    assert "entry_timing" in data["candidates"][0]
    assert "excluded_candidates" in data
    assert "rejected_count" in data
    assert "opportunity_summary" in data
    assert "exclusion_breakdown" in data["opportunity_summary"]
