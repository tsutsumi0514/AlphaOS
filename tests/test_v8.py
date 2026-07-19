from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.opportunity import evaluate_candidate_pool
from src.simulation.replay import run_walk_forward_validation


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
                "status": "strong",
                "volume": 2_000_000,
                "sector": "technology",
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
    monkeypatch.setattr("src.app.record_briefing_snapshot", lambda briefing, source: None)
    monkeypatch.setattr("src.app.record_news_snapshot", lambda news_item, recorded_at=None: None)
    monkeypatch.setattr("src.app.record_market_memory", lambda briefing, source: None)
    monkeypatch.setattr("src.app.record_replay_memory", lambda replay_result: None)


def test_evaluate_candidate_pool_exposes_candidate_reason_and_unavailable_liquidity():
    briefing = {
        "market_state": "bullish",
        "fx_state": "weak yen",
        "confidence": "high",
        "risk_alerts": ["Market tone is calm."],
        "watchlist_status": [
            {
                "symbol": "7203.T",
                "name": "Toyota",
                "status": "strong",
                "change_pct": 2.4,
                "sector": "technology",
            }
        ],
        "decision_ai": {"stance": "supportive", "reason": "Decision support leans constructive."},
        "evidence": [
            {"source": "market", "label": "Nikkei day-over-day change", "value": 1.2},
            {"source": "fx", "label": "USD/JPY", "value": 156.2},
        ],
    }

    pool = evaluate_candidate_pool(briefing, horizon="swing")

    assert pool["candidates"]
    candidate = pool["candidates"][0]
    assert candidate["candidate_reason"]
    assert candidate["candidate_reason"] != candidate["entry_reason"]
    assert candidate["candidate_reason"].startswith("7203.T:")
    assert "\n" not in candidate["candidate_reason"]
    assert candidate["liquidity"] == "unavailable"
    assert candidate["counter_evidence"]
    assert candidate["entry_timing"] == "buy_now"


def test_evaluate_candidate_pool_excludes_daytrade_thin_liquidity():
    briefing = {
        "market_state": "neutral",
        "fx_state": "neutral",
        "confidence": "medium",
        "risk_alerts": [],
        "watchlist_status": [
            {
                "symbol": "0000.T",
                "name": "ThinStock",
                "status": "weak",
                "change_pct": -4.8,
                "volume": 10_000,
            }
        ],
        "evidence": [{"source": "market", "label": "Nikkei", "value": 0.1}],
    }

    pool = evaluate_candidate_pool(briefing, horizon="daytrade")

    assert not pool["candidates"]
    assert pool["excluded"]
    assert pool["excluded"][0]["symbol"] == "0000.T"
    assert any(
        tag in pool["excluded"][0]["tags"]
        for tag in ("thin_liquidity", "risk_off", "low_score")
    )


def test_candidates_endpoint_includes_personalization_details(monkeypatch):
    monkeypatch.setattr(
        "src.app.find_similar_market_memory",
        lambda briefing, limit=5: [],
    )
    monkeypatch.setattr(
        "src.app.build_knowledge_graph",
        lambda briefing, scenarios=(), horizon="swing": {
            "nodes": [{"id": "candidate:7203.T", "label": "7203.T", "kind": "candidate", "summary": "core_entry"}],
            "edges": [],
            "top_candidate": None,
            "scenario_report": {"scenarios": []},
        },
    )

    response = client.get(
        "/candidates?horizon=daytrade&limit=1&style=daytrade&investment_period=short&interested_markets=technology"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["strategy_mode"] == "daytrade"
    assert data["candidates"]
    top_candidate = data["candidates"][0]
    assert top_candidate["candidate_reason"]
    assert top_candidate["personalized_score"] >= top_candidate["score"]
    assert top_candidate["personalization_notes"]
    assert data["top_candidate"]["symbol"] == top_candidate["symbol"]


def test_replay_compare_view_shows_replay_summary(monkeypatch):
    monkeypatch.setattr(
        "src.app.find_latest_replay_summary",
        lambda: {
            "memory_id": "replay-1",
            "recorded_at": "2026-07-15T00:00:00Z",
            "replay_summary": {
                "sample_size": 500,
                "summary": {
                    "accuracy": 0.9477,
                    "weighted_accuracy": 0.9409,
                    "coverage": 0.42,
                },
                "baseline": {"summary": {"accuracy": 0.5632, "weighted_accuracy": 0.5601}},
                "validation": {"summary": {"accuracy": 0.9477, "weighted_accuracy": 0.9409}},
            },
        },
    )
    monkeypatch.setattr(
        "src.app.find_similar_market_memory",
        lambda briefing, limit=5: [
            {"briefing_id": "alpha", "score": 0.91, "match_reasons": ["market_state", "fx_state"]}
        ],
    )

    response = client.get("/replay/compare")

    assert response.status_code == 200
    assert "AlphaOS Replay 比較" in response.text
    assert "Replay summary" in response.text
    assert "weighted_accuracy" in response.text
    assert "類似事例" in response.text


def test_walk_forward_validation_uses_bounded_training_window(monkeypatch):
    monkeypatch.setattr(
        "src.simulation.replay._compose_replay_briefing",
        lambda source, thresholds, learning_summary=None: {
            "market_state": "bullish",
            "fx_state": "weak yen",
            "confidence": "high",
            "watchlist_status": [{"symbol": "7203.T", "status": "strong"}],
            "evidence": [{"source": "market", "label": "Nikkei", "value": 1.2}],
        },
    )

    records = []
    base_date = date(2026, 7, 1)
    for offset in range(8):
        briefing_date = base_date + timedelta(days=offset)
        outcome_date = briefing_date + timedelta(days=1)
        records.append(
            {
                "briefing_date": briefing_date,
                "outcome_date": outcome_date,
                "source": {
                    "briefing_date": briefing_date,
                    "market_change_pct": 1.0,
                    "usd_jpy": 156.2,
                    "watchlist_status": [{"symbol": "7203.T", "status": "strong", "change_pct": 2.4}],
                },
                "outcome": {
                    "market_change_pct": 1.1,
                    "usd_jpy": 156.0,
                    "watchlist_status": [{"symbol": "7203.T", "status": "strong", "change_pct": 2.0}],
                },
            }
        )

    result = run_walk_forward_validation(records, training_window=3, evaluation_window=2)

    assert result["sample_size"] > 0
    assert result["folds"]
    assert result["folds"][0]["train_range"]["start"] == "2026-07-01"
    assert result["folds"][0]["train_range"]["end"] == "2026-07-03"
    assert result["folds"][1]["train_range"]["start"] == "2026-07-03"
    assert result["windows"]["training_window"] == 3
