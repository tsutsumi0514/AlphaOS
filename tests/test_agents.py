from src.agents.chairman_ai import compose_briefing
from src.agents.company_ai import review_company
from src.agents.decision_ai import build_decision_ai
from src.agents.macro_ai import review_macro
from src.agents.news_ai import review_news
from src.agents.risk_ai import build_risk_decision
from src.agents.risk_ai import review_risk
from src.agents.technical_ai import review_technical
from src.briefing import build_briefing


def test_compose_briefing_overrides_risk_alerts(monkeypatch):
    monkeypatch.setattr(
        "src.agents.chairman_ai.build_briefing",
        lambda source: {
            "headline": "headline",
            "risk_alerts": ["old-risk"],
            "key_changes": [],
            "reasons": [],
            "evidence": [],
        },
    )
    monkeypatch.setattr(
        "src.agents.chairman_ai.review_risk",
        lambda briefing: ["new-risk"],
    )
    monkeypatch.setattr(
        "src.agents.chairman_ai.build_learning_summary",
        lambda: {
            "status": "insufficient",
            "sample_size": 0,
            "accuracy": None,
            "weighted_accuracy": None,
            "notes": ["No matched outcomes yet."],
            "periods": {"all": {"total": 0}},
        },
    )

    briefing = compose_briefing({"market_state": "bullish"})

    assert briefing["risk_alerts"] == ["new-risk"]
    assert briefing["headline"] == "headline"
    assert "decision_ai" in briefing
    assert len(briefing["decision_ai"]["views"]) == 5


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


def test_agent_decision_contract_is_stable():
    briefing = build_briefing(
        {
            "market_change_pct": -1.2,
            "usd_jpy": 144.0,
            "news_item": {
                "title": "日経平均、下落と円高で重い展開",
                "source": "Google News",
                "url": "https://example.com/news",
            },
            "watchlist_status": [
                {
                    "symbol": "7203.T",
                    "price": 2700.0,
                    "change_pct": -2.4,
                    "status": "weak",
                },
                {
                    "symbol": "6758.T",
                    "price": 12800.0,
                    "change_pct": 0.2,
                    "status": "steady",
                },
                {
                    "symbol": "9984.T",
                    "price": 9800.0,
                    "change_pct": 2.1,
                    "status": "strong",
                },
            ],
        }
    )

    decisions = [
        build_risk_decision(briefing),
        review_macro(briefing),
        review_news(briefing),
        review_technical(briefing),
        review_company(briefing),
        build_decision_ai(briefing),
    ]

    for decision in decisions:
        assert decision["agent"]
        assert decision["stance"] in {"supportive", "balanced", "defensive", "neutral", "unknown"}
        assert 0.0 <= decision["score"] <= 1.0
        assert decision["confidence"] in {"low", "medium", "high"}
        assert isinstance(decision["reason"], str)
        assert isinstance(decision["evidence"], list)

    chairman = decisions[-1]
    assert chairman["agent"] == "ChairmanAI"
    assert len(chairman["views"]) == 5
    assert chairman["evidence"]
    assert review_risk(briefing)


def test_golden_briefing_case_keeps_expected_output():
    briefing = build_briefing(
        {
            "market_change_pct": -1.2,
            "usd_jpy": 144.0,
            "news_item": {
                "title": "日経平均、下落と円高で重い展開",
                "source": "Google News",
                "url": "https://example.com/news",
            },
            "watchlist_status": [
                {
                    "symbol": "7203.T",
                    "price": 2700.0,
                    "change_pct": -2.4,
                    "status": "weak",
                },
                {
                    "symbol": "6758.T",
                    "price": 12800.0,
                    "change_pct": 0.2,
                    "status": "steady",
                },
                {
                    "symbol": "9984.T",
                    "price": 9800.0,
                    "change_pct": 2.1,
                    "status": "strong",
                },
            ],
        }
    )

    assert briefing["headline"] == "Nikkei is under pressure. yen is strong. 7203.T is weak."
    assert briefing["risk_alerts"] == [
        "Market tone is bearish. Keep new positions small.",
        "Strong yen may pressure export-related names.",
        "7203.T is weakening. Review entry timing carefully.",
        "Both market and currency conditions are risk-off.",
    ]
    assert briefing["reasons"] == [
        "Nikkei day-over-day change is negative.",
        "USD/JPY is in a strong-yen range.",
        "7203.T is weakening versus the previous close.",
        "6758.T is moving within a normal daily range.",
        "9984.T is rising strongly versus the previous close.",
    ]
    assert briefing["confidence"] == "high"
    assert [item["source"] for item in briefing["evidence"]] == ["market", "fx", "news", "watchlist", "watchlist", "watchlist"]
