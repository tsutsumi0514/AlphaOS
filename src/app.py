from fastapi import FastAPI, Query

from .briefing import build_briefing
from .fx import fetch_usd_jpy_rate
from .market import fetch_nikkei_change_pct

app = FastAPI(title="AlphaOS")


@app.get("/briefing")
def get_briefing(
    usd_jpy: float | None = Query(default=None, description="USD/JPY rate"),
    market_change_pct: float | None = Query(
        default=None, description="Nikkei 225 day-over-day percent change"
    ),
):
    if usd_jpy is None:
        usd_jpy = fetch_usd_jpy_rate()
    if market_change_pct is None:
        market_change_pct = fetch_nikkei_change_pct()

    source: dict[str, float] = {}
    if usd_jpy is not None:
        source["usd_jpy"] = usd_jpy
    if market_change_pct is not None:
        source["market_change_pct"] = market_change_pct

    source = source or None
    return build_briefing(source)
