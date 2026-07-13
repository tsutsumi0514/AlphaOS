from src.agents.chairman_ai import compose_briefing


def test_compose_briefing_overrides_risk_alerts(monkeypatch):
    monkeypatch.setattr(
        "src.agents.chairman_ai.build_briefing",
        lambda source: {
            "headline": "headline",
            "risk_alerts": ["old-risk"],
            "evidence": [],
        },
    )
    monkeypatch.setattr(
        "src.agents.chairman_ai.review_risk",
        lambda briefing: ["new-risk"],
    )

    briefing = compose_briefing({"market_state": "bullish"})

    assert briefing["risk_alerts"] == ["new-risk"]
    assert briefing["headline"] == "headline"
