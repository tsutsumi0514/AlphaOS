"""Foreign exchange data helpers for AlphaOS."""

from __future__ import annotations

from typing import Any


def fetch_usd_jpy_rate() -> float | None:
    """Fetch the latest USD/JPY rate from Yahoo Finance via yfinance.

    Returns None when the rate cannot be obtained.
    """
    try:
        import yfinance as yf
    except Exception:
        return None

    try:
        ticker = yf.Ticker("JPY=X")
        history: Any = ticker.history(period="5d", interval="1d")
        if history is None or history.empty:
            return None
        close = history["Close"].dropna()
        if close.empty:
            return None
        return float(close.iloc[-1])
    except Exception:
        return None
