"""Utilities for building AlphaOS briefing payloads."""

from collections.abc import Mapping
from typing import Any

Briefing = dict[str, Any]

DEFAULT_BRIEFING: Briefing = {
    "market_state": "unknown",
    "fx_state": "unknown",
    "watchlist_status": [],
    "risk_alerts": [],
    "key_changes": [],
}


def build_briefing(source: Mapping[str, Any] | None = None) -> Briefing:
    """Return a briefing payload, optionally merging values from source."""
    briefing: Briefing = {
        "market_state": DEFAULT_BRIEFING["market_state"],
        "fx_state": DEFAULT_BRIEFING["fx_state"],
        "watchlist_status": list(DEFAULT_BRIEFING["watchlist_status"]),
        "risk_alerts": list(DEFAULT_BRIEFING["risk_alerts"]),
        "key_changes": list(DEFAULT_BRIEFING["key_changes"]),
    }

    if source is None:
        return briefing

    for key in briefing:
        if key in source:
            value = source[key]
            briefing[key] = list(value) if isinstance(value, list) else value

    return briefing
