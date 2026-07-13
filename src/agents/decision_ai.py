"""Decision AI orchestrator for AlphaOS V4."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .company_ai import review_company
from .macro_ai import review_macro
from .news_ai import review_news
from .technical_ai import review_technical
from .risk_ai import review_risk


def build_decision_ai(briefing: Mapping[str, Any]) -> dict[str, Any]:
    macro = review_macro(briefing)
    news = review_news(briefing)
    technical = review_technical(briefing)
    company = review_company(briefing)
    risk_alerts = review_risk(dict(briefing))
    risk = {
        "agent": "RiskAI",
        "stance": "defensive" if risk_alerts else "balanced",
        "summary": _risk_summary(risk_alerts),
        "signals": risk_alerts,
    }

    views = [macro, news, technical, company, risk]
    stance = _consensus_stance(view["stance"] for view in views)
    summary = _consensus_summary(stance, views)

    return {
        "agent": "ChairmanAI",
        "stance": stance,
        "summary": summary,
        "views": views,
        "signals": {
            "supportive": sum(1 for view in views if view["stance"] in {"supportive", "risk-on"}),
            "defensive": sum(1 for view in views if view["stance"] in {"defensive", "cautious", "risk-off"}),
            "balanced": sum(1 for view in views if view["stance"] in {"balanced", "neutral", "unknown"}),
        },
    }


def _consensus_stance(stances: Any) -> str:
    scores = {"supportive": 0, "balanced": 0, "defensive": 0}
    for stance in stances:
        if stance in {"supportive", "risk-on"}:
            scores["supportive"] += 1
        elif stance in {"defensive", "cautious", "risk-off"}:
            scores["defensive"] += 1
        else:
            scores["balanced"] += 1

    if scores["supportive"] > scores["defensive"] and scores["supportive"] >= scores["balanced"]:
        return "supportive"
    if scores["defensive"] > scores["supportive"] and scores["defensive"] >= scores["balanced"]:
        return "defensive"
    return "balanced"


def _consensus_summary(stance: str, views: list[dict[str, Any]]) -> str:
    summary_bits = [view["summary"] for view in views[:3] if isinstance(view.get("summary"), str)]
    if stance == "supportive":
        prefix = "Decision support leans constructive."
    elif stance == "defensive":
        prefix = "Decision support leans defensive."
    else:
        prefix = "Decision support remains balanced."

    if summary_bits:
        return prefix + " " + " ".join(summary_bits)
    return prefix


def _risk_summary(alerts: list[str]) -> str:
    if not alerts:
        return "Risk view is calm."
    if len(alerts) == 1:
        return alerts[0]
    return alerts[0] + f" (+{len(alerts) - 1} more)"
