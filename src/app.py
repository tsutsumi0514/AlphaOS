import logging

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from .agents.chairman_ai import compose_briefing
from .collectors.briefing_inputs import collect_briefing_source
from .learning.backtest import backtest_history, summarize_backtest
from .learning.feedback import build_learning_summary
from .storage.briefing_history import record_briefing_snapshot
from .storage.briefing_history import load_briefing_history
from .storage.outcome_history import record_market_outcome
from .presenters.history import render_history_page
from .presenters.web import render_homepage

app = FastAPI(title="AlphaOS")
logger = logging.getLogger(__name__)


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
    except Exception as exc:
        logger.warning("Failed to record briefing snapshot: %s", exc)
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


@app.get("/history/view", response_class=HTMLResponse)
def get_history_view(limit: int = Query(default=10, ge=1, le=200)):
    records = load_briefing_history()
    recent_records = records[-limit:]
    learning_summary = build_learning_summary()
    return render_history_page(recent_records, learning_summary)


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


@app.post("/outcome")
def post_outcome(payload: dict[str, object] = Body(default_factory=dict)):
    briefing_id = payload.get("briefing_id")
    if not isinstance(briefing_id, str) or not briefing_id.strip():
        raise HTTPException(status_code=400, detail="briefing_id is required")

    outcome = payload.get("outcome")
    if isinstance(outcome, dict):
        outcome_payload = outcome
    else:
        outcome_payload = {
            key: value for key, value in payload.items() if key != "briefing_id"
        }

    try:
        record = record_market_outcome(briefing_id.strip(), outcome_payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="failed to record outcome") from exc
    return {
        "status": "recorded",
        "briefing_id": briefing_id.strip(),
        "record": record,
        "learning_summary": build_learning_summary(),
    }


@app.get("/learning")
def get_learning():
    return build_learning_summary()
