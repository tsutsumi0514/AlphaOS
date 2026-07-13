"""Top-level orchestration agent for AlphaOS briefings."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..briefing import build_briefing
from .risk_ai import review_risk


def compose_briefing(source: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build the briefing and let the risk agent own the risk view."""
    briefing = build_briefing(source)
    briefing["risk_alerts"] = review_risk(briefing)
    return briefing
