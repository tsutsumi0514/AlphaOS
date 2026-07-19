"""Watchlist data helpers for AlphaOS."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .cache import get_cached_value

DEFAULT_WATCHLIST_SYMBOLS = ("7203.T", "6758.T", "9984.T")
DEFAULT_WATCHLIST_SYMBOL = DEFAULT_WATCHLIST_SYMBOLS[0]
_WATCHLIST_CACHE_TTL_SECONDS = 300
_VALID_INTERVALS = {"1d", "1m", "2m", "5m", "15m", "30m", "60m"}


def derive_watch_status(change_pct: float | None) -> str:
    """Map a percent move to a simple watch status label."""
    if change_pct is None:
        return "unknown"
    if change_pct >= 2.0:
        return "strong"
    if change_pct <= -2.0:
        return "weak"
    return "steady"


def fetch_watchlist_status(
    symbols: Sequence[str] = DEFAULT_WATCHLIST_SYMBOLS,
    interval: str = "1d",
) -> list[dict[str, Any]]:
    """Fetch watchlist snapshots for one or more symbols."""
    interval = _normalize_interval(interval)
    watchlist: list[dict[str, Any]] = []

    for symbol in symbols:
        snapshot = None
        for candidate_interval in _interval_candidates(interval):
            cache_key = f"watchlist.{candidate_interval}.{symbol}"
            snapshot = get_cached_value(
                cache_key,
                lambda symbol=symbol, interval=candidate_interval: _fetch_watchlist_status_uncached(
                    symbol, interval
                ),
                _WATCHLIST_CACHE_TTL_SECONDS,
            )
            if snapshot:
                if candidate_interval != interval:
                    adjusted_snapshot: list[dict[str, Any]] = []
                    for item in snapshot:
                        if isinstance(item, dict):
                            copied_item = dict(item)
                            copied_item["interval_used"] = candidate_interval
                            adjusted_snapshot.append(copied_item)
                        else:
                            adjusted_snapshot.append(item)
                    watchlist.extend(adjusted_snapshot)
                else:
                    watchlist.extend(snapshot)
                break

    return watchlist


def _fetch_watchlist_status_uncached(symbol: str, interval: str) -> list[dict[str, Any]]:
    try:
        import yfinance as yf
    except Exception:
        return []

    try:
        ticker = yf.Ticker(symbol)
        history: Any = ticker.history(period="5d", interval=interval)
        if history is None or history.empty:
            return []
        close = history["Close"].dropna()
        if close.empty:
            return []
        volume_series = history["Volume"].dropna() if "Volume" in history else None

        latest_close = float(close.iloc[-1])
        previous_close = float(close.iloc[-2]) if len(close) >= 2 else None
        change_pct = None
        if previous_close not in (None, 0):
            change_pct = ((latest_close - previous_close) / previous_close) * 100.0

        latest_volume = None
        avg_volume = None
        if volume_series is not None and not volume_series.empty:
            latest_volume = float(volume_series.iloc[-1])
            window = volume_series.iloc[-min(len(volume_series), 5):]
            if not window.empty:
                avg_volume = float(window.mean())

        return [
            {
                "symbol": symbol,
                "price": latest_close,
                "change_pct": change_pct,
                "volume": latest_volume,
                "avg_volume": avg_volume,
                "status": derive_watch_status(change_pct),
            }
        ]
    except Exception:
        return []


def _normalize_interval(interval: str | None) -> str:
    if not isinstance(interval, str):
        return "1d"
    text = interval.strip().lower()
    return text if text in _VALID_INTERVALS else "1d"


def _interval_candidates(interval: str) -> tuple[str, ...]:
    if interval == "1d":
        return ("1d",)
    return (interval, "1d")
