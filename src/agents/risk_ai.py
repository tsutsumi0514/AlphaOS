"""Risk-focused briefing agent for AlphaOS."""

from __future__ import annotations

from ..analyzers.briefing_signals import summarize_risk_alerts


def review_risk(briefing: dict) -> list[str]:
    """Return the compact risk view for a briefing."""
    return summarize_risk_alerts(briefing)
