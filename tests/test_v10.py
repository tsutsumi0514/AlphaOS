from src.opportunity import evaluate_candidate_pool


def test_candidate_noise_reduction_excludes_low_evidence_low_confidence_candidate():
    briefing = {
        "market_state": "neutral",
        "fx_state": "neutral",
        "confidence": "medium",
        "risk_alerts": [],
        "watchlist_status": [
            {
                "symbol": "0000.T",
                "name": "ThinStock",
                "status": "steady",
                "change_pct": 0.2,
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
        "decision_ai": {"stance": "balanced", "reason": "Consensus is mixed."},
        "evidence": [],
    }

    pool = evaluate_candidate_pool(briefing, horizon="daytrade")

    symbols = [candidate["symbol"] for candidate in pool["candidates"]]
    excluded_symbols = [candidate["symbol"] for candidate in pool["excluded"]]

    assert "7203.T" in symbols
    assert "0000.T" in excluded_symbols
    excluded = next(item for item in pool["excluded"] if item["symbol"] == "0000.T")
    assert "low_evidence" in excluded["tags"]
    assert excluded["reason"]
