from pathlib import Path

from src.storage.market_memory import find_similar_market_memory
from src.storage.market_memory import load_market_memory
from src.storage.market_memory import record_market_memory
from src.storage.market_memory import record_replay_memory
from src.storage.market_memory import resolve_memory_path
from src.storage.market_memory import update_market_memory


def test_record_market_memory_and_similarity_search(tmp_path):
    path = tmp_path / "memory.jsonl"

    record_market_memory(
        {
            "briefing_id": "alpha",
            "market_state": "bullish",
            "fx_state": "weak yen",
            "confidence": "high",
            "risk_alerts": ["Market tone is calm."],
            "reasons": ["Momentum is improving."],
            "evidence": [{"source": "market", "label": "Nikkei", "value": 1.2}],
            "watchlist_status": [{"symbol": "7203.T", "status": "strong"}],
        },
        source={"market_change_pct": 1.2},
        path=path,
    )
    record_market_memory(
        {
            "briefing_id": "beta",
            "market_state": "bearish",
            "fx_state": "strong yen",
            "confidence": "low",
            "risk_alerts": ["Risk-off tone."],
            "reasons": ["Pressure is building."],
            "evidence": [{"source": "fx", "label": "USD/JPY", "value": 144.0}],
            "watchlist_status": [{"symbol": "6758.T", "status": "weak"}],
        },
        source={"market_change_pct": -1.4},
        path=path,
    )

    records = load_market_memory(path)
    assert len(records) == 2

    matches = find_similar_market_memory(
        {
            "briefing_id": "query",
            "market_state": "bullish",
            "fx_state": "weak yen",
            "confidence": "high",
            "risk_alerts": ["Market tone is calm."],
            "reasons": ["Momentum is improving."],
            "evidence": [{"source": "market", "label": "Nikkei", "value": 1.2}],
            "watchlist_status": [{"symbol": "7203.T", "status": "strong"}],
        },
        path=path,
    )

    assert matches
    assert matches[0]["briefing_id"] == "alpha"
    assert matches[0]["score"] >= matches[-1]["score"]


def test_update_market_memory_merges_outcome(tmp_path):
    path = tmp_path / "memory.jsonl"

    record_market_memory(
        {
            "briefing_id": "alpha",
            "market_state": "bullish",
            "fx_state": "weak yen",
            "confidence": "high",
            "risk_alerts": [],
            "reasons": [],
            "evidence": [],
            "watchlist_status": [],
        },
        path=path,
    )

    updated = update_market_memory("alpha", {"market_change_pct": 2.1}, path=path)
    assert updated is not None
    assert updated["briefing_id"] == "alpha"
    assert updated["outcome"]["market_change_pct"] == 2.1
    assert load_market_memory(path)[0]["outcome"]["market_change_pct"] == 2.1


def test_record_replay_memory_writes_replay_summary(tmp_path):
    path = tmp_path / "memory.jsonl"

    record = record_replay_memory(
        {"sample_size": 500, "summary": {"accuracy": 0.95}},
        path=path,
    )

    assert record["type"] == "replay_summary"
    assert record["replay_summary"]["sample_size"] == 500
    assert resolve_memory_path(path) == Path(path)
