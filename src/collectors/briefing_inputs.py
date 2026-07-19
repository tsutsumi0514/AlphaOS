"""Collector utilities for AlphaOS briefing inputs."""

from __future__ import annotations

from collections.abc import Sequence

from ..fx import fetch_usd_jpy_rate
from ..market import fetch_nikkei_change_pct
from ..news import fetch_latest_market_news
from ..watchlist import DEFAULT_WATCHLIST_SYMBOLS, fetch_watchlist_status


def parse_watchlist_symbols(
    watchlist_symbols: str | None, watchlist_symbol: str | None
) -> list[str]:
    if watchlist_symbols:
        symbols = [symbol.strip() for symbol in watchlist_symbols.split(",")]
        return [symbol for symbol in symbols if symbol]

    if watchlist_symbol:
        symbol = watchlist_symbol.strip()
        if symbol:
            return [symbol]

    return list(DEFAULT_WATCHLIST_SYMBOLS)


def collect_briefing_source(
    usd_jpy: float | None = None,
    market_change_pct: float | None = None,
    watchlist_symbols: str | None = None,
    watchlist_symbol: str | None = None,
    interval: str = "1d",
) -> dict[str, object] | None:
    """Collect the current briefing inputs with soft failure handling."""
    source: dict[str, object] = {}
    warnings: list[str] = []
    interval = _normalize_interval(interval)

    if usd_jpy is None:
        usd_jpy = _safe_call(fetch_usd_jpy_rate, interval, warnings=warnings, label="usd_jpy")
        if usd_jpy is None and interval != "1d":
            usd_jpy = _safe_call(fetch_usd_jpy_rate, "1d", warnings=warnings, label="usd_jpy")
    if market_change_pct is None:
        market_change_pct = _safe_call(
            fetch_nikkei_change_pct, interval, warnings=warnings, label="market_change_pct"
        )
        if market_change_pct is None and interval != "1d":
            market_change_pct = _safe_call(
                fetch_nikkei_change_pct, "1d", warnings=warnings, label="market_change_pct"
            )

    requested_watchlist_symbols = parse_watchlist_symbols(
        watchlist_symbols, watchlist_symbol
    )
    watchlist_status = _safe_call(
        fetch_watchlist_status,
        requested_watchlist_symbols,
        interval,
        warnings=warnings,
        label="watchlist_status",
    )
    if not watchlist_status and interval != "1d":
        watchlist_status = _safe_call(
            fetch_watchlist_status,
            requested_watchlist_symbols,
            "1d",
            warnings=warnings,
            label="watchlist_status",
        )
    news_item = _safe_call(fetch_latest_market_news, warnings=warnings, label="news_item")

    if usd_jpy is not None:
        source["usd_jpy"] = usd_jpy
    if market_change_pct is not None:
        source["market_change_pct"] = market_change_pct
    if watchlist_status is not None:
        source["watchlist_status"] = watchlist_status
    if news_item is not None:
        source["news_item"] = news_item

    watchlist_summary = _summarize_watchlist_status(watchlist_status)

    available_inputs = sum(
        1 for item in (usd_jpy, market_change_pct, watchlist_status, news_item) if item is not None
    )
    source["data_health"] = {
        "status": "degraded" if warnings else ("ok" if available_inputs > 0 else "empty"),
        "available_inputs": available_inputs,
        "requested_watchlist_symbols": requested_watchlist_symbols,
        "interval": interval,
        "watchlist_count": watchlist_summary["count"],
        "strong_watchlist_count": watchlist_summary["strong_count"],
        "steady_watchlist_count": watchlist_summary["steady_count"],
        "weak_watchlist_count": watchlist_summary["weak_count"],
        "top_watchlist_symbol": watchlist_summary["top_symbol"],
        "top_watchlist_change_pct": watchlist_summary["top_change_pct"],
        "news_query": _news_query(news_item),
    }
    source["watchlist_summary"] = watchlist_summary
    if warnings:
        source["data_warnings"] = warnings

    if source and interval != "1d":
        source["data_interval"] = interval

    return source or None


def _safe_call(function, *args, warnings: list[str] | None = None, label: str | None = None, **kwargs):
    attempts: list[tuple[tuple[object, ...], dict[str, object]]] = [(args, kwargs)]
    if args:
        for end in range(len(args) - 1, -1, -1):
            attempts.append((args[:end], kwargs))
    elif kwargs:
        attempts.append(((), {}))

    for attempt_args, attempt_kwargs in attempts:
        try:
            return function(*attempt_args, **attempt_kwargs)
        except TypeError:
            continue
        except Exception as exc:
            if warnings is not None and label:
                warnings.append(f"{label} unavailable: {exc}")
            return None
    return None


def _normalize_interval(interval: str | None) -> str:
    if not isinstance(interval, str):
        return "1d"
    text = interval.strip().lower()
    if text in {"1d", "1m", "2m", "5m", "15m", "30m", "60m"}:
        return text
    return "1d"


def _summarize_watchlist_status(watchlist_status: list[dict[str, object]] | None) -> dict[str, object]:
    items = watchlist_status if isinstance(watchlist_status, list) else []
    strong_count = 0
    steady_count = 0
    weak_count = 0
    top_symbol = ""
    top_change_pct = None
    top_abs_change = -1.0

    for item in items:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "").strip()
        if status == "strong":
            strong_count += 1
        elif status == "weak":
            weak_count += 1
        else:
            steady_count += 1

        change_pct = item.get("change_pct")
        if isinstance(change_pct, (int, float)):
            abs_change = abs(float(change_pct))
            if abs_change > top_abs_change:
                top_abs_change = abs_change
                top_symbol = str(item.get("symbol") or "").strip()
                top_change_pct = float(change_pct)

    return {
        "count": len(items),
        "strong_count": strong_count,
        "steady_count": steady_count,
        "weak_count": weak_count,
        "top_symbol": top_symbol,
        "top_change_pct": top_change_pct,
    }


def _news_query(news_item: object) -> str:
    if not isinstance(news_item, dict):
        return ""
    query = news_item.get("query")
    if isinstance(query, str):
        return query.strip()
    return ""
