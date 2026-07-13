"""Minimal backtesting helpers for AlphaOS."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ..briefing import derive_fx_state, derive_market_state
from ..watchlist import derive_watch_status

CHECK_WEIGHTS = {
    "market_state": 2.0,
    "fx_state": 2.0,
    "watchlist": 1.0,
}


def score_briefing_against_outcome(
    briefing: Mapping[str, Any], outcome: Mapping[str, Any]
) -> dict[str, Any]:
    """Score a briefing against actual market outcomes."""
    checks: list[dict[str, Any]] = []

    market_actual = derive_market_state(outcome.get("market_change_pct"))
    market_predicted = briefing.get("market_state")
    _append_check(
        checks,
        "market_state",
        market_predicted,
        market_actual,
        CHECK_WEIGHTS["market_state"],
    )

    fx_actual = derive_fx_state(outcome.get("usd_jpy"))
    fx_predicted = briefing.get("fx_state")
    _append_check(
        checks,
        "fx_state",
        fx_predicted,
        fx_actual,
        CHECK_WEIGHTS["fx_state"],
    )

    watchlist_checks = _score_watchlist(
        briefing.get("watchlist_status"), outcome.get("watchlist_status")
    )
    checks.extend(watchlist_checks)

    matched = sum(1 for check in checks if check["matched"])
    total = len(checks)
    accuracy = matched / total if total else 0.0
    weighted_matched = sum(check["weight"] for check in checks if check["matched"])
    weighted_total = sum(check["weight"] for check in checks)
    weighted_accuracy = weighted_matched / weighted_total if weighted_total else 0.0

    return {
        "matched": matched,
        "total": total,
        "accuracy": accuracy,
        "weighted_matched": weighted_matched,
        "weighted_total": weighted_total,
        "weighted_accuracy": weighted_accuracy,
        "checks": checks,
    }


def backtest_history(
    history: Sequence[Mapping[str, Any]],
    outcomes_by_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Score each stored briefing record against a matching outcome."""
    results: list[dict[str, Any]] = []
    for record in history:
        briefing_id = record.get("briefing_id")
        if not isinstance(briefing_id, str):
            continue

        outcome = outcomes_by_id.get(briefing_id)
        if outcome is None:
            continue

        briefing = record.get("briefing")
        if not isinstance(briefing, Mapping):
            continue

        result = score_briefing_against_outcome(briefing, outcome)
        results.append(
            {
                "briefing_id": briefing_id,
                "recorded_at": record.get("recorded_at"),
                "result": result,
            }
        )

    return results


def summarize_backtest(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate backtest results into a compact summary."""
    total = len(results)
    if total == 0:
        return {
            "total": 0,
            "matched": 0,
            "accuracy": 0.0,
            "weighted_matched": 0.0,
            "weighted_total": 0.0,
            "weighted_accuracy": 0.0,
        }

    matched = 0
    checks = 0
    weighted_matched = 0.0
    weighted_total = 0.0
    for result in results:
        payload = result.get("result")
        if not isinstance(payload, Mapping):
            continue
        matched += int(payload.get("matched", 0))
        checks += int(payload.get("total", 0))
        weighted_matched += float(payload.get("weighted_matched", payload.get("matched", 0)))
        weighted_total += float(payload.get("weighted_total", payload.get("total", 0)))

    accuracy = matched / checks if checks else 0.0
    weighted_accuracy = weighted_matched / weighted_total if weighted_total else 0.0
    return {
        "total": total,
        "matched": matched,
        "checks": checks,
        "accuracy": accuracy,
        "weighted_matched": weighted_matched,
        "weighted_total": weighted_total,
        "weighted_accuracy": weighted_accuracy,
    }


def _append_check(
    checks: list[dict[str, Any]], label: str, predicted: Any, actual: Any, weight: float
) -> None:
    checks.append(
        {
            "label": label,
            "predicted": predicted,
            "actual": actual,
            "matched": predicted == actual,
            "weight": weight,
        }
    )


def _score_watchlist(
    predicted_items: Any, actual_items: Any
) -> list[dict[str, Any]]:
    if not isinstance(predicted_items, list) or not isinstance(actual_items, list):
        return []

    actual_by_symbol = {}
    for item in actual_items:
        if isinstance(item, Mapping):
            symbol = item.get("symbol")
            if isinstance(symbol, str):
                actual_by_symbol[symbol] = item

    checks: list[dict[str, Any]] = []
    for item in predicted_items:
        if not isinstance(item, Mapping):
            continue
        symbol = item.get("symbol")
        if not isinstance(symbol, str):
            continue
        actual = actual_by_symbol.get(symbol)
        if actual is None:
            continue

        predicted_status = item.get("status")
        actual_status = actual.get("status")
        if actual_status is None:
            change_pct = actual.get("change_pct")
            actual_status = derive_watch_status(change_pct)

        checks.append(
            {
                "label": f"watchlist:{symbol}",
                "predicted": predicted_status,
                "actual": actual_status,
                "matched": predicted_status == actual_status,
                "weight": CHECK_WEIGHTS["watchlist"],
            }
        )

    return checks
