"""News perspective helper for AlphaOS V4."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


POSITIVE_MARKERS = ("上昇", "好調", "改善", "追い風", "最高", "増益", "買い")
NEGATIVE_MARKERS = ("下落", "悪化", "懸念", "逆風", "減益", "売り", "低下")


def review_news(briefing: Mapping[str, Any]) -> dict[str, Any]:
    news_item = briefing.get("news_item")
    if not isinstance(news_item, Mapping):
        return {
            "agent": "NewsAI",
            "stance": "unknown",
            "summary": "Historical news is unavailable in this replay.",
            "signals": ["No archived news item was supplied."],
        }

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

    return {
        "agent": "NewsAI",
        "stance": stance,
        "summary": summary,
        "signals": signals,
    }


def _text(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if value is None:
        return default
    return str(value)
