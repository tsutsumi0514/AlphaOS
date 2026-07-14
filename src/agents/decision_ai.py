"""Decision AI orchestrator for AlphaOS V4."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .company_ai import review_company
from .contracts import AgentDecision, make_agent_decision, normalize_stance
from .macro_ai import review_macro
from .news_ai import review_news
from .risk_ai import build_risk_decision
from .technical_ai import review_technical


def build_decision_ai(briefing: Mapping[str, Any]) -> AgentDecision:
    risk = build_risk_decision(briefing)
    macro = review_macro(briefing)
    news = review_news(briefing)
    technical = review_technical(briefing)
    company = review_company(briefing)

    views = [risk, macro, news, technical, company]
    stance = _consensus_stance(view["stance"] for view in views)
    score = _consensus_score(views)
    confidence = _consensus_confidence(views)
    reason = _consensus_reason(stance, views)
    evidence = _merge_evidence(views)
    signals = {
        "supportive": sum(1 for view in views if view["stance"] == "supportive"),
        "defensive": sum(1 for view in views if view["stance"] == "defensive"),
        "balanced": sum(1 for view in views if view["stance"] in {"balanced", "neutral", "unknown"}),
    }

    decision = make_agent_decision(
        agent="ChairmanAI",
        stance=stance,
        score=score,
        confidence=confidence,
        reason=reason,
        evidence=evidence,
        summary=reason,
        views=views,
    )
    decision["signals"] = [f"{key}={value}" for key, value in signals.items()]
    return decision


def _consensus_stance(stances: Any) -> str:
    scores = {"supportive": 0, "balanced": 0, "defensive": 0}
    for stance in stances:
        normalized = normalize_stance(stance)
        if normalized == "supportive":
            scores["supportive"] += 1
        elif normalized == "defensive":
            scores["defensive"] += 1
        else:
            scores["balanced"] += 1

    if scores["supportive"] > scores["defensive"] and scores["supportive"] >= scores["balanced"]:
        return "supportive"
    if scores["defensive"] > scores["supportive"] and scores["defensive"] >= scores["balanced"]:
        return "defensive"
    return "balanced"


def _consensus_score(views: list[AgentDecision]) -> float:
    if not views:
        return 0.0
    score = sum(float(view.get("score", 0.0)) for view in views) / len(views)
    return round(score, 3)


def _consensus_confidence(views: list[AgentDecision]) -> str:
    if not views:
        return "low"

    weight = 0
    for view in views:
        confidence = view.get("confidence", "low")
        if confidence == "high":
            weight += 3
        elif confidence == "medium":
            weight += 2
        else:
            weight += 1

    average = weight / len(views)
    if average >= 2.5:
        return "high"
    if average >= 1.6:
        return "medium"
    return "low"


def _consensus_reason(stance: str, views: list[AgentDecision]) -> str:
    reason_bits = [view.get("reason") for view in views if isinstance(view.get("reason"), str)]
    reason_bits = [bit for bit in reason_bits if bit]
    if stance == "supportive":
        prefix = "Decision support leans constructive."
    elif stance == "defensive":
        prefix = "Decision support leans defensive."
    else:
        prefix = "Decision support remains balanced."

    if reason_bits:
        return prefix + " " + " ".join(reason_bits[:3])
    return prefix


def _merge_evidence(views: list[AgentDecision]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[Any, Any, Any]] = set()
    for view in views:
        evidence = view.get("evidence", [])
        if not isinstance(evidence, list):
            continue
        for item in evidence:
            if not isinstance(item, Mapping):
                continue
            key = (item.get("source"), item.get("label"), item.get("value"))
            if key in seen:
                continue
            seen.add(key)
            merged.append(dict(item))
    return merged
