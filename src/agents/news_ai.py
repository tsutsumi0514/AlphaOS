"""News perspective helper for AlphaOS V4."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .contracts import make_agent_decision


POSITIVE_MARKERS = ("上昇", "好調", "改善", "追い風", "最高", "増益", "買い")
NEGATIVE_MARKERS = ("下落", "悪化", "懸念", "逆風", "減益", "売り", "低下")


def review_news(briefing: Mapping[str, Any]) -> dict[str, Any]:
    news_item = briefing.get("news_item")
    if not isinstance(news_item, Mapping):
        return make_agent_decision(
            agent="NewsAI",
            stance="unknown",
            score=0.0,
            confidence="low",
            reason="Historical news is unavailable in this replay.",
            evidence=_select_evidence(briefing, {"news"}),
            summary="Historical news is unavailable in this replay.",
            signals=["No archived news item was supplied."],
        )

    title = _text(news_item.get("title"), "")
    source = _text(news_item.get("source"), "")
    signals: list[str] = []

    lowered = title.lower()
    if any(marker in title for marker in POSITIVE_MARKERS):
        stance = "supportive"
        signals.append("Headline wording is supportive.")
        summary = f"News tone is constructive: {title}."
    elif any(marker in title for marker in NEGATIVE_MARKERS):
        stance = "cautious"
        signals.append("Headline wording is cautious.")
        summary = f"News tone is defensive: {title}."
    else:
        stance = "neutral"
        signals.append("Headline wording is neutral.")
        summary = f"News tone is mixed: {title}."

    if source:
        signals.append(f"Source: {source}.")
    if lowered and "決算" in lowered:
        signals.append("Earnings-related story detected.")

    score = 0.75 if stance == "supportive" else 0.25 if stance == "defensive" else 0.5
    return make_agent_decision(
        agent="NewsAI",
        stance=stance,
        score=score,
        confidence="high" if len(signals) >= 2 else "medium",
        reason=summary,
        evidence=_select_evidence(briefing, {"news"}),
        summary=summary,
        signals=signals,
    )


def _text(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if value is None:
        return default
    return str(value)


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
