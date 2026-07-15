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
    interval = _normalize_interval(interval)

    if usd_jpy is None:
        usd_jpy = _safe_call(fetch_usd_jpy_rate, interval)
    if market_change_pct is None:
        market_change_pct = _safe_call(fetch_nikkei_change_pct, interval)

    requested_watchlist_symbols = parse_watchlist_symbols(
        watchlist_symbols, watchlist_symbol
    )
    watchlist_status = _safe_call(fetch_watchlist_status, requested_watchlist_symbols, interval)
    news_item = _safe_call(fetch_latest_market_news)

    if usd_jpy is not None:
        source["usd_jpy"] = usd_jpy
    if market_change_pct is not None:
        source["market_change_pct"] = market_change_pct
    if watchlist_status is not None:
        source["watchlist_status"] = watchlist_status
    if news_item is not None:
        source["news_item"] = news_item

    if source and interval != "1d":
        source["data_interval"] = interval

    return source or None


def _safe_call(function, *args, **kwargs):
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
        except Exception:
            return None
    return None


def _normalize_interval(interval: str | None) -> str:
    if not isinstance(interval, str):
        return "1d"
    text = interval.strip().lower()
    if text in {"1d", "1m", "2m", "5m", "15m", "30m", "60m"}:
        return text
    return "1d"
