"""Historical replay helpers for AlphaOS V4."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import date, datetime
from typing import Any

from ..agents.chairman_ai import compose_briefing
from ..agents.decision_ai import build_decision_ai
from ..briefing import (
    derive_confidence,
    summarize_evidence,
    summarize_headline,
    summarize_key_changes,
    summarize_reasons,
    summarize_risk_alerts,
)
from ..learning.backtest import (
    CHECK_WEIGHTS,
    ReplayThresholds,
    score_briefing_against_outcome,
    summarize_backtest,
)
from ..storage.news_history import find_latest_news_before
from ..watchlist import DEFAULT_WATCHLIST_SYMBOLS

HistoryLoader = Callable[[str, str], list[tuple[date, float]]]


REPLAY_LEARNING_SUMMARY: dict[str, Any] = {
    "status": "insufficient",
    "sample_size": 0,
    "accuracy": None,
    "weighted_accuracy": None,
    "notes": ["Replay mode uses only historical market inputs."],
    "periods": {"all": {"total": 0}},
}


def run_replay_simulation(
    lookback_trading_days: int = 20,
    symbols: tuple[str, ...] = DEFAULT_WATCHLIST_SYMBOLS,
    period: str = "6mo",
    history_loader: HistoryLoader | None = None,
    calibrate: bool = True,
) -> dict[str, Any]:
    """Run a replay simulation over historical daily market data."""
    loader = history_loader or _load_close_history
    symbols = symbols or DEFAULT_WATCHLIST_SYMBOLS

    benchmark = loader("^N225", period)
    fx = loader("JPY=X", period)
    watchlist = {symbol: loader(symbol, period) for symbol in symbols}

    records = _build_records(benchmark, fx, watchlist)
    if not records:
        return {
            "mode": "replay",
            "sample_size": 0,
            "summary": {"total": 0, "matched": 0, "checks": 0, "accuracy": 0.0},
            "calibration": {
                "enabled": calibrate,
                "thresholds": ReplayThresholds().__dict__,
                "summary": {"total": 0, "matched": 0, "checks": 0, "accuracy": 0.0},
            },
            "baseline": {
                "summary": {"total": 0, "matched": 0, "checks": 0, "accuracy": 0.0},
            },
            "results": [],
            "notes": [
                "NewsAI is intentionally neutral in replay mode because no archived news store exists yet."
            ],
        }

    window_records = records[-lookback_trading_days:] if lookback_trading_days > 0 else records
    thresholds = (
        calibrate_replay_thresholds(window_records) if calibrate else ReplayThresholds()
    )
    calibration_summary = _score_records(window_records, thresholds)
    baseline_summary = _score_records(window_records, ReplayThresholds())
    validation = run_walk_forward_validation(records)
    results: list[dict[str, Any]] = []

    for record in window_records:
        briefing = _compose_replay_briefing(record["source"], thresholds)
        result = score_briefing_against_outcome(
            briefing, record["outcome"], thresholds=thresholds
        )
        results.append(
            {
                "briefing_date": record["briefing_date"].isoformat(),
                "outcome_date": record["outcome_date"].isoformat(),
                "briefing": briefing,
                "outcome": record["outcome"],
                "result": result,
            }
        )

    summary = summarize_backtest(results)
    return {
        "mode": "replay",
        "sample_size": len(results),
        "summary": summary,
        "calibration": {
            "enabled": calibrate,
            "thresholds": thresholds.__dict__,
            "summary": calibration_summary,
        },
        "baseline": {
            "thresholds": ReplayThresholds().__dict__,
            "summary": baseline_summary,
        },
        "validation": validation,
        "results": results,
        "notes": [
            "Archived news is used when a dated match exists in the local news archive."
            if calibrate
            else "Replay mode is running without calibration.",
        ],
    }


def calibrate_replay_thresholds(records: list[dict[str, Any]]) -> ReplayThresholds:
    market_candidates = _market_candidates(records)
    fx_candidates = _fx_candidates(records)
    watchlist_candidates = _watchlist_candidates(records)

    market_threshold = _best_market_threshold(records, market_candidates)
    fx_thresholds = _best_fx_threshold(records, fx_candidates)
    watchlist_threshold = _best_watchlist_threshold(records, watchlist_candidates)

    return ReplayThresholds(
        market_move_pct=market_threshold,
        fx_weak_yen=fx_thresholds[0],
        fx_strong_yen=fx_thresholds[1],
        watchlist_move_pct=watchlist_threshold,
    )


def _score_records(
    records: list[dict[str, Any]], thresholds: ReplayThresholds
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for record in records:
        briefing = _compose_replay_briefing(record["source"], thresholds)
        result = score_briefing_against_outcome(
            briefing, record["outcome"], thresholds=thresholds
        )
        results.append({"result": result})
    return summarize_backtest(results)


def run_walk_forward_validation(
    records: list[dict[str, Any]],
    training_window: int = 20,
    evaluation_window: int = 5,
) -> dict[str, Any]:
    if len(records) < training_window + evaluation_window:
        return {
            "mode": "walk_forward",
            "sample_size": 0,
            "summary": {"total": 0, "matched": 0, "checks": 0, "accuracy": 0.0},
            "baseline": {"summary": {"total": 0, "matched": 0, "checks": 0, "accuracy": 0.0}},
            "folds": [],
            "windows": {
                "training_window": training_window,
                "evaluation_window": evaluation_window,
            },
        }

    folds: list[dict[str, Any]] = []
    evaluated_results: list[dict[str, Any]] = []
    baseline_results: list[dict[str, Any]] = []

    start = training_window
    while start < len(records):
        train_records = records[:start]
        eval_records = records[start : min(len(records), start + evaluation_window)]
        if not train_records or not eval_records:
            break

        thresholds = calibrate_replay_thresholds(train_records)
        fold_results = _score_records(eval_records, thresholds)
        baseline_fold_results = _score_records(eval_records, ReplayThresholds())

        folds.append(
            {
                "train_range": {
                    "start": train_records[0]["briefing_date"].isoformat(),
                    "end": train_records[-1]["briefing_date"].isoformat(),
                },
                "eval_range": {
                    "start": eval_records[0]["briefing_date"].isoformat(),
                    "end": eval_records[-1]["outcome_date"].isoformat(),
                },
                "thresholds": thresholds.__dict__,
                "summary": fold_results,
                "baseline": baseline_fold_results,
            }
        )
        evaluated_results.extend({"result": result["result"]} for result in _fold_result_items(eval_records, thresholds))
        baseline_results.extend({"result": result["result"]} for result in _fold_result_items(eval_records, ReplayThresholds()))
        start += evaluation_window

    summary = summarize_backtest(evaluated_results)
    baseline_summary = summarize_backtest(baseline_results)
    return {
        "mode": "walk_forward",
        "sample_size": len(evaluated_results),
        "summary": summary,
        "baseline": {"summary": baseline_summary},
        "folds": folds,
        "windows": {
            "training_window": training_window,
            "evaluation_window": evaluation_window,
        },
    }


def _fold_result_items(
    records: list[dict[str, Any]], thresholds: ReplayThresholds
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for record in records:
        briefing = _compose_replay_briefing(record["source"], thresholds)
        result = score_briefing_against_outcome(
            briefing, record["outcome"], thresholds=thresholds
        )
        items.append(
            {
                "briefing_date": record["briefing_date"].isoformat(),
                "outcome_date": record["outcome_date"].isoformat(),
                "result": result,
            }
        )
    return items


def _compose_replay_briefing(
    source: Mapping[str, Any], thresholds: ReplayThresholds
) -> dict[str, Any]:
    replay_source = dict(source)
    if "news_item" not in replay_source or replay_source.get("news_item") is None:
        replay_source["news_item"] = find_latest_news_before(
            replay_source.get("briefing_date")
        )

    briefing = compose_briefing(replay_source, learning_summary=REPLAY_LEARNING_SUMMARY)
    _apply_replay_thresholds(briefing, source, thresholds)
    briefing["decision_ai"] = build_decision_ai(briefing)
    return briefing


def _apply_replay_thresholds(
    briefing: dict[str, Any], source: Mapping[str, Any], thresholds: ReplayThresholds
) -> None:
    market_change_pct = source.get("market_change_pct")
    usd_jpy = source.get("usd_jpy")
    watchlist_status = source.get("watchlist_status")

    briefing["market_state"] = _classify_market_state(
        market_change_pct, thresholds.market_move_pct
    )
    briefing["fx_state"] = _classify_fx_state(
        usd_jpy, thresholds.fx_weak_yen, thresholds.fx_strong_yen
    )
    briefing["watchlist_status"] = _relabel_watchlist(
        watchlist_status, thresholds.watchlist_move_pct
    )
    briefing["evidence"] = summarize_evidence(briefing, source)
    briefing["risk_alerts"] = summarize_risk_alerts(briefing)
    briefing["key_changes"] = summarize_key_changes(briefing)
    briefing["reasons"] = summarize_reasons(briefing)
    briefing["headline"] = summarize_headline(briefing)
    briefing["confidence"] = derive_confidence(briefing)


def _market_candidates(records: list[dict[str, Any]]) -> list[float]:
    candidates: set[float] = {0.1, 0.2, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 4.0}
    for record in records:
        for key in ("source", "outcome"):
            value = record[key].get("market_change_pct")
            if isinstance(value, (int, float)):
                candidates.add(round(abs(float(value)), 6))
    return sorted(candidate for candidate in candidates if candidate > 0)


def _fx_candidates(records: list[dict[str, Any]]) -> list[float]:
    candidates: set[float] = {140.0, 142.0, 144.0, 145.0, 146.0, 148.0, 150.0, 152.0, 154.0, 155.0, 156.0, 158.0, 160.0}
    for record in records:
        for key in ("source", "outcome"):
            value = record[key].get("usd_jpy")
            if isinstance(value, (int, float)):
                candidates.add(round(float(value), 6))
    return sorted(candidates)


def _watchlist_candidates(records: list[dict[str, Any]]) -> list[float]:
    candidates: set[float] = {0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.5}
    for record in records:
        for key in ("source", "outcome"):
            watchlist = record[key].get("watchlist_status")
            if not isinstance(watchlist, list):
                continue
            for item in watchlist:
                if not isinstance(item, Mapping):
                    continue
                change_pct = item.get("change_pct")
                if isinstance(change_pct, (int, float)):
                    candidates.add(round(abs(float(change_pct)), 6))
    return sorted(candidate for candidate in candidates if candidate > 0)


def _best_market_threshold(records: list[dict[str, Any]], candidates: list[float]) -> float:
    best_threshold = 0.7
    best_score = -1.0
    for threshold in candidates:
        summary = _threshold_summary(records, ReplayThresholds(market_move_pct=threshold))
        score = _threshold_score(summary)
        if score > best_score:
            best_score = score
            best_threshold = threshold
    return best_threshold


def _best_fx_threshold(records: list[dict[str, Any]], candidates: list[float]) -> tuple[float, float]:
    best_pair = (155.0, 145.0)
    best_score = -1.0
    for strong in candidates:
        for weak in candidates:
            if strong >= weak:
                continue
            summary = _threshold_summary(
                records,
                ReplayThresholds(fx_weak_yen=weak, fx_strong_yen=strong),
            )
            score = _threshold_score(summary)
            if score > best_score:
                best_score = score
                best_pair = (weak, strong)
    return best_pair


def _best_watchlist_threshold(records: list[dict[str, Any]], candidates: list[float]) -> float:
    best_threshold = 2.0
    best_score = -1.0
    for threshold in candidates:
        summary = _threshold_summary(
            records, ReplayThresholds(watchlist_move_pct=threshold)
        )
        score = _threshold_score(summary)
        if score > best_score:
            best_score = score
            best_threshold = threshold
    return best_threshold


def _threshold_summary(
    records: list[dict[str, Any]], thresholds: ReplayThresholds
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for record in records:
        results.append({"result": _direct_score_record(record, thresholds)})
    return summarize_backtest(results)


def _threshold_score(summary: Mapping[str, Any]) -> float:
    coverage = float(summary.get("coverage", 0.0))
    weighted_accuracy = float(summary.get("weighted_accuracy", 0.0))
    active_accuracy = float(summary.get("active_accuracy", 0.0))
    if coverage < 0.35:
        return coverage * 0.5 + weighted_accuracy * 0.5
    return weighted_accuracy * 0.7 + active_accuracy * 0.3 + coverage * 0.1


def _direct_score_record(
    record: Mapping[str, Any], thresholds: ReplayThresholds
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    source = record["source"]
    outcome = record["outcome"]

    _append_direct_check(
        checks,
        "market_state",
        _classify_market_state(source.get("market_change_pct"), thresholds.market_move_pct),
        _classify_market_state(outcome.get("market_change_pct"), thresholds.market_move_pct),
        CHECK_WEIGHTS["market_state"],
    )
    _append_direct_check(
        checks,
        "fx_state",
        _classify_fx_state(source.get("usd_jpy"), thresholds.fx_weak_yen, thresholds.fx_strong_yen),
        _classify_fx_state(outcome.get("usd_jpy"), thresholds.fx_weak_yen, thresholds.fx_strong_yen),
        CHECK_WEIGHTS["fx_state"],
    )

    source_items = source.get("watchlist_status")
    outcome_items = outcome.get("watchlist_status")
    if isinstance(source_items, list) and isinstance(outcome_items, list):
        outcome_by_symbol = {
            item.get("symbol"): item
            for item in outcome_items
            if isinstance(item, Mapping) and isinstance(item.get("symbol"), str)
        }
        for item in source_items:
            if not isinstance(item, Mapping):
                continue
            symbol = item.get("symbol")
            if not isinstance(symbol, str):
                continue
            outcome_item = outcome_by_symbol.get(symbol)
            if outcome_item is None:
                continue
            predicted = _classify_watch_status(item.get("change_pct"), thresholds.watchlist_move_pct)
            actual = _classify_watch_status(outcome_item.get("change_pct"), thresholds.watchlist_move_pct)
            _append_direct_check(
                checks,
                f"watchlist:{symbol}",
                predicted,
                actual,
                CHECK_WEIGHTS["watchlist"],
            )

    matched = sum(1 for check in checks if check["matched"])
    total = len(checks)
    active_checks = sum(1 for check in checks if check["active"])
    active_matched = sum(1 for check in checks if check["active"] and check["matched"])
    weighted_matched = sum(check["weight"] for check in checks if check["matched"])
    weighted_total = sum(check["weight"] for check in checks)
    return {
        "matched": matched,
        "total": total,
        "accuracy": matched / total if total else 0.0,
        "active_checks": active_checks,
        "active_matched": active_matched,
        "coverage": active_checks / total if total else 0.0,
        "active_accuracy": active_matched / active_checks if active_checks else 0.0,
        "weighted_matched": weighted_matched,
        "weighted_total": weighted_total,
        "weighted_accuracy": weighted_matched / weighted_total if weighted_total else 0.0,
    }


def _append_direct_check(
    checks: list[dict[str, Any]], label: str, predicted: Any, actual: Any, weight: float
) -> None:
    checks.append(
        {
            "label": label,
            "predicted": predicted,
            "actual": actual,
            "matched": predicted == actual,
            "active": _is_active_prediction(label, predicted),
            "weight": weight,
        }
    )


def _is_active_prediction(label: str, predicted: Any) -> bool:
    if label == "market_state":
        return predicted in {"bullish", "bearish"}
    if label == "fx_state":
        return predicted in {"weak yen", "strong yen"}
    if label.startswith("watchlist:"):
        return predicted in {"strong", "weak"}
    return predicted not in {None, "unknown", "neutral", "steady"}


def _classify_market_state(market_change_pct: Any, threshold: float) -> str:
    if market_change_pct is None:
        return "unknown"
    if market_change_pct >= threshold:
        return "bullish"
    if market_change_pct <= -threshold:
        return "bearish"
    return "neutral"


def _classify_fx_state(usd_jpy: Any, weak_yen_threshold: float, strong_yen_threshold: float) -> str:
    if usd_jpy is None:
        return "unknown"
    if usd_jpy >= weak_yen_threshold:
        return "weak yen"
    if usd_jpy <= strong_yen_threshold:
        return "strong yen"
    return "neutral"


def _classify_watch_status(change_pct: Any, threshold: float) -> str:
    if change_pct is None:
        return "unknown"
    if change_pct >= threshold:
        return "strong"
    if change_pct <= -threshold:
        return "weak"
    return "steady"


def _relabel_watchlist(
    watchlist_status: Any, threshold: float
) -> list[dict[str, Any]]:
    if not isinstance(watchlist_status, list):
        return []

    relabeled: list[dict[str, Any]] = []
    for item in watchlist_status:
        if not isinstance(item, Mapping):
            continue
        symbol = item.get("symbol")
        if not isinstance(symbol, str) or not symbol.strip():
            continue
        change_pct = item.get("change_pct")
        relabeled.append(
            {
                "symbol": symbol.strip(),
                "price": item.get("price"),
                "change_pct": change_pct,
                "status": _classify_watch_status(change_pct, threshold),
            }
        )
    return relabeled


def _build_records(
    benchmark: list[tuple[date, float]],
    fx: list[tuple[date, float]],
    watchlist: Mapping[str, list[tuple[date, float]]],
) -> list[dict[str, Any]]:
    benchmark_map = {trade_date: close for trade_date, close in benchmark}
    fx_map = {trade_date: close for trade_date, close in fx}
    watchlist_maps = {symbol: {trade_date: close for trade_date, close in series} for symbol, series in watchlist.items()}

    common_dates = set(benchmark_map) & set(fx_map)
    if watchlist_maps:
        common_dates &= set.intersection(*(set(series) for series in watchlist_maps.values()))
    common_dates = sorted(common_dates)
    if len(common_dates) < 3:
        return []

    records: list[dict[str, Any]] = []
    for index in range(1, len(common_dates) - 1):
        briefing_date = common_dates[index]
        outcome_date = common_dates[index + 1]
        previous_date = common_dates[index - 1]

        source = {
            "briefing_date": briefing_date,
            "market_change_pct": _percent_change(
                benchmark_map.get(briefing_date), benchmark_map.get(previous_date)
            ),
            "usd_jpy": fx_map.get(briefing_date),
            "watchlist_status": _build_watchlist_snapshot(
                briefing_date, previous_date, watchlist_maps
            ),
        }
        outcome = {
            "market_change_pct": _percent_change(
                benchmark_map.get(outcome_date), benchmark_map.get(briefing_date)
            ),
            "usd_jpy": fx_map.get(outcome_date),
            "watchlist_status": _build_watchlist_outcome(
                outcome_date, briefing_date, watchlist_maps
            ),
        }

        records.append(
            {
                "briefing_date": briefing_date,
                "outcome_date": outcome_date,
                "source": source,
                "outcome": outcome,
            }
        )

    return records


def _build_watchlist_snapshot(
    briefing_date: date,
    previous_date: date,
    watchlist_maps: Mapping[str, Mapping[date, float]],
) -> list[dict[str, Any]]:
    snapshots: list[dict[str, Any]] = []
    for symbol, series in watchlist_maps.items():
        current = series.get(briefing_date)
        previous = series.get(previous_date)
        if current is None or previous in (None, 0):
            continue
        change_pct = _percent_change(current, previous)
        snapshots.append(
            {
                "symbol": symbol,
                "price": current,
                "change_pct": change_pct,
                "status": _classify_watch_status(change_pct, 2.0),
            }
        )
    return snapshots


def _build_watchlist_outcome(
    outcome_date: date,
    briefing_date: date,
    watchlist_maps: Mapping[str, Mapping[date, float]],
) -> list[dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    for symbol, series in watchlist_maps.items():
        current = series.get(outcome_date)
        previous = series.get(briefing_date)
        if current is None or previous in (None, 0):
            continue
        change_pct = _percent_change(current, previous)
        outcomes.append(
            {
                "symbol": symbol,
                "price": current,
                "change_pct": change_pct,
                "status": _classify_watch_status(change_pct, 2.0),
            }
        )
    return outcomes


def _percent_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return ((current - previous) / previous) * 100.0


def _load_close_history(symbol: str, period: str) -> list[tuple[date, float]]:
    try:
        import yfinance as yf
    except Exception:
        return []

    try:
        history = yf.Ticker(symbol).history(period=period, interval="1d")
    except Exception:
        return []

    if history is None or history.empty:
        return []

    close = history["Close"].dropna()
    rows: list[tuple[date, float]] = []
    for timestamp, value in close.items():
        trade_date = _to_date(timestamp)
        if trade_date is None:
            continue
        rows.append((trade_date, float(value)))

    rows.sort(key=lambda row: row[0])
    return rows


def _to_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if hasattr(value, "to_pydatetime"):
        try:
            return value.to_pydatetime().date()
        except Exception:
            return None
    return None
