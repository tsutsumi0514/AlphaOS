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


def derive_market_state(market_change_pct: float | int | None) -> str:
    """Map a market move to a simple market state label."""
    if market_change_pct is None:
        return "unknown"
    if market_change_pct >= 0.7:
        return "bullish"
    if market_change_pct <= -0.7:
        return "bearish"
    return "neutral"


def derive_fx_state(usd_jpy: float | int | None) -> str:
    """Map a USD/JPY rate to a simple FX state label."""
    if usd_jpy is None:
        return "unknown"
    if usd_jpy >= 155:
        return "weak yen"
    if usd_jpy <= 145:
        return "strong yen"
    return "neutral"


def summarize_key_changes(briefing: Briefing) -> list[str]:
    """Build a short list of human-readable market changes."""
    changes: list[str] = []

    market_state = briefing.get("market_state")
    if market_state == "bullish":
        changes.append("Nikkei momentum is positive today.")
    elif market_state == "bearish":
        changes.append("Nikkei momentum is under pressure today.")

    fx_state = briefing.get("fx_state")
    if fx_state == "weak yen":
        changes.append("Yen weakness is supporting exporter sentiment.")
    elif fx_state == "strong yen":
        changes.append("Yen strength may pressure exporter sentiment.")

    watchlist_status = briefing.get("watchlist_status")
    if isinstance(watchlist_status, list) and watchlist_status:
        first = watchlist_status[0]
        if isinstance(first, Mapping):
            symbol = first.get("symbol", "Watchlist")
            status = first.get("status")
            if status == "strong":
                changes.append(f"{symbol} is showing strong watchlist momentum.")
            elif status == "weak":
                changes.append(f"{symbol} is weakening on the watchlist.")

    return changes


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

    if "market_change_pct" in source:
        briefing["market_state"] = derive_market_state(source["market_change_pct"])

    if "usd_jpy" in source:
        briefing["fx_state"] = derive_fx_state(source["usd_jpy"])

    for key in briefing:
        if key in source and key != "fx_state":
            value = source[key]
            briefing[key] = list(value) if isinstance(value, list) else value

    if not briefing["key_changes"]:
        briefing["key_changes"] = summarize_key_changes(briefing)

    return briefing
