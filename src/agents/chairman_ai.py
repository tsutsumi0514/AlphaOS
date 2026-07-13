"""Top-level orchestration agent for AlphaOS briefings."""

from __future__ import annotations

from collections.abc import Mapping
from uuid import uuid4
from typing import Any

from ..briefing import build_briefing
from ..learning.feedback import build_learning_summary
from .decision_ai import build_decision_ai
from .risk_ai import review_risk


def compose_briefing(
    source: Mapping[str, Any] | None = None,
    learning_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the briefing and let the risk agent own the risk view."""
    briefing = build_briefing(source)
    briefing["briefing_id"] = str(uuid4())
    if learning_summary is None:
        learning_summary = build_learning_summary()
    else:
        learning_summary = dict(learning_summary)

    briefing["learning_summary"] = learning_summary
    briefing["risk_alerts"] = review_risk(briefing)

    _apply_learning_reflection(briefing, learning_summary)
    briefing["decision_ai"] = build_decision_ai(briefing)

    return briefing


def _apply_learning_reflection(briefing: dict[str, Any], learning_summary: dict[str, Any]) -> None:
    status = learning_summary.get("status")
    if not isinstance(status, str):
        return

    note_by_status = {
        "strong": "Recent learning is stable. Keep following the current signal mix.",
        "moderate": "Recent learning is mixed. Keep position sizing conservative.",
        "weak": "Recent learning is weak. Use signals with extra caution.",
    }
    note = note_by_status.get(status)
    if not isinstance(note, str):
        return

    _append_unique(briefing.setdefault("key_changes", []), note)
    _append_unique(briefing.setdefault("reasons", []), note)

    if status == "weak":
        _append_unique(briefing.setdefault("risk_alerts", []), note)


def _append_unique(items: list[Any], value: str) -> None:
    if value not in items:
        items.append(value)
