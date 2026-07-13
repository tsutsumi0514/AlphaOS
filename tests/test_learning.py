from src.learning.backtest import backtest_history, score_briefing_against_outcome, summarize_backtest


def test_score_briefing_against_outcome_scores_market_fx_and_watchlist():
    score = score_briefing_against_outcome(
        {
            "market_state": "bullish",
            "fx_state": "weak yen",
            "watchlist_status": [
                {"symbol": "7203.T", "status": "strong"},
            ],
        },
        {
            "market_change_pct": 1.1,
            "usd_jpy": 156.2,
            "watchlist_status": [
                {"symbol": "7203.T", "change_pct": 2.4},
            ],
        },
    )

    assert score["matched"] == 3
    assert score["total"] == 3
    assert score["accuracy"] == 1.0
    assert score["weighted_accuracy"] == 1.0


def test_score_briefing_against_outcome_uses_weights():
    score = score_briefing_against_outcome(
        {
            "market_state": "bullish",
            "fx_state": "weak yen",
            "watchlist_status": [
                {"symbol": "7203.T", "status": "strong"},
            ],
        },
        {
            "market_change_pct": 0.1,
            "usd_jpy": 150.0,
            "watchlist_status": [
                {"symbol": "7203.T", "change_pct": 2.4},
            ],
        },
    )

    assert score["matched"] == 1
    assert score["total"] == 3
    assert score["weighted_matched"] == 1.0
    assert score["weighted_total"] == 5.0
    assert score["weighted_accuracy"] == 0.2


def test_backtest_history_joins_records_by_briefing_id():
    results = backtest_history(
        [
            {
                "briefing_id": "alpha",
                "recorded_at": "2026-07-14T00:00:00Z",
                "briefing": {
                    "market_state": "bearish",
                    "fx_state": "strong yen",
                },
            }
        ],
        {
            "alpha": {"market_change_pct": -1.2, "usd_jpy": 144.0},
        },
    )

    assert len(results) == 1
    assert results[0]["briefing_id"] == "alpha"
    assert results[0]["result"]["accuracy"] == 1.0


def test_summarize_backtest_aggregates_result_counts():
    summary = summarize_backtest(
        [
            {"result": {"matched": 2, "total": 3, "weighted_matched": 3.0, "weighted_total": 4.0}},
            {"result": {"matched": 1, "total": 1, "weighted_matched": 1.0, "weighted_total": 1.0}},
        ]
    )

    assert summary["total"] == 2
    assert summary["matched"] == 3
    assert summary["checks"] == 4
    assert summary["accuracy"] == 0.75
    assert summary["weighted_matched"] == 4.0
    assert summary["weighted_total"] == 5.0
    assert summary["weighted_accuracy"] == 0.8
