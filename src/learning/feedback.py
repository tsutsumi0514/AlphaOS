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
    backtest_summary = summarize_backtest(results)
    periods = _build_period_summaries(results)

    sample_size = int(backtest_summary.get("total", 0))
    accuracy = backtest_summary.get("weighted_accuracy", backtest_summary.get("accuracy"))

    if sample_size == 0:
        learning_summary = {
            "status": "insufficient",
            "sample_size": 0,
            "accuracy": None,
            "weighted_accuracy": None,
            "notes": ["No matched outcomes yet."],
            "periods": periods,
        }
        learning_summary["candidate_profile"] = build_candidate_learning_profile(learning_summary)
        return learning_summary

    if isinstance(accuracy, (int, float)) and accuracy < 0.5:
        status = "weak"
        notes = ["Recent forecast accuracy is low. Treat signals carefully."]
    elif isinstance(accuracy, (int, float)) and accuracy < 0.8:
        status = "moderate"
        notes = ["Recent forecast accuracy is mixed."]
    else:
        status = "strong"
        notes = ["Recent forecast accuracy is stable."]

    learning_summary = {
        "status": status,
        "sample_size": sample_size,
        "accuracy": accuracy,
        "weighted_accuracy": backtest_summary.get("weighted_accuracy"),
        "notes": notes,
        "summary": backtest_summary,
        "periods": periods,
    }
    learning_summary["candidate_profile"] = build_candidate_learning_profile(learning_summary)
    return learning_summary


def build_candidate_learning_profile(summary: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if summary is None:
        summary = build_learning_summary()
    if not isinstance(summary, Mapping):
        return _empty_candidate_profile()

    sample_size = _int(summary.get("sample_size"))
    accuracy = _float(summary.get("accuracy"))
    weighted_accuracy = _float(summary.get("weighted_accuracy"))
    periods = summary.get("periods")
    recent_weighted_accuracy = weighted_accuracy
    if isinstance(periods, Mapping):
        recent_5 = periods.get("recent_5")
        if isinstance(recent_5, Mapping):
            recent_weighted_accuracy = _float(recent_5.get("weighted_accuracy"), weighted_accuracy)

    support_gap = recent_weighted_accuracy - weighted_accuracy

    if sample_size <= 0:
        return {
            "status": "insufficient",
            "sample_size": 0,
            "accuracy": None,
            "weighted_accuracy": None,
            "recent_weighted_accuracy": None,
            "score_adjustment": 0.0,
            "confidence_adjustment": 0.0,
            "exclusion_bias": "strict",
            "timing_bias": "wait",
            "support_gap": 0.0,
            "notes": ["No matched outcomes yet."],
        }

    if weighted_accuracy >= 0.8 and recent_weighted_accuracy >= 0.75 and sample_size >= 5:
        status = "strong"
        score_adjustment = 0.04
        confidence_adjustment = 0.05
        exclusion_bias = "relaxed"
        timing_bias = "buy_now"
        note = "Recent learning supports stronger candidate selection."
    elif weighted_accuracy >= 0.6:
        status = "moderate"
        score_adjustment = 0.01
        confidence_adjustment = 0.02
        exclusion_bias = "normal"
        timing_bias = "wait"
        note = "Recent learning is mixed. Keep candidate selection balanced."
    else:
        status = "weak"
        score_adjustment = -0.04
        confidence_adjustment = -0.05
        exclusion_bias = "strict"
        timing_bias = "avoid"
        note = "Recent learning is weak. Use extra filtering."

    if support_gap > 0.05:
        score_adjustment += 0.01
        note = "Recent learning is improving."
    elif support_gap < -0.05:
        score_adjustment -= 0.01
        note = "Recent learning is deteriorating."

    return {
        "status": status,
        "sample_size": sample_size,
        "accuracy": accuracy,
        "weighted_accuracy": weighted_accuracy,
        "recent_weighted_accuracy": recent_weighted_accuracy,
        "score_adjustment": round(score_adjustment, 4),
        "confidence_adjustment": round(confidence_adjustment, 4),
        "exclusion_bias": exclusion_bias,
        "timing_bias": timing_bias,
        "support_gap": round(support_gap, 4),
        "notes": [note],
    }


def _build_period_summaries(
    results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    periods: dict[str, dict[str, Any]] = {}
    periods["all"] = summarize_backtest(results)

    for window in PERIOD_WINDOWS:
        periods[f"recent_{window}"] = summarize_backtest(results[-window:])

    return periods


def _empty_candidate_profile() -> dict[str, Any]:
    return {
        "status": "insufficient",
        "sample_size": 0,
        "accuracy": None,
        "weighted_accuracy": None,
        "recent_weighted_accuracy": None,
        "score_adjustment": 0.0,
        "confidence_adjustment": 0.0,
        "exclusion_bias": "strict",
        "timing_bias": "wait",
        "support_gap": 0.0,
        "notes": ["No matched outcomes yet."],
    }


def _float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return default


def _int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return default
