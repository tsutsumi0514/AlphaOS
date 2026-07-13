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


def derive_fx_state(usd_jpy: float | int | None) -> str:
    """Map a USD/JPY rate to a simple FX state label."""
    if usd_jpy is None:
        return "unknown"
    if usd_jpy >= 155:
        return "weak yen"
    if usd_jpy <= 145:
        return "strong yen"
    return "neutral"


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

    if "usd_jpy" in source:
        briefing["fx_state"] = derive_fx_state(source["usd_jpy"])

    for key in briefing:
        if key in source and key != "fx_state":
            value = source[key]
            briefing[key] = list(value) if isinstance(value, list) else value

    return briefing
