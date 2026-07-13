from src.briefing import build_briefing

def test_build_briefing_returns_expected_keys():
    briefing = build_briefing()

    assert "market_state" in briefing
    assert "watchlist_status" in briefing
    assert "risk_alerts" in briefing
    assert "key_changes" in briefing
