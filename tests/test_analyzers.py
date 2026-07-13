from src.analyzers.briefing_signals import (
    derive_confidence,
    summarize_evidence,
    summarize_reasons,
    summarize_risk_alerts,
)


def test_summarize_risk_alerts_combines_bearish_market_and_strong_yen():
    alerts = summarize_risk_alerts(
        {
            "market_state": "bearish",
            "fx_state": "strong yen",
            "watchlist_status": [
                {
                    "symbol": "7203.T",
                    "status": "weak",
                }
            ],
        }
    )

    assert "Market tone is bearish. Keep new positions small." in alerts
    assert "Strong yen may pressure export-related names." in alerts
    assert "7203.T is weakening. Review entry timing carefully." in alerts
    assert "Both market and currency conditions are risk-off." in alerts


def test_summarize_reasons_reflects_watchlist_and_market_signals():
    reasons = summarize_reasons(
        {
            "market_state": "bullish",
            "fx_state": "weak yen",
            "watchlist_status": [
                {
                    "symbol": "7203.T",
                    "status": "strong",
                }
            ],
        }
    )

    assert "Nikkei day-over-day change is positive." in reasons
    assert "USD/JPY is in a weak-yen range." in reasons
    assert "7203.T is rising strongly versus the previous close." in reasons


def test_summarize_evidence_keeps_structured_items():
    evidence = summarize_evidence(
        {
            "market_state": "bullish",
            "fx_state": "weak yen",
            "news_item": {
                "title": "日経平均、寄り付き後に上昇",
                "source": "Google News",
            },
            "watchlist_status": [
                {
                    "symbol": "7203.T",
                    "status": "strong",
                    "price": 2810.0,
                    "change_pct": 2.4,
                }
            ],
        },
        {
            "market_change_pct": 1.0,
            "usd_jpy": 156.2,
        },
    )

    assert any(item["source"] == "market" for item in evidence)
    assert any(item["source"] == "fx" for item in evidence)
    assert any(item["source"] == "news" for item in evidence)
    assert any(item["source"] == "watchlist" for item in evidence)


def test_derive_confidence_reflects_signal_depth():
    assert derive_confidence({"market_state": "bullish", "fx_state": "weak yen"}) == "medium"
    assert (
        derive_confidence(
            {
                "market_state": "bullish",
                "fx_state": "weak yen",
                "news_item": {"title": "headline"},
            }
        )
        == "high"
    )
    assert (
        derive_confidence(
            {
                "market_state": "bullish",
                "fx_state": "weak yen",
                "news_item": {"title": "headline"},
                "watchlist_status": [{"symbol": "7203.T", "status": "strong"}],
                "evidence": [{"source": "market", "label": "Nikkei", "value": 1.0}],
            }
        )
        == "high"
    )
