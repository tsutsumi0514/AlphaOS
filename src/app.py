from fastapi import FastAPI, Query

from .briefing import build_briefing
from .fx import fetch_usd_jpy_rate
from .news import fetch_latest_market_news
from .market import fetch_nikkei_change_pct
from .watchlist import DEFAULT_WATCHLIST_SYMBOLS, fetch_watchlist_status

app = FastAPI(title="AlphaOS")


def _parse_watchlist_symbols(
    watchlist_symbols: str | None, watchlist_symbol: str | None
) -> list[str]:
    if watchlist_symbols:
        symbols = [symbol.strip() for symbol in watchlist_symbols.split(",")]
        return [symbol for symbol in symbols if symbol]

    if watchlist_symbol:
        return [watchlist_symbol.strip()]

    return list(DEFAULT_WATCHLIST_SYMBOLS)


@app.get("/briefing")
def get_briefing(
    usd_jpy: float | None = Query(default=None, description="USD/JPY rate"),
    market_change_pct: float | None = Query(
        default=None, description="Nikkei 225 day-over-day percent change"
    ),
    watchlist_symbols: str | None = Query(
        default=None, description="Comma-separated watchlist symbols"
    ),
    watchlist_symbol: str | None = Query(
        default=None, description="Single watchlist symbol override"
    ),
):
    if usd_jpy is None:
        usd_jpy = fetch_usd_jpy_rate()
    if market_change_pct is None:
        market_change_pct = fetch_nikkei_change_pct()
    requested_watchlist_symbols = _parse_watchlist_symbols(
        watchlist_symbols, watchlist_symbol
    )
    watchlist_status = fetch_watchlist_status(requested_watchlist_symbols)
    news_item = fetch_latest_market_news()

    source: dict[str, object] = {}
    if usd_jpy is not None:
        source["usd_jpy"] = usd_jpy
    if market_change_pct is not None:
        source["market_change_pct"] = market_change_pct
    if watchlist_status:
        source["watchlist_status"] = watchlist_status
    if news_item is not None:
        source["news_item"] = news_item

    source = source or None
    return build_briefing(source)
