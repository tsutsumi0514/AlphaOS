from fastapi import Body, FastAPI, Query
from fastapi.responses import HTMLResponse

from .agents.chairman_ai import compose_briefing
from .collectors.briefing_inputs import collect_briefing_source
from .learning.backtest import backtest_history, summarize_backtest
from .storage.briefing_history import record_briefing_snapshot
from .storage.briefing_history import load_briefing_history
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


@app.get("/history")
def get_history(limit: int = Query(default=20, ge=1, le=200)):
    records = load_briefing_history()
    recent_records = records[-limit:]
    return {"count": len(records), "records": recent_records}


@app.post("/backtest")
def post_backtest(payload: dict[str, object] = Body(default_factory=dict)):
    history = payload.get("history", [])
    outcomes = payload.get("outcomes", {})

    if not isinstance(history, list):
        history = []
    if not isinstance(outcomes, dict):
        outcomes = {}

    results = backtest_history(history, outcomes)
    return {"results": results, "summary": summarize_backtest(results)}
