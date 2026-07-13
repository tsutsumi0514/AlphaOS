from src.briefing import build_briefing


def test_build_briefing_applies_source_overrides():
    briefing = build_briefing(
        {
            "market_state": "bullish",
            "watchlist_status": [{"symbol": "7203.T", "status": "watch"}],
            "risk_alerts": ["yen weakness"],
            "key_changes": ["Toyota upgraded"],
        }
    )

    assert briefing["market_state"] == "bullish"
    assert briefing["watchlist_status"] == [{"symbol": "7203.T", "status": "watch"}]
    assert briefing["risk_alerts"] == ["yen weakness"]
    assert briefing["key_changes"] == ["Toyota upgraded"]


def test_build_briefing_derives_market_state_from_change_pct():
    briefing = build_briefing({"market_change_pct": -1.2})

    assert briefing["market_state"] == "bearish"
