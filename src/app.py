from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from .agents.chairman_ai import compose_briefing
from .collectors.briefing_inputs import collect_briefing_source
from .storage.briefing_history import record_briefing_snapshot
from .presenters.web import render_homepage

app = FastAPI(title="AlphaOS")


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
    source = collect_briefing_source(
        usd_jpy, market_change_pct, watchlist_symbols, watchlist_symbol
    )
    briefing = compose_briefing(source)
    try:
        record_briefing_snapshot(briefing, source)
    except Exception:
        pass
    return briefing


@app.get("/", response_class=HTMLResponse)
def get_homepage(
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
    source = collect_briefing_source(
        usd_jpy, market_change_pct, watchlist_symbols, watchlist_symbol
    )
    briefing = compose_briefing(source)
    return render_homepage(briefing)
