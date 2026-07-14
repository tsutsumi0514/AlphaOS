"""Risk-focused briefing agent for AlphaOS."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..analyzers.briefing_signals import summarize_risk_alerts
from .contracts import make_agent_decision


def review_risk(briefing: dict) -> list[str]:
    """Return the compact risk view for a briefing."""
    return build_risk_decision(briefing).get("signals", [])


def build_risk_decision(briefing: Mapping[str, Any]) -> dict[str, Any]:
    alerts = summarize_risk_alerts(dict(briefing))
    stance = "defensive" if alerts else "balanced"
    reason = alerts[0] if alerts else "Risk view is calm."
    confidence = "high" if len(alerts) >= 2 else "medium" if alerts else "low"
    score = 0.2 if alerts else 0.6
    return make_agent_decision(
        agent="RiskAI",
        stance=stance,
        score=score,
        confidence=confidence,
        reason=reason,
        evidence=_select_evidence(briefing, {"market", "fx", "watchlist"}),
        summary=reason,
        signals=alerts,
    )


def _select_evidence(briefing: Mapping[str, Any], sources: set[str]) -> list[dict[str, Any]]:
    evidence = briefing.get("evidence")
    if not isinstance(evidence, list):
        return []
    selected: list[dict[str, Any]] = []
    for item in evidence:
        if not isinstance(item, Mapping):
            continue
        if item.get("source") in sources:
            selected.append(dict(item))
    return selected
