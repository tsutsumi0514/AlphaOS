from src.learning.feedback import build_learning_summary


def test_build_learning_summary_reports_strong_accuracy():
    summary = build_learning_summary(
        history=[
            {
                "briefing_id": "alpha",
                "briefing": {
                    "market_state": "bullish",
                    "fx_state": "weak yen",
                    "watchlist_status": [{"symbol": "7203.T", "status": "strong"}],
                },
            }
        ],
        outcomes=[
            {
                "briefing_id": "alpha",
                "outcome": {
                    "market_change_pct": 1.2,
                    "usd_jpy": 156.2,
                    "watchlist_status": [{"symbol": "7203.T", "change_pct": 2.4}],
                },
            }
        ],
    )

    assert summary["status"] == "strong"
    assert summary["sample_size"] == 1
    assert summary["accuracy"] == 1.0
    assert "stable" in summary["notes"][0]


def test_build_learning_summary_reports_insufficient_when_no_matches():
    summary = build_learning_summary(history=[], outcomes=[])

    assert summary["status"] == "insufficient"
    assert summary["sample_size"] == 0
    assert summary["accuracy"] is None
