"""Shared agent output contract helpers for AlphaOS."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, NotRequired, TypedDict


ALLOWED_AGENT_STANCES = {"supportive", "balanced", "defensive", "neutral", "unknown"}
ALLOWED_CONFIDENCE = {"low", "medium", "high"}


class AgentDecision(TypedDict):
    agent: str
    stance: str
    score: float
    confidence: str
    reason: str
    evidence: list[dict[str, Any]]
    summary: NotRequired[str]
    signals: NotRequired[list[str]]
    views: NotRequired[list[dict[str, Any]]]


def make_agent_decision(
    *,
    agent: str,
    stance: str,
    score: float,
    confidence: str,
    reason: str,
    evidence: Sequence[Mapping[str, Any]] | Sequence[dict[str, Any]] | None,
    summary: str | None = None,
    signals: Sequence[str] | None = None,
    views: Sequence[Mapping[str, Any]] | Sequence[dict[str, Any]] | None = None,
) -> AgentDecision:
    decision: AgentDecision = {
        "agent": agent,
        "stance": normalize_stance(stance),
        "score": _bounded_score(score),
        "confidence": normalize_confidence(confidence),
        "reason": reason.strip() if isinstance(reason, str) and reason.strip() else "No clear signal.",
        "evidence": _normalize_evidence(evidence),
    }

    if isinstance(summary, str) and summary.strip():
        decision["summary"] = summary.strip()
    else:
        decision["summary"] = decision["reason"]

    normalized_signals = _normalize_signals(signals)
    if normalized_signals:
        decision["signals"] = normalized_signals

    normalized_views = _normalize_views(views)
    if normalized_views:
        decision["views"] = normalized_views

    return decision


def normalize_stance(value: Any) -> str:
    if not isinstance(value, str):
        return "unknown"

    text = value.strip().lower()
    alias_map = {
        "risk-on": "supportive",
        "supportive": "supportive",
        "constructive": "supportive",
        "bullish": "supportive",
        "risk-off": "defensive",
        "defensive": "defensive",
        "cautious": "defensive",
        "bearish": "defensive",
        "balanced": "balanced",
        "neutral": "neutral",
        "unknown": "unknown",
    }
    return alias_map.get(text, "unknown")


def normalize_confidence(value: Any) -> str:
    if not isinstance(value, str):
        return "low"

    text = value.strip().lower()
    if text in ALLOWED_CONFIDENCE:
        return text
    return "low"


def _normalize_evidence(
    evidence: Sequence[Mapping[str, Any]] | Sequence[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if not evidence:
        return []

    normalized: list[dict[str, Any]] = []
    for item in evidence:
        if isinstance(item, Mapping):
            normalized.append(dict(item))
    return normalized


def _normalize_signals(signals: Sequence[str] | None) -> list[str]:
    if not signals:
        return []

    normalized: list[str] = []
    for signal in signals:
        if isinstance(signal, str) and signal.strip():
            normalized.append(signal.strip())
    return normalized


def _normalize_views(
    views: Sequence[Mapping[str, Any]] | Sequence[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if not views:
        return []

    normalized: list[dict[str, Any]] = []
    for view in views:
        if isinstance(view, Mapping):
            normalized.append(dict(view))
    return normalized


def _bounded_score(score: Any) -> float:
    try:
        numeric = float(score)
    except (TypeError, ValueError):
        return 0.0
    if numeric < 0.0:
        return 0.0
    if numeric > 1.0:
        return 1.0
    return round(numeric, 3)
