"""Historical replay helpers for AlphaOS V4."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import date, datetime
from typing import Any

from ..agents.chairman_ai import compose_briefing
from ..briefing import derive_fx_state, derive_market_state
from ..learning.backtest import score_briefing_against_outcome, summarize_backtest
from ..watchlist import DEFAULT_WATCHLIST_SYMBOLS, derive_watch_status

HistoryLoader = Callable[[str, str], list[tuple[date, float]]]


def run_replay_simulation(
    lookback_trading_days: int = 20,
    symbols: tuple[str, ...] = DEFAULT_WATCHLIST_SYMBOLS,
    period: str = "6mo",
    history_loader: HistoryLoader | None = None,
) -> dict[str, Any]:
    """Run a replay simulation over historical daily market data."""
    loader = history_loader or _load_close_history
    symbols = symbols or DEFAULT_WATCHLIST_SYMBOLS

    benchmark = loader("^N225", period)
    fx = loader("JPY=X", period)
    watchlist = {symbol: loader(symbol, period) for symbol in symbols}

    records = _build_records(benchmark, fx, watchlist)
    results: list[dict[str, Any]] = []

    for record in records[-lookback_trading_days:]:
        briefing = compose_briefing(
            record["source"],
            learning_summary={
                "status": "insufficient",
                "sample_size": 0,
                "accuracy": None,
                "weighted_accuracy": None,
                "notes": ["Replay mode uses only historical market inputs."],
                "periods": {"all": {"total": 0}},
            },
        )
        result = score_briefing_against_outcome(briefing, record["outcome"])
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
        "results": results,
        "notes": [
            "NewsAI is intentionally neutral in replay mode because no archived news store exists yet."
        ],
    }


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
                "status": derive_watch_status(change_pct),
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
                "status": derive_watch_status(change_pct),
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
