from src.knowledge_graph import build_knowledge_graph
from src.personal import personalize_candidates
from src.simulation.what_if import run_what_if_simulation


def test_run_what_if_simulation_uses_builtin_scenarios():
    briefing = {
        "market_state": "bullish",
        "fx_state": "weak yen",
        "confidence": "high",
        "risk_alerts": ["Market tone is calm."],
    }

    report = run_what_if_simulation(briefing, ["yen_appreciation", "us_recession"])

    assert report["scenario_count"] == 2
    assert report["scenarios"][0]["market_bias"] == "bearish"
    assert report["scenarios"][1]["risk_bias"] == "high"


def test_build_knowledge_graph_links_candidate_and_scenario():
    briefing = {
        "market_state": "bullish",
        "fx_state": "weak yen",
        "confidence": "high",
        "risk_alerts": ["Market tone is calm."],
        "decision_ai": {"agent": "ChairmanAI", "reason": "Constructive consensus."},
        "watchlist_status": [
            {"symbol": "7203.T", "name": "Toyota", "status": "strong", "change_pct": 2.1, "volume": 2_000_000}
        ],
        "evidence": [{"source": "market", "label": "Nikkei", "value": 1.2}],
    }

    graph = build_knowledge_graph(briefing, scenarios=["rate_cut"])

    assert graph["nodes"]
    assert graph["edges"]
    assert graph["top_candidate"]["symbol"] == "7203.T"
    assert any(node["kind"] == "scenario" for node in graph["nodes"])


def test_personalize_candidates_filters_holdings_and_style():
    candidates = [
        {"symbol": "7203.T", "horizon": "swing", "confidence": "high"},
        {"symbol": "6758.T", "horizon": "daytrade", "confidence": "low"},
        {"symbol": "9984.T", "horizon": "daytrade", "confidence": "high"},
    ]

    result = personalize_candidates(
        candidates,
        {
            "holdings": ["7203.T"],
            "investment_period": "short",
            "risk_tolerance": "low",
            "style": "daytrade",
            "interested_markets": [],
        },
    )

    assert result["profile"]["holdings"] == ["7203.T"]
    assert all(candidate["symbol"] != "7203.T" for candidate in result["candidates"])
    assert all(candidate["horizon"] == "daytrade" for candidate in result["candidates"])
