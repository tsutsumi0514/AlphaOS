"""Macro perspective helper for AlphaOS V4."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def review_macro(briefing: Mapping[str, Any]) -> dict[str, Any]:
    market_state = _text(briefing.get("market_state"), "unknown")
    fx_state = _text(briefing.get("fx_state"), "unknown")

    signals: list[str] = []
    if market_state == "bullish":
        signals.append("Equity momentum is positive.")
    elif market_state == "bearish":
        signals.append("Equity momentum is weak.")
    else:
        signals.append("Equity momentum is mixed.")

    if fx_state == "weak yen":
        signals.append("FX is supporting exporters.")
    elif fx_state == "strong yen":
        signals.append("FX is pressuring exporters.")
    else:
        signals.append("FX is neutral.")

    if market_state == "bullish" and fx_state == "weak yen":
        stance = "risk-on"
        summary = "Macro conditions lean supportive for Japanese equities."
    elif market_state == "bearish" and fx_state == "strong yen":
        stance = "risk-off"
        summary = "Macro conditions lean defensive for Japanese equities."
    else:
        stance = "balanced"
        summary = "Macro signals are mixed and need risk control."

    return {
        "agent": "MacroAI",
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
