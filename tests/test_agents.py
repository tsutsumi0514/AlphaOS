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


def test_compose_briefing_reflects_learning_summary(monkeypatch):
    monkeypatch.setattr(
        "src.agents.chairman_ai.build_briefing",
        lambda source: {
            "headline": "headline",
            "risk_alerts": [],
            "key_changes": [],
            "reasons": [],
            "evidence": [],
        },
    )
    monkeypatch.setattr("src.agents.chairman_ai.review_risk", lambda briefing: [])
    monkeypatch.setattr(
        "src.agents.chairman_ai.build_learning_summary",
        lambda: {
            "status": "weak",
            "sample_size": 3,
            "accuracy": 0.25,
            "weighted_accuracy": 0.25,
            "notes": ["Recent forecast accuracy is low. Treat signals carefully."],
            "periods": {"all": {"total": 3}},
        },
    )

    briefing = compose_briefing({"market_state": "bullish"})

    assert briefing["risk_alerts"] == [
        "Recent learning is weak. Use signals with extra caution."
    ]
    assert briefing["key_changes"][-1] == "Recent learning is weak. Use signals with extra caution."
    assert briefing["reasons"][-1] == "Recent learning is weak. Use signals with extra caution."
