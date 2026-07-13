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


def test_build_briefing_generates_key_changes_from_states():
    briefing = build_briefing(
        {
            "market_change_pct": 1.0,
            "usd_jpy": 156.2,
            "watchlist_status": [
                {
                    "symbol": "7203.T",
                    "price": 2810.0,
                    "change_pct": 2.4,
                    "status": "strong",
                }
            ],
        }
    )

    assert "Nikkei momentum is positive today." in briefing["key_changes"]
    assert "Yen weakness is supporting exporter sentiment." in briefing["key_changes"]
    assert "7203.T is showing strong watchlist momentum." in briefing["key_changes"]


def test_build_briefing_generates_risk_alerts_from_states():
    briefing = build_briefing(
        {
            "market_change_pct": -1.2,
            "usd_jpy": 144.0,
            "watchlist_status": [
                {
                    "symbol": "7203.T",
                    "price": 2700.0,
                    "change_pct": -2.4,
                    "status": "weak",
                }
            ],
        }
    )

    assert "Market tone is bearish. Keep new positions small." in briefing["risk_alerts"]
    assert "Strong yen may pressure export-related names." in briefing["risk_alerts"]
    assert "7203.T is weakening. Review entry timing carefully." in briefing["risk_alerts"]
    assert "Both market and currency conditions are risk-off." in briefing["risk_alerts"]


def test_build_briefing_generates_reasons_and_confidence():
    briefing = build_briefing(
        {
            "market_change_pct": 1.0,
            "usd_jpy": 156.2,
            "watchlist_status": [
                {
                    "symbol": "7203.T",
                    "price": 2810.0,
                    "change_pct": 2.4,
                    "status": "strong",
                }
            ],
        }
    )

    assert "Nikkei day-over-day change is positive." in briefing["reasons"]
    assert "USD/JPY is in a weak-yen range." in briefing["reasons"]
    assert "7203.T is rising strongly versus the previous close." in briefing["reasons"]
    assert briefing["confidence"] == "high"
