from fastapi import FastAPI, Query

from .briefing import build_briefing
from .fx import fetch_usd_jpy_rate
from .market import fetch_nikkei_change_pct
from .watchlist import DEFAULT_WATCHLIST_SYMBOL, fetch_watchlist_status

app = FastAPI(title="AlphaOS")


@app.get("/briefing")
def get_briefing(
    usd_jpy: float | None = Query(default=None, description="USD/JPY rate"),
    market_change_pct: float | None = Query(
        default=None, description="Nikkei 225 day-over-day percent change"
    ),
    watchlist_symbol: str = Query(
        default=DEFAULT_WATCHLIST_SYMBOL, description="Single watchlist symbol"
    ),
):
    if usd_jpy is None:
        usd_jpy = fetch_usd_jpy_rate()
    if market_change_pct is None:
        market_change_pct = fetch_nikkei_change_pct()
    watchlist_status = fetch_watchlist_status(watchlist_symbol)

    source: dict[str, float | list[dict[str, object]]] = {}
    if usd_jpy is not None:
        source["usd_jpy"] = usd_jpy
    if market_change_pct is not None:
        source["market_change_pct"] = market_change_pct
    if watchlist_status:
        source["watchlist_status"] = watchlist_status

    source = source or None
    return build_briefing(source)
