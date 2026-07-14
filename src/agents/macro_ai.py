"""Macro perspective helper for AlphaOS V4."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .contracts import make_agent_decision


def review_macro(briefing: Mapping[str, Any]) -> dict[str, Any]:
    market_state = _text(briefing.get("market_state"), "unknown")
    fx_state = _text(briefing.get("fx_state"), "unknown")

    signals: list[str] = []
    if market_state == "bullish":
        signals.append("Equity momentum is positive.")
    elif market_state == "bearish":
        signals.append("Equity momentum is weak.")
    else:
        signals.append("Equity momentum is mixed.")

    if fx_state == "weak yen":
        signals.append("FX is supporting exporters.")
    elif fx_state == "strong yen":
        signals.append("FX is pressuring exporters.")
    else:
        signals.append("FX is neutral.")

    if market_state == "bullish" and fx_state == "weak yen":
        stance = "risk-on"
        summary = "Macro conditions lean supportive for Japanese equities."
    elif market_state == "bearish" and fx_state == "strong yen":
        stance = "risk-off"
        summary = "Macro conditions lean defensive for Japanese equities."
    else:
        stance = "balanced"
        summary = "Macro signals are mixed and need risk control."

    score = 0.8 if stance == "supportive" else 0.2 if stance == "defensive" else 0.5
    evidence = _select_evidence(briefing, {"market", "fx"})
    reason = summary
    return make_agent_decision(
        agent="MacroAI",
        stance=stance,
        score=score,
        confidence="high" if evidence else "medium",
        reason=reason,
        evidence=evidence,
        summary=summary,
        signals=signals,
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


def _text(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if value is None:
        return default
    return str(value)
