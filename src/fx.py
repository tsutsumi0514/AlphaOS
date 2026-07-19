"""Foreign exchange data helpers for AlphaOS."""

from __future__ import annotations

from typing import Any

from .cache import get_cached_value


_USD_JPY_CACHE_KEY = "fx.usd_jpy"
_USD_JPY_CACHE_TTL_SECONDS = 300
_VALID_INTERVALS = {"1d", "1m", "2m", "5m", "15m", "30m", "60m"}


def fetch_usd_jpy_rate(interval: str = "1d") -> float | None:
    """Fetch the latest USD/JPY rate from Yahoo Finance via yfinance.

    Returns None when the rate cannot be obtained.
    """
    interval = _normalize_interval(interval)
    for candidate_interval in _interval_candidates(interval):
        value = get_cached_value(
            f"{_USD_JPY_CACHE_KEY}.{candidate_interval}",
            lambda candidate_interval=candidate_interval: _fetch_usd_jpy_rate_uncached(
                candidate_interval
            ),
            _USD_JPY_CACHE_TTL_SECONDS,
        )
        if value is not None:
            return value
    return None


def _fetch_usd_jpy_rate_uncached(interval: str) -> float | None:
    try:
        import yfinance as yf
    except Exception:
        return None

    try:
        ticker = yf.Ticker("JPY=X")
        history: Any = ticker.history(period="5d", interval=interval)
        if history is None or history.empty:
            return None
        close = history["Close"].dropna()
        if close.empty:
            return None
        return float(close.iloc[-1])
    except Exception:
        return None


def _normalize_interval(interval: str | None) -> str:
    if not isinstance(interval, str):
        return "1d"
    text = interval.strip().lower()
    return text if text in _VALID_INTERVALS else "1d"


def _interval_candidates(interval: str) -> tuple[str, ...]:
    if interval == "1d":
        return ("1d",)
    return (interval, "1d")
