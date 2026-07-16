from datetime import date, timedelta

from src.opportunity import evaluate_candidate_pool
from src.simulation.replay import run_walk_forward_validation


def test_support_gap_nudges_candidate_score():
    briefing = {
        "market_state": "neutral",
        "fx_state": "neutral",
        "confidence": "medium",
        "risk_alerts": [],
        "watchlist_status": [
            {
                "symbol": "7203.T",
                "name": "Toyota",
                "status": "strong",
                "change_pct": 2.4,
                "volume": 2_000_000,
            }
        ],
        "evidence": [{"source": "market", "label": "Nikkei", "value": 0.4}],
        "candidate_learning_profile": {
            "status": "moderate",
            "score_adjustment": 0.0,
            "confidence_adjustment": 0.0,
            "timing_bias": "wait",
            "exclusion_bias": "normal",
            "support_gap": 0.08,
        },
    }

    low_support = evaluate_candidate_pool(briefing)["candidates"][0]["score"]
    briefing["candidate_learning_profile"]["support_gap"] = -0.08
    low_score = evaluate_candidate_pool(briefing)["candidates"][0]["score"]

    assert low_support > low_score


def test_walk_forward_validation_reports_window_sizes():
    records = []
    base_date = date(2026, 7, 1)
    for offset in range(7):
        briefing_date = base_date + timedelta(days=offset)
        records.append(
            {
                "briefing_date": briefing_date,
                "outcome_date": briefing_date + timedelta(days=1),
                "source": {
                    "briefing_date": briefing_date,
                    "market_change_pct": 1.0,
                    "usd_jpy": 156.2,
                    "watchlist_status": [{"symbol": "7203.T", "status": "strong", "change_pct": 2.4}],
                },
                "outcome": {
                    "market_change_pct": 1.2,
                    "usd_jpy": 156.0,
                    "watchlist_status": [{"symbol": "7203.T", "status": "strong", "change_pct": 2.1}],
                },
            }
        )

    result = run_walk_forward_validation(records, training_window=3, evaluation_window=2)

    assert result["folds"]
    first_fold = result["folds"][0]
    assert first_fold["training_sample_size"] == 3
    assert first_fold["evaluation_sample_size"] == 2
