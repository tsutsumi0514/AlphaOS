"""Signal analysis helpers for AlphaOS briefings."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..evidence import Evidence


Briefing = dict[str, Any]


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


def summarize_evidence(
    briefing: Briefing, source: Mapping[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Build structured evidence items from the current briefing state."""
    evidence: list[dict[str, Any]] = []

    market_change_pct = _source_or_briefing_value(source, briefing, "market_change_pct")
    if market_change_pct is not None:
        evidence.append(
            Evidence(
                source="market",
                label="Nikkei day-over-day change",
                value=market_change_pct,
                note=briefing.get("market_state"),
            ).to_dict()
        )

    usd_jpy = _source_or_briefing_value(source, briefing, "usd_jpy")
    if usd_jpy is not None:
        evidence.append(
            Evidence(
                source="fx",
                label="USD/JPY",
                value=usd_jpy,
                note=briefing.get("fx_state"),
            ).to_dict()
        )

    news_item = _news_item(briefing)
    if news_item is not None:
        title = news_item.get("title")
        source_name = news_item.get("source")
        if isinstance(title, str) and title.strip():
            evidence.append(
                Evidence(
                    source="news",
                    label="Latest market news",
                    value=title.strip(),
                    note=source_name.strip()
                    if isinstance(source_name, str) and source_name.strip()
                    else None,
                ).to_dict()
            )

    for item in _watchlist_items(briefing):
        symbol = item.get("symbol")
        if isinstance(symbol, str) and symbol.strip():
            note_parts: list[str] = []
            if "status" in item:
                note_parts.append(f"status={item.get('status')}")
            if "price" in item:
                note_parts.append(f"price={item.get('price')}")
            if "change_pct" in item:
                note_parts.append(f"change_pct={item.get('change_pct')}")

            evidence.append(
                Evidence(
                    source="watchlist",
                    label=symbol.strip(),
                    value=item.get("status"),
                    note=", ".join(note_parts) if note_parts else None,
                ).to_dict()
            )

    return evidence


def derive_confidence(briefing: Briefing) -> str:
    """Estimate confidence from how many data-backed signals are available."""
    score = 0

    if briefing.get("market_state") != "unknown":
        score += 1
    if briefing.get("fx_state") != "unknown":
        score += 1

    if _evidence_items(briefing):
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

    return "Market overview is not ready yet."


def _source_or_briefing_value(
    source: Mapping[str, Any] | None, briefing: Briefing, key: str
) -> Any:
    if source is not None and key in source:
        return source[key]
    return briefing.get(key)


def _evidence_items(briefing: Briefing) -> list[Mapping[str, Any]]:
    evidence = briefing.get("evidence")
    if not isinstance(evidence, list):
        return []

    items: list[Mapping[str, Any]] = []
    for item in evidence:
        if isinstance(item, Evidence):
            items.append(item.to_dict())
        elif isinstance(item, Mapping):
            items.append(dict(item))
    return items


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
