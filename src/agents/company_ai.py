"""Company perspective helper for AlphaOS V4."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def review_company(briefing: Mapping[str, Any]) -> dict[str, Any]:
    watchlist = _watchlist_items(briefing)
    if not watchlist:
        return {
            "agent": "CompanyAI",
            "stance": "unknown",
            "summary": "No company-specific watchlist data is available.",
            "signals": ["No watchlist symbols were supplied."],
        }

    strong = [item.get("symbol") for item in watchlist if item.get("status") == "strong"]
    weak = [item.get("symbol") for item in watchlist if item.get("status") == "weak"]

    if len(strong) > len(weak):
        stance = "supportive"
        summary = "Company-level momentum is broadly supportive."
    elif len(weak) > len(strong):
        stance = "cautious"
        summary = "Company-level momentum is broadly cautious."
    else:
        stance = "balanced"
        summary = "Company-level momentum is mixed."

    signals = []
    if strong:
        signals.append("Strong names: " + ", ".join(str(symbol) for symbol in strong if symbol))
    if weak:
        signals.append("Weak names: " + ", ".join(str(symbol) for symbol in weak if symbol))
    if not signals:
        signals.append("All tracked names are steady.")

    return {
        "agent": "CompanyAI",
        "stance": stance,
        "summary": summary,
        "signals": signals,
    }


def _watchlist_items(briefing: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    watchlist_status = briefing.get("watchlist_status")
    if not isinstance(watchlist_status, list):
        return []

    items: list[Mapping[str, Any]] = []
    for item in watchlist_status:
        if isinstance(item, Mapping):
            items.append(item)
    return items
