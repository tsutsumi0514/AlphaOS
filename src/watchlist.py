"""Watchlist data helpers for AlphaOS."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .cache import get_cached_value

DEFAULT_WATCHLIST_SYMBOLS = ("7203.T", "6758.T", "9984.T")
DEFAULT_WATCHLIST_SYMBOL = DEFAULT_WATCHLIST_SYMBOLS[0]
_WATCHLIST_CACHE_TTL_SECONDS = 300


def derive_watch_status(change_pct: float | None) -> str:
    """Map a percent move to a simple watch status label."""
    if change_pct is None:
        return "unknown"
    if change_pct >= 2.0:
        return "strong"
    if change_pct <= -2.0:
        return "weak"
    return "steady"


def fetch_watchlist_status(symbols: Sequence[str] = DEFAULT_WATCHLIST_SYMBOLS) -> list[dict[str, Any]]:
    """Fetch watchlist snapshots for one or more symbols."""
    watchlist: list[dict[str, Any]] = []

    for symbol in symbols:
        cache_key = f"watchlist.{symbol}"
        snapshot = get_cached_value(
            cache_key,
            lambda symbol=symbol: _fetch_watchlist_status_uncached(symbol),
            _WATCHLIST_CACHE_TTL_SECONDS,
        )
        if snapshot:
            watchlist.extend(snapshot)

    return watchlist


def _fetch_watchlist_status_uncached(symbol: str) -> list[dict[str, Any]]:
    try:
        import yfinance as yf
    except Exception:
        return []

    try:
        ticker = yf.Ticker(symbol)
        history: Any = ticker.history(period="5d", interval="1d")
        if history is None or history.empty:
            return []
        close = history["Close"].dropna()
        if close.empty:
            return []

        latest_close = float(close.iloc[-1])
        previous_close = float(close.iloc[-2]) if len(close) >= 2 else None
        change_pct = None
        if previous_close not in (None, 0):
            change_pct = ((latest_close - previous_close) / previous_close) * 100.0

        return [
            {
                "symbol": symbol,
                "price": latest_close,
                "change_pct": change_pct,
                "status": derive_watch_status(change_pct),
            }
        ]
    except Exception:
        return []
