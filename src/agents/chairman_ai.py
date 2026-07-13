"""Top-level orchestration agent for AlphaOS briefings."""

from __future__ import annotations

from collections.abc import Mapping
from uuid import uuid4
from typing import Any

from ..briefing import build_briefing
from ..learning.feedback import build_learning_summary
from .risk_ai import review_risk


def compose_briefing(source: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build the briefing and let the risk agent own the risk view."""
    briefing = build_briefing(source)
    briefing["briefing_id"] = str(uuid4())
    briefing["learning_summary"] = build_learning_summary()
    briefing["risk_alerts"] = review_risk(briefing)

    learning_summary = briefing.get("learning_summary")
    if isinstance(learning_summary, dict) and learning_summary.get("status") == "weak":
        notes = learning_summary.get("notes")
        if isinstance(notes, list):
            notes.append("Apply extra caution until accuracy improves.")
        briefing["risk_alerts"] = [
            *briefing.get("risk_alerts", []),
            "Historical accuracy is weak. Use signals carefully.",
        ]

    return briefing
