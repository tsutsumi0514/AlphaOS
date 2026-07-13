"""Market data helpers for AlphaOS."""

from __future__ import annotations

from typing import Any


def fetch_nikkei_change_pct() -> float | None:
    """Fetch the latest Nikkei 225 day-over-day percent change.

    Returns None when the change cannot be obtained.
    """
    try:
        import yfinance as yf
    except Exception:
        return None

    try:
        ticker = yf.Ticker("^N225")
        history: Any = ticker.history(period="5d", interval="1d")
        if history is None or history.empty:
            return None
        close = history["Close"].dropna()
        if len(close) < 2:
            return None
        previous_close = float(close.iloc[-2])
        latest_close = float(close.iloc[-1])
        if previous_close == 0:
            return None
        return ((latest_close - previous_close) / previous_close) * 100.0
    except Exception:
        return None
