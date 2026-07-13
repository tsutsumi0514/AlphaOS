"""Utilities for building AlphaOS briefing payloads."""

from collections.abc import Mapping
from typing import Any

Briefing = dict[str, Any]

DEFAULT_BRIEFING: Briefing = {
    "headline": "Market overview is not ready yet.",
    "market_state": "unknown",
    "fx_state": "unknown",
    "news_item": None,
    "watchlist_status": [],
    "risk_alerts": [],
    "key_changes": [],
    "reasons": [],
    "confidence": "low",
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

    news_item = _news_item(briefing)
    if news_item is not None:
        title = news_item.get("title")
        source = news_item.get("source")
        if isinstance(title, str) and title.strip():
            news_sentence = f"News: {title.strip()}"
            if isinstance(source, str) and source.strip():
                news_sentence += f" ({source.strip()})"
            changes.append(f"{news_sentence}.")

    for item in _watchlist_items(briefing):
        symbol = item.get("symbol", "Watchlist")
        status = item.get("status")
        if status == "strong":
            changes.append(f"{symbol} is showing strong watchlist momentum.")
        elif status == "weak":
            changes.append(f"{symbol} is weakening on the watchlist.")

    return changes


def summarize_risk_alerts(briefing: Briefing) -> list[str]:
    """Build short risk-oriented alerts from the current briefing state."""
    alerts: list[str] = []

    market_state = briefing.get("market_state")
    fx_state = briefing.get("fx_state")

    if market_state == "bearish":
        alerts.append("Market tone is bearish. Keep new positions small.")

    if fx_state == "strong yen":
        alerts.append("Strong yen may pressure export-related names.")

    for item in _watchlist_items(briefing):
        symbol = item.get("symbol", "Watchlist")
        status = item.get("status")
        if status == "weak":
            alerts.append(f"{symbol} is weakening. Review entry timing carefully.")

    if market_state == "bearish" and fx_state == "strong yen":
        alerts.append("Both market and currency conditions are risk-off.")

    return alerts


def summarize_reasons(briefing: Briefing) -> list[str]:
    """Build short reason statements for the current briefing."""
    reasons: list[str] = []

    market_state = briefing.get("market_state")
    if market_state == "bullish":
        reasons.append("Nikkei day-over-day change is positive.")
    elif market_state == "bearish":
        reasons.append("Nikkei day-over-day change is negative.")

    fx_state = briefing.get("fx_state")
    if fx_state == "weak yen":
        reasons.append("USD/JPY is in a weak-yen range.")
    elif fx_state == "strong yen":
        reasons.append("USD/JPY is in a strong-yen range.")

    for item in _watchlist_items(briefing):
        symbol = item.get("symbol", "Watchlist")
        status = item.get("status")
        if status == "strong":
            reasons.append(f"{symbol} is rising strongly versus the previous close.")
        elif status == "weak":
            reasons.append(f"{symbol} is weakening versus the previous close.")
        elif status == "steady":
            reasons.append(f"{symbol} is moving within a normal daily range.")

    return reasons


def _watchlist_items(briefing: Briefing) -> list[Mapping[str, Any]]:
    watchlist_status = briefing.get("watchlist_status")
    if not isinstance(watchlist_status, list):
        return []

    items: list[Mapping[str, Any]] = []
    for item in watchlist_status:
        if isinstance(item, Mapping):
            items.append(item)
    return items


def _news_item(briefing: Briefing) -> Mapping[str, Any] | None:
    news_item = briefing.get("news_item")
    if isinstance(news_item, Mapping):
        return news_item
    return None


def _primary_watchlist_item(briefing: Briefing) -> Mapping[str, Any] | None:
    items = _watchlist_items(briefing)
    if not items:
        return None

    for item in items:
        if item.get("status") in {"strong", "weak"}:
            return item

    return items[0]


def derive_confidence(briefing: Briefing) -> str:
    """Estimate confidence from how many data-backed signals are available."""
    score = 0

    if briefing.get("market_state") != "unknown":
        score += 1
    if briefing.get("fx_state") != "unknown":
        score += 1

    if _watchlist_items(briefing):
        score += 1
    if _news_item(briefing) is not None:
        score += 1

    if score >= 3:
        return "high"
    if score == 2:
        return "medium"
    return "low"


def summarize_headline(briefing: Briefing) -> str:
    """Build a one-line headline for a fast morning read."""
    market_state = briefing.get("market_state")
    fx_state = briefing.get("fx_state")
    watchlist_item = _primary_watchlist_item(briefing)

    headline_parts: list[str] = []

    if market_state == "bullish":
        headline_parts.append("Nikkei is firm")
    elif market_state == "bearish":
        headline_parts.append("Nikkei is under pressure")
    elif market_state == "neutral":
        headline_parts.append("Nikkei is steady")

    if fx_state == "weak yen":
        headline_parts.append("yen is weak")
    elif fx_state == "strong yen":
        headline_parts.append("yen is strong")
    elif fx_state == "neutral":
        headline_parts.append("FX is stable")

    if watchlist_item is not None:
        symbol = watchlist_item.get("symbol", "Watchlist")
        status = watchlist_item.get("status")
        if status == "strong":
            headline_parts.append(f"{symbol} is strong")
        elif status == "weak":
            headline_parts.append(f"{symbol} is weak")
        elif status == "steady":
            headline_parts.append(f"{symbol} is steady")

    if headline_parts:
        return ". ".join(headline_parts) + "."

    return DEFAULT_BRIEFING["headline"]


def build_briefing(source: Mapping[str, Any] | None = None) -> Briefing:
    """Return a briefing payload, optionally merging values from source."""
    briefing: Briefing = {
        "headline": DEFAULT_BRIEFING["headline"],
        "market_state": DEFAULT_BRIEFING["market_state"],
        "fx_state": DEFAULT_BRIEFING["fx_state"],
        "news_item": DEFAULT_BRIEFING["news_item"],
        "watchlist_status": list(DEFAULT_BRIEFING["watchlist_status"]),
        "risk_alerts": list(DEFAULT_BRIEFING["risk_alerts"]),
        "key_changes": list(DEFAULT_BRIEFING["key_changes"]),
        "reasons": list(DEFAULT_BRIEFING["reasons"]),
        "confidence": DEFAULT_BRIEFING["confidence"],
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

    if not briefing["risk_alerts"]:
        briefing["risk_alerts"] = summarize_risk_alerts(briefing)

    if not briefing["key_changes"]:
        briefing["key_changes"] = summarize_key_changes(briefing)

    if briefing["headline"] == DEFAULT_BRIEFING["headline"]:
        briefing["headline"] = summarize_headline(briefing)

    if not briefing["reasons"]:
        briefing["reasons"] = summarize_reasons(briefing)

    if briefing["confidence"] == "low":
        briefing["confidence"] = derive_confidence(briefing)

    return briefing
