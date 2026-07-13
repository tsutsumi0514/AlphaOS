"""Learning feedback helpers for AlphaOS."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .backtest import backtest_history, summarize_backtest
from ..storage.briefing_history import load_briefing_history
from ..storage.outcome_history import load_market_outcomes

PERIOD_WINDOWS = (5, 20)


def build_learning_summary(
    history: list[dict[str, Any]] | None = None,
    outcomes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Summarize historical briefing accuracy for reflection in the next briefing."""
    if history is None:
        history = load_briefing_history()
    if outcomes is None:
        outcomes = load_market_outcomes()

    outcomes_by_id: dict[str, Mapping[str, Any]] = {}
    for record in outcomes:
        briefing_id = record.get("briefing_id")
        outcome = record.get("outcome")
        if isinstance(briefing_id, str) and isinstance(outcome, Mapping):
            outcomes_by_id[briefing_id] = outcome

    results = backtest_history(history, outcomes_by_id)
    summary = summarize_backtest(results)
    periods = _build_period_summaries(results)

    sample_size = int(summary.get("total", 0))
    accuracy = summary.get("weighted_accuracy", summary.get("accuracy"))

    if sample_size == 0:
        return {
            "status": "insufficient",
            "sample_size": 0,
            "accuracy": None,
            "weighted_accuracy": None,
            "notes": ["No matched outcomes yet."],
            "periods": periods,
        }

    if isinstance(accuracy, (int, float)) and accuracy < 0.5:
        status = "weak"
        notes = ["Recent forecast accuracy is low. Treat signals carefully."]
    elif isinstance(accuracy, (int, float)) and accuracy < 0.8:
        status = "moderate"
        notes = ["Recent forecast accuracy is mixed."]
    else:
        status = "strong"
        notes = ["Recent forecast accuracy is stable."]

    return {
        "status": status,
        "sample_size": sample_size,
        "accuracy": accuracy,
        "weighted_accuracy": summary.get("weighted_accuracy"),
        "notes": notes,
        "summary": summary,
        "periods": periods,
    }


def _build_period_summaries(
    results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    periods: dict[str, dict[str, Any]] = {}
    periods["all"] = summarize_backtest(results)

    for window in PERIOD_WINDOWS:
        periods[f"recent_{window}"] = summarize_backtest(results[-window:])

    return periods
