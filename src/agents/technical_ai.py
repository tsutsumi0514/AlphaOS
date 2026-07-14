"""Technical perspective helper for AlphaOS V4."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .contracts import make_agent_decision


def review_technical(briefing: Mapping[str, Any]) -> dict[str, Any]:
    market_state = _text(briefing.get("market_state"), "unknown")
    watchlist = _watchlist_items(briefing)
    strong = sum(1 for item in watchlist if item.get("status") == "strong")
    weak = sum(1 for item in watchlist if item.get("status") == "weak")
    steady = sum(1 for item in watchlist if item.get("status") == "steady")

    if market_state == "bullish" or strong > weak:
        stance = "supportive"
        summary = "Technical momentum is supportive."
    elif market_state == "bearish" or weak > strong:
        stance = "defensive"
        summary = "Technical momentum is defensive."
    else:
        stance = "balanced"
        summary = "Technical momentum is mixed."

    signals = [
        f"{strong} strong / {weak} weak / {steady} steady watchlist names.",
        f"Market state: {market_state}.",
    ]

    score = 0.75 if stance == "supportive" else 0.25 if stance == "defensive" else 0.5
    evidence = _select_evidence(briefing, {"watchlist", "market"})
    return make_agent_decision(
        agent="TechnicalAI",
        stance=stance,
        score=score,
        confidence="high" if watchlist else "medium",
        reason=summary,
        evidence=evidence,
        summary=summary,
        signals=signals,
    )


def _watchlist_items(briefing: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    watchlist_status = briefing.get("watchlist_status")
    if not isinstance(watchlist_status, list):
        return []

    items: list[Mapping[str, Any]] = []
    for item in watchlist_status:
        if isinstance(item, Mapping):
            items.append(item)
    return items


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
