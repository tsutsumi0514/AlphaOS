from src.briefing import build_briefing


def test_build_briefing_returns_expected_keys():
    briefing = build_briefing()

    assert "market_state" in briefing
    assert "fx_state" in briefing
    assert "watchlist_status" in briefing
    assert "risk_alerts" in briefing
    assert "key_changes" in briefing


def test_build_briefing_derives_fx_state_from_usd_jpy():
    briefing = build_briefing({"usd_jpy": 156.2})

    assert briefing["fx_state"] == "weak yen"
