"""Opportunity validation helpers for AlphaOS."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import date
from statistics import mean, median, pstdev
from typing import Any

from ..learning.backtest import ReplayThresholds
from ..opportunity import evaluate_candidate_pool
from ..watchlist import DEFAULT_WATCHLIST_SYMBOLS
from .replay import _build_records
from .replay import _compose_replay_briefing
from .replay import _load_close_history
from .replay import calibrate_replay_thresholds

HistoryLoader = Callable[[str, str], list[tuple[date, float]]]

DEFAULT_HORIZON_HOLDING_DAYS = {
    "daytrade": 1,
    "swing": 5,
    "long": 20,
}

DEFAULT_HORIZON_EXIT_RULES = {
    "daytrade": {"take_profit_pct": 0.02, "stop_loss_pct": 0.015},
    "swing": {"take_profit_pct": 0.06, "stop_loss_pct": 0.04},
    "long": {"take_profit_pct": 0.08, "stop_loss_pct": 0.03},
}


def run_opportunity_validation(
    lookback_trading_days: int = 500,
    symbols: tuple[str, ...] = DEFAULT_WATCHLIST_SYMBOLS,
    period: str = "5y",
    history_loader: HistoryLoader | None = None,
    calibrate: bool = True,
    validation_training_window: int = 19,
    validation_evaluation_window: int = 5,
    transaction_cost_pct: float = 0.002,
    horizons: Sequence[str] = ("daytrade", "swing", "long"),
) -> dict[str, Any]:
    """Validate candidate ranking with a simple virtual-trading simulator."""
    loader = history_loader or _load_close_history
    symbols = symbols or DEFAULT_WATCHLIST_SYMBOLS
    horizon_names = _normalize_horizons(horizons)

    benchmark = loader("^N225", period)
    fx = loader("JPY=X", period)
    watchlist = {symbol: loader(symbol, period) for symbol in symbols}

    records = _build_records(benchmark, fx, watchlist)
    if not records:
        return _empty_validation_result(
            calibrate=calibrate,
            transaction_cost_pct=transaction_cost_pct,
            horizons=horizon_names,
            validation_training_window=validation_training_window,
            validation_evaluation_window=validation_evaluation_window,
        )

    window_records = records[-lookback_trading_days:] if lookback_trading_days > 0 else records
    price_maps = _build_price_maps(benchmark, watchlist)
    benchmark_map = dict(price_maps["^N225"])

    thresholds = calibrate_replay_thresholds(window_records) if calibrate else ReplayThresholds()

    horizon_results: dict[str, dict[str, Any]] = {}
    for horizon in horizon_names:
        horizon_results[horizon] = _validate_horizon(
            window_records,
            thresholds,
            price_maps,
            benchmark_map,
            horizon=horizon,
            transaction_cost_pct=transaction_cost_pct,
        )

    walk_forward = _walk_forward_validation(
        records,
        price_maps=price_maps,
        benchmark_map=benchmark_map,
        horizons=horizon_names,
        transaction_cost_pct=transaction_cost_pct,
        training_window=validation_training_window,
        evaluation_window=validation_evaluation_window,
        calibrate=calibrate,
    )

    return {
        "mode": "opportunity_validation",
        "sample_size": len(window_records),
        "calibration": {
            "enabled": calibrate,
            "thresholds": thresholds.__dict__,
        },
        "transaction_cost_pct": transaction_cost_pct,
        "horizons": horizon_names,
        "by_horizon": horizon_results,
        "walk_forward": walk_forward,
        "notes": [
            "Virtual trades use only historical data available at each decision point.",
            "Entry timing is applied as a gate; only buy_now signals are executed.",
        ],
    }


def _validate_horizon(
    records: list[dict[str, Any]],
    thresholds: ReplayThresholds,
    price_maps: Mapping[str, list[tuple[date, float]]],
    benchmark_map: Mapping[date, float],
    *,
    horizon: str,
    transaction_cost_pct: float,
) -> dict[str, Any]:
    holding_days = DEFAULT_HORIZON_HOLDING_DAYS[horizon]
    trades: list[dict[str, Any]] = []
    baselines: list[dict[str, Any]] = []
    skipped = 0
    open_until: date | None = None

    for record in records:
        entry_date = record["briefing_date"]
        if open_until is not None and entry_date <= open_until:
            skipped += 1
            continue

        briefing = _compose_replay_briefing(record["source"], thresholds)
        pool = evaluate_candidate_pool(briefing, horizon=horizon, limit=1)
        if not pool["candidates"]:
            skipped += 1
            continue

        candidate = pool["candidates"][0]
        if candidate["entry_timing"] != "buy_now":
            skipped += 1
            continue

        symbol = candidate["symbol"]
        series = price_maps.get(symbol)
        if not series:
            skipped += 1
            continue

        trade = _simulate_trade(
            entry_date=entry_date,
            symbol=symbol,
            series=series,
            benchmark_map=benchmark_map,
            holding_days=holding_days,
            take_profit_pct=DEFAULT_HORIZON_EXIT_RULES[horizon]["take_profit_pct"],
            stop_loss_pct=DEFAULT_HORIZON_EXIT_RULES[horizon]["stop_loss_pct"],
            transaction_cost_pct=transaction_cost_pct,
            candidate=candidate,
            horizon=horizon,
        )
        if trade is None:
            skipped += 1
            continue

        trades.append(trade)
        baselines.append(_trade_baseline(trade))
        open_until = trade["exit_date"]

    summary = _summarize_trades(trades)
    baseline_summary = _summarize_trades(baselines)

    return {
        "horizon": horizon,
        "holding_days": holding_days,
        "signal_count": len(records),
        "executed_trades": len(trades),
        "skipped_signals": skipped,
            "summary": summary,
            "baseline": {
                "symbol": "^N225",
                "summary": baseline_summary,
            },
        "trades": trades,
        "confidence_analysis": _group_analysis(trades, "confidence"),
        "risk_analysis": _group_risk_analysis(trades),
    }


def _walk_forward_validation(
    records: list[dict[str, Any]],
    *,
    price_maps: Mapping[str, list[tuple[date, float]]],
    benchmark_map: Mapping[date, float],
    horizons: Sequence[str],
    transaction_cost_pct: float,
    training_window: int,
    evaluation_window: int,
    calibrate: bool,
) -> dict[str, Any]:
    if len(records) < training_window + evaluation_window:
        return {
            "mode": "walk_forward",
            "sample_size": 0,
            "folds": [],
            "by_horizon": {
                horizon: {
                    "summary": _empty_trade_summary(),
                    "baseline": {"summary": _empty_trade_summary()},
                    "folds": [],
                }
                for horizon in horizons
            },
            "windows": {
                "training_window": training_window,
                "evaluation_window": evaluation_window,
            },
        }

    horizon_folds: dict[str, list[dict[str, Any]]] = {horizon: [] for horizon in horizons}
    horizon_trades: dict[str, list[dict[str, Any]]] = {horizon: [] for horizon in horizons}
    horizon_baselines: dict[str, list[dict[str, Any]]] = {horizon: [] for horizon in horizons}
    folds: list[dict[str, Any]] = []

    start = training_window
    while start < len(records):
        train_start = max(0, start - training_window)
        train_records = records[train_start:start]
        eval_records = records[start : min(len(records), start + evaluation_window)]
        if not train_records or not eval_records:
            break

        thresholds = calibrate_replay_thresholds(train_records) if calibrate else ReplayThresholds()
        fold_entry: dict[str, Any] = {
            "train_range": {
                "start": train_records[0]["briefing_date"].isoformat(),
                "end": train_records[-1]["briefing_date"].isoformat(),
            },
            "eval_range": {
                "start": eval_records[0]["briefing_date"].isoformat(),
                "end": eval_records[-1]["outcome_date"].isoformat(),
            },
            "horizons": {},
        }

        for horizon in horizons:
            fold_trades, fold_baseline = _simulate_fold(
                eval_records,
                thresholds=thresholds,
                price_maps=price_maps,
                benchmark_map=benchmark_map,
                horizon=horizon,
                transaction_cost_pct=transaction_cost_pct,
            )
            horizon_trades[horizon].extend(fold_trades)
            horizon_baselines[horizon].extend(fold_baseline)
            fold_summary = _summarize_trades(fold_trades)
            fold_baseline_summary = _summarize_trades(fold_baseline)
            horizon_folds[horizon].append(
                {
                    "train_range": fold_entry["train_range"],
                    "eval_range": fold_entry["eval_range"],
                    "summary": fold_summary,
                    "baseline": fold_baseline_summary,
                    "executed_trades": len(fold_trades),
                }
            )
            fold_entry["horizons"][horizon] = {
                "summary": fold_summary,
                "baseline": fold_baseline_summary,
                "executed_trades": len(fold_trades),
            }

        folds.append(fold_entry)
        start += evaluation_window

    return {
        "mode": "walk_forward",
        "sample_size": sum(len(items) for items in horizon_trades.values()),
        "folds": folds,
        "by_horizon": {
            horizon: {
                "summary": _summarize_trades(trades),
                "baseline": {"summary": _summarize_trades(horizon_baselines[horizon])},
                "folds": horizon_folds[horizon],
            }
            for horizon, trades in horizon_trades.items()
        },
        "windows": {
            "training_window": training_window,
            "evaluation_window": evaluation_window,
        },
    }


def _simulate_fold(
    records: list[dict[str, Any]],
    *,
    thresholds: ReplayThresholds,
    price_maps: Mapping[str, list[tuple[date, float]]],
    benchmark_map: Mapping[date, float],
    horizon: str,
    transaction_cost_pct: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    holding_days = DEFAULT_HORIZON_HOLDING_DAYS[horizon]
    trades: list[dict[str, Any]] = []
    baselines: list[dict[str, Any]] = []
    open_until: date | None = None

    for record in records:
        entry_date = record["briefing_date"]
        baseline = _benchmark_trade(record, benchmark_map, holding_days, transaction_cost_pct)
        if baseline is not None:
            baselines.append(baseline)

        if open_until is not None and entry_date <= open_until:
            continue

        briefing = _compose_replay_briefing(record["source"], thresholds)
        pool = evaluate_candidate_pool(briefing, horizon=horizon, limit=1)
        if not pool["candidates"]:
            continue

        candidate = pool["candidates"][0]
        if candidate["entry_timing"] != "buy_now":
            continue

        series = price_maps.get(candidate["symbol"])
        if not series:
            continue

        trade = _simulate_trade(
            entry_date=entry_date,
            symbol=candidate["symbol"],
            series=series,
            benchmark_map=benchmark_map,
            holding_days=holding_days,
            take_profit_pct=DEFAULT_HORIZON_EXIT_RULES[horizon]["take_profit_pct"],
            stop_loss_pct=DEFAULT_HORIZON_EXIT_RULES[horizon]["stop_loss_pct"],
            transaction_cost_pct=transaction_cost_pct,
            candidate=candidate,
            horizon=horizon,
        )
        if trade is None:
            continue

        trades.append(trade)
        baselines.append(_trade_baseline(trade))
        open_until = trade["exit_date"]

    return trades, baselines


def _simulate_trade(
    *,
    entry_date: date,
    symbol: str,
    series: list[tuple[date, float]],
    benchmark_map: Mapping[date, float],
    holding_days: int,
    take_profit_pct: float,
    stop_loss_pct: float,
    transaction_cost_pct: float,
    candidate: Mapping[str, Any],
    horizon: str,
) -> dict[str, Any] | None:
    index_map = {trade_date: index for index, (trade_date, _close) in enumerate(series)}
    entry_index = index_map.get(entry_date)
    if entry_index is None:
        return None

    exit_index = entry_index + holding_days
    if exit_index >= len(series):
        return None

    entry_close = series[entry_index][1]
    exit_date, exit_close = series[exit_index]
    path = series[entry_index : exit_index + 1]
    selected_exit_close = exit_close
    selected_exit_date = exit_date
    selected_index = exit_index
    for idx, (trade_date, close) in enumerate(path[1:], start=entry_index + 1):
        move_pct = (close / entry_close) - 1.0
        if move_pct >= take_profit_pct or move_pct <= -stop_loss_pct:
            selected_exit_date = trade_date
            selected_exit_close = close
            selected_index = idx
            break

    path_prices = [close for _, close in series[entry_index : selected_index + 1]]
    benchmark_entry = benchmark_map.get(entry_date)
    benchmark_exit = benchmark_map.get(selected_exit_date)
    if benchmark_entry in (None, 0) or benchmark_exit is None:
        return None

    gross_return = (selected_exit_close / entry_close) - 1.0
    benchmark_return = (benchmark_exit / benchmark_entry) - 1.0
    net_return = gross_return - transaction_cost_pct
    benchmark_net_return = benchmark_return - transaction_cost_pct

    return {
        "date": entry_date.isoformat(),
        "exit_date": selected_exit_date,
        "symbol": symbol,
        "horizon": horizon,
        "entry_price": round(entry_close, 4),
        "exit_price": round(selected_exit_close, 4),
        "gross_return_pct": round(gross_return * 100.0, 4),
        "net_return_pct": round(net_return * 100.0, 4),
        "benchmark_return_pct": round(benchmark_net_return * 100.0, 4),
        "win": net_return > 0,
        "max_drawdown_pct": round(_max_drawdown_pct(path_prices) * 100.0, 4),
        "confidence": candidate.get("confidence"),
        "score": candidate.get("score"),
        "risk_alert_count": len(candidate.get("risk_alerts", [])),
        "entry_reason": candidate.get("entry_reason"),
        "reasons": candidate.get("reasons", []),
    }


def _benchmark_trade(
    record: Mapping[str, Any],
    benchmark_map: Mapping[date, float],
    holding_days: int,
    transaction_cost_pct: float,
) -> dict[str, Any] | None:
    entry_date = record["briefing_date"]
    index_map = {trade_date: trade_date for trade_date in benchmark_map}
    if entry_date not in index_map:
        return None

    dates = sorted(benchmark_map)
    entry_index = dates.index(entry_date)
    exit_index = entry_index + holding_days
    if exit_index >= len(dates):
        return None

    exit_date = dates[exit_index]
    entry_close = benchmark_map[entry_date]
    exit_close = benchmark_map[exit_date]
    gross_return = (exit_close / entry_close) - 1.0
    net_return = gross_return - transaction_cost_pct
    return {
        "date": entry_date.isoformat(),
        "exit_date": exit_date,
        "symbol": "^N225",
        "entry_price": round(entry_close, 4),
        "exit_price": round(exit_close, 4),
        "gross_return_pct": round(gross_return * 100.0, 4),
        "net_return_pct": round(net_return * 100.0, 4),
        "win": net_return > 0,
        "max_drawdown_pct": round(_max_drawdown_pct([benchmark_map[d] for d in dates[entry_index : exit_index + 1]]) * 100.0, 4),
    }


def _trade_baseline(trade: Mapping[str, Any]) -> dict[str, Any]:
    benchmark_return = float(trade.get("benchmark_return_pct", 0.0))
    return {
        "date": trade.get("date"),
        "exit_date": trade.get("exit_date"),
        "symbol": "^N225",
        "net_return_pct": benchmark_return,
        "benchmark_return_pct": benchmark_return,
        "win": benchmark_return > 0,
        "max_drawdown_pct": float(trade.get("max_drawdown_pct", 0.0)),
    }


def _summarize_trades(trades: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    total = len(trades)
    if total == 0:
        return _empty_trade_summary()

    returns = [float(trade.get("net_return_pct", 0.0)) for trade in trades]
    benchmark_returns = [float(trade.get("benchmark_return_pct", 0.0)) for trade in trades if "benchmark_return_pct" in trade]
    wins = sum(1 for trade in trades if trade.get("win"))
    gains = sum(value for value in returns if value > 0)
    losses = sum(value for value in returns if value < 0)
    profit_factor = gains / abs(losses) if losses < 0 else (9999.0 if gains > 0 else 0.0)
    sharpe = _sharpe_ratio(returns)
    max_drawdown = _equity_curve_max_drawdown(returns)
    benchmark_average = mean(benchmark_returns) if benchmark_returns else 0.0
    beat_rate = (
        sum(1 for trade in trades if float(trade.get("net_return_pct", 0.0)) > float(trade.get("benchmark_return_pct", 0.0)))
        / total
        if benchmark_returns
        else 0.0
    )

    return {
        "total": total,
        "win_rate": wins / total,
        "average_return_pct": round(mean(returns), 4),
        "median_return_pct": round(median(returns), 4),
        "total_return_pct": round(sum(returns), 4),
        "profit_factor": round(profit_factor, 4),
        "sharpe": round(sharpe, 4),
        "max_drawdown_pct": round(max_drawdown, 4),
        "benchmark_average_return_pct": round(benchmark_average, 4),
        "outperform_rate": round(beat_rate, 4),
    }


def _group_analysis(trades: Sequence[Mapping[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    buckets: dict[str, list[Mapping[str, Any]]] = {}
    for trade in trades:
        value = trade.get(field)
        if not isinstance(value, str) or not value:
            value = "unknown"
        buckets.setdefault(value, []).append(trade)

    return {
        key: {
            "count": len(group),
            "win_rate": round(sum(1 for trade in group if trade.get("win")) / len(group), 4)
            if group
            else 0.0,
            "average_return_pct": round(mean(float(trade.get("net_return_pct", 0.0)) for trade in group), 4)
            if group
            else 0.0,
        }
        for key, group in buckets.items()
    }


def _group_risk_analysis(trades: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    buckets = {"low": [], "medium": [], "high": []}
    for trade in trades:
        count = int(trade.get("risk_alert_count", 0))
        if count <= 1:
            buckets["low"].append(trade)
        elif count == 2:
            buckets["medium"].append(trade)
        else:
            buckets["high"].append(trade)

    return {
        key: {
            "count": len(group),
            "win_rate": round(sum(1 for trade in group if trade.get("win")) / len(group), 4)
            if group
            else 0.0,
            "average_return_pct": round(mean(float(trade.get("net_return_pct", 0.0)) for trade in group), 4)
            if group
            else 0.0,
        }
        for key, group in buckets.items()
    }


def _build_price_maps(
    benchmark: list[tuple[date, float]],
    watchlist: Mapping[str, list[tuple[date, float]]],
) -> dict[str, list[tuple[date, float]]]:
    price_maps = {"^N225": sorted(benchmark, key=lambda row: row[0])}
    for symbol, series in watchlist.items():
        price_maps[symbol] = sorted(series, key=lambda row: row[0])
    return price_maps


def _max_drawdown_pct(prices: Sequence[float]) -> float:
    if not prices:
        return 0.0
    peak = prices[0]
    max_drawdown = 0.0
    for price in prices:
        if price > peak:
            peak = price
        if peak <= 0:
            continue
        drawdown = (price / peak) - 1.0
        if drawdown < max_drawdown:
            max_drawdown = drawdown
    return max_drawdown


def _equity_curve_max_drawdown(returns: Sequence[float]) -> float:
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for value in returns:
        equity *= 1.0 + (value / 100.0)
        if equity > peak:
            peak = equity
        drawdown = (equity / peak) - 1.0
        if drawdown < max_drawdown:
            max_drawdown = drawdown
    return max_drawdown * 100.0


def _sharpe_ratio(returns: Sequence[float]) -> float:
    if len(returns) < 2:
        return 0.0
    sample_stdev = pstdev(returns)
    if sample_stdev == 0:
        return 0.0
    return (mean(returns) / sample_stdev) * (len(returns) ** 0.5)


def _normalize_horizons(horizons: Sequence[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for horizon in horizons:
        text = str(horizon).strip().lower()
        if text in DEFAULT_HORIZON_HOLDING_DAYS and text not in normalized:
            normalized.append(text)
    return tuple(normalized or ("daytrade", "swing", "long"))


def _empty_trade_summary() -> dict[str, Any]:
    return {
        "total": 0,
        "win_rate": 0.0,
        "average_return_pct": 0.0,
        "median_return_pct": 0.0,
        "total_return_pct": 0.0,
        "profit_factor": 0.0,
        "sharpe": 0.0,
        "max_drawdown_pct": 0.0,
        "benchmark_average_return_pct": 0.0,
        "outperform_rate": 0.0,
    }


def _empty_validation_result(
    *,
    calibrate: bool,
    transaction_cost_pct: float,
    horizons: Sequence[str],
    validation_training_window: int,
    validation_evaluation_window: int,
) -> dict[str, Any]:
    return {
        "mode": "opportunity_validation",
        "sample_size": 0,
        "calibration": {
            "enabled": calibrate,
            "thresholds": ReplayThresholds().__dict__,
        },
        "transaction_cost_pct": transaction_cost_pct,
        "horizons": tuple(horizons),
        "by_horizon": {
            horizon: {
                "horizon": horizon,
                "holding_days": DEFAULT_HORIZON_HOLDING_DAYS[horizon],
                "signal_count": 0,
                "executed_trades": 0,
                "skipped_signals": 0,
                "summary": _empty_trade_summary(),
                "baseline": {"symbol": "^N225", "summary": _empty_trade_summary()},
                "trades": [],
                "confidence_analysis": {},
                "risk_analysis": {},
            }
            for horizon in horizons
        },
        "walk_forward": {
            "mode": "walk_forward",
            "sample_size": 0,
            "folds": [],
            "by_horizon": {
                horizon: {
                    "summary": _empty_trade_summary(),
                    "baseline": {"summary": _empty_trade_summary()},
                    "folds": [],
                }
                for horizon in horizons
            },
            "windows": {
                "training_window": validation_training_window,
                "evaluation_window": validation_evaluation_window,
            },
        },
        "notes": [
            "No historical records were available for validation."
        ],
    }
