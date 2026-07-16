import logging
from datetime import datetime, timezone

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from .agents.chairman_ai import compose_briefing
from .collectors.briefing_inputs import collect_briefing_source
from .learning.backtest import backtest_history, summarize_backtest
from .learning.feedback import build_learning_summary
from .knowledge_graph import build_knowledge_graph
from .opportunity import evaluate_candidate_pool
from .personal import personalize_candidates
from .personal import normalize_personal_profile
from .simulation.replay import run_replay_simulation
from .simulation.validation import run_opportunity_validation
from .simulation.what_if import run_what_if_simulation
from .presenters.v6 import render_knowledge_graph_page
from .presenters.v6 import render_candidates_page
from .presenters.v6 import render_replay_compare_page
from .presenters.v6 import render_validation_page
from .presenters.v6 import render_what_if_page
from .storage.briefing_history import record_briefing_snapshot
from .storage.briefing_history import load_briefing_history
from .storage.market_memory import find_similar_market_memory
from .storage.market_memory import find_latest_replay_summary
from .storage.market_memory import load_market_memory
from .storage.market_memory import record_market_memory
from .storage.market_memory import record_replay_memory
from .storage.market_memory import update_market_memory
from .storage.outcome_history import record_market_outcome
from .presenters.history import render_history_page
from .presenters.web import render_homepage
from .storage.news_history import record_news_snapshot

app = FastAPI(title="AlphaOS")
logger = logging.getLogger(__name__)


def _parse_csv_list(value: object) -> tuple[str, ...]:
    if not isinstance(value, str) or not value.strip():
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _run_validation_report(payload: dict[str, object]):
    lookback = payload.get("lookback_trading_days", 500)
    period = payload.get("period", "5y")
    symbols = payload.get("symbols")
    calibrate = payload.get("calibrate", True)
    validation_training_window = payload.get("validation_training_window", 19)
    validation_evaluation_window = payload.get("validation_evaluation_window", 5)
    transaction_cost_pct = payload.get("transaction_cost_pct", 0.002)
    horizons = payload.get("horizons", ["daytrade", "swing", "long"])
    interval = payload.get("interval", "1d")

    if not isinstance(lookback, int) or lookback < 1:
        lookback = 500

    if not isinstance(period, str) or not period.strip():
        period = "5y"

    if isinstance(symbols, list):
        requested_symbols = tuple(
            symbol.strip() for symbol in symbols if isinstance(symbol, str) and symbol.strip()
        )
        if not requested_symbols:
            requested_symbols = ()
    else:
        requested_symbols = ()

    if not isinstance(calibrate, bool):
        calibrate = True

    if not isinstance(validation_training_window, int) or validation_training_window < 1:
        validation_training_window = 19

    if not isinstance(validation_evaluation_window, int) or validation_evaluation_window < 1:
        validation_evaluation_window = 5

    if not isinstance(transaction_cost_pct, (int, float)) or transaction_cost_pct < 0:
        transaction_cost_pct = 0.002

    if not isinstance(interval, str) or not interval.strip():
        interval = "1d"

    if isinstance(horizons, list):
        requested_horizons = tuple(
            horizon.strip().lower()
            for horizon in horizons
            if isinstance(horizon, str) and horizon.strip()
        )
    else:
        requested_horizons = ("daytrade", "swing", "long")

    result = run_opportunity_validation(
        lookback_trading_days=lookback,
        symbols=requested_symbols or (),
        period=period,
        calibrate=calibrate,
        validation_training_window=validation_training_window,
        validation_evaluation_window=validation_evaluation_window,
        transaction_cost_pct=float(transaction_cost_pct),
        horizons=requested_horizons or ("daytrade", "swing", "long"),
        interval=interval,
    )
    if result["sample_size"] == 0:
        raise HTTPException(status_code=503, detail="insufficient historical data for validation")
    try:
        record_replay_memory(result)
    except Exception as exc:
        logger.warning("Failed to record validation memory: %s", exc)
    return result


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
    interval: str = Query(default="1d", description="Data interval such as 1d or 1m"),
):
    source = collect_briefing_source(
        usd_jpy, market_change_pct, watchlist_symbols, watchlist_symbol, interval=interval
    )
    briefing = compose_briefing(source)
    try:
        record_briefing_snapshot(briefing, source)
    except Exception as exc:
        logger.warning("Failed to record briefing snapshot: %s", exc)
    try:
        record_market_memory(briefing, source)
    except Exception as exc:
        logger.warning("Failed to record market memory snapshot: %s", exc)
    try:
        record_news_snapshot(briefing.get("news_item"), recorded_at=datetime.now(timezone.utc))
    except Exception as exc:
        logger.warning("Failed to record news snapshot: %s", exc)
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
    interval: str = Query(default="1d", description="Data interval such as 1d or 1m"),
):
    source = collect_briefing_source(
        usd_jpy, market_change_pct, watchlist_symbols, watchlist_symbol, interval=interval
    )
    briefing = compose_briefing(source)
    try:
        record_news_snapshot(briefing.get("news_item"), recorded_at=datetime.now(timezone.utc))
    except Exception as exc:
        logger.warning("Failed to record news snapshot: %s", exc)
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
    try:
        update_market_memory(briefing_id.strip(), outcome_payload)
    except Exception as exc:
        logger.warning("Failed to update market memory: %s", exc)
    return {
        "status": "recorded",
        "briefing_id": briefing_id.strip(),
        "record": record,
        "learning_summary": build_learning_summary(),
    }


@app.get("/learning")
def get_learning():
    return build_learning_summary()


@app.get("/memory")
def get_memory(limit: int = Query(default=20, ge=1, le=200)):
    records = load_market_memory()
    recent_records = records[-limit:]
    return {"count": len(records), "records": recent_records}


@app.get("/memory/search")
def get_memory_search(
    limit: int = Query(default=5, ge=1, le=20),
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
    interval: str = Query(default="1d", description="Data interval such as 1d or 1m"),
):
    source = collect_briefing_source(
        usd_jpy, market_change_pct, watchlist_symbols, watchlist_symbol, interval=interval
    )
    briefing = compose_briefing(source)
    matches = find_similar_market_memory(briefing, limit=limit)
    return {
        "count": len(matches),
        "query": {
            "briefing_id": briefing.get("briefing_id"),
            "market_state": briefing.get("market_state"),
            "fx_state": briefing.get("fx_state"),
            "confidence": briefing.get("confidence"),
            "risk_alerts": briefing.get("risk_alerts", []),
            "reasons": briefing.get("reasons", []),
            "evidence": briefing.get("evidence", []),
        },
        "matches": matches,
    }


@app.get("/candidates")
def get_candidates(
    horizon: str = Query(default="swing", description="Candidate horizon"),
    limit: int = Query(default=5, ge=1, le=20),
    holdings: str | None = Query(default=None, description="Comma-separated current holdings"),
    investment_period: str | None = Query(default=None, description="Investment period"),
    risk_tolerance: str | None = Query(default=None, description="Risk tolerance"),
    style: str | None = Query(default=None, description="Investment style"),
    interested_markets: str | None = Query(default=None, description="Comma-separated interested markets"),
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
    interval: str = Query(default="1d", description="Data interval such as 1d or 1m"),
):
    source = collect_briefing_source(
        usd_jpy, market_change_pct, watchlist_symbols, watchlist_symbol, interval=interval
    )
    briefing = compose_briefing(source)
    candidate_pool = evaluate_candidate_pool(briefing, horizon=horizon, limit=limit)
    candidates = candidate_pool["candidates"]
    profile = normalize_personal_profile(
        {
            "holdings": [item.strip() for item in holdings.split(",") if item.strip()]
            if isinstance(holdings, str) and holdings.strip()
            else [],
            "investment_period": investment_period,
            "risk_tolerance": risk_tolerance,
            "style": style,
            "interested_markets": [
                item.strip() for item in interested_markets.split(",") if item.strip()
            ]
            if isinstance(interested_markets, str) and interested_markets.strip()
            else [],
        }
    )
    personalized = personalize_candidates(candidates, profile)
    return {
        "count": len(personalized["candidates"]),
        "rejected_count": len(candidate_pool["excluded"]),
        "opportunity_summary": candidate_pool["summary"],
        "horizon": "daytrade" if horizon.strip().lower() == "daytrade" else "swing",
        "personal_profile": personalized["profile"],
        "personal_notes": personalized["notes"],
        "candidates": personalized["candidates"],
        "excluded_candidates": candidate_pool["excluded"],
        "top_candidate": personalized["candidates"][0] if personalized["candidates"] else None,
        "briefing_id": briefing.get("briefing_id"),
    }


@app.get("/candidates/view", response_class=HTMLResponse)
def get_candidates_view(
    horizon: str = Query(default="swing", description="Candidate horizon"),
    limit: int = Query(default=5, ge=1, le=20),
    holdings: str | None = Query(default=None, description="Comma-separated current holdings"),
    investment_period: str | None = Query(default=None, description="Investment period"),
    risk_tolerance: str | None = Query(default=None, description="Risk tolerance"),
    style: str | None = Query(default=None, description="Investment style"),
    interested_markets: str | None = Query(default=None, description="Comma-separated interested markets"),
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
    interval: str = Query(default="1d", description="Data interval such as 1d or 1m"),
):
    source = collect_briefing_source(
        usd_jpy, market_change_pct, watchlist_symbols, watchlist_symbol, interval=interval
    )
    briefing = compose_briefing(source)
    candidate_pool = evaluate_candidate_pool(briefing, horizon=horizon, limit=limit)
    candidates = candidate_pool["candidates"]
    profile = normalize_personal_profile(
        {
            "holdings": [item.strip() for item in holdings.split(",") if item.strip()]
            if isinstance(holdings, str) and holdings.strip()
            else [],
            "investment_period": investment_period,
            "risk_tolerance": risk_tolerance,
            "style": style,
            "interested_markets": [
                item.strip() for item in interested_markets.split(",") if item.strip()
            ]
            if isinstance(interested_markets, str) and interested_markets.strip()
            else [],
        }
    )
    personalized = personalize_candidates(candidates, profile)
    report = {
        "count": len(personalized["candidates"]),
        "rejected_count": len(candidate_pool["excluded"]),
        "opportunity_summary": candidate_pool["summary"],
        "horizon": "daytrade" if horizon.strip().lower() == "daytrade" else "swing",
        "personal_profile": personalized["profile"],
        "personal_notes": personalized["notes"],
        "candidates": personalized["candidates"],
        "excluded_candidates": candidate_pool["excluded"],
        "top_candidate": personalized["candidates"][0] if personalized["candidates"] else None,
        "briefing_id": briefing.get("briefing_id"),
    }
    return render_candidates_page(report)


@app.post("/what-if")
def post_what_if(payload: dict[str, object] = Body(default_factory=dict)):
    scenarios = payload.get("scenarios", [])
    if not isinstance(scenarios, list):
        scenarios = []
    source = collect_briefing_source(None, None, None, None)
    briefing = compose_briefing(source)
    report = run_what_if_simulation(briefing, scenarios)
    return report


@app.get("/what-if", response_class=HTMLResponse)
def get_what_if(
    scenarios: str | None = Query(default=None, description="Comma-separated scenarios"),
    interval: str = Query(default="1d", description="Data interval such as 1d or 1m"),
):
    source = collect_briefing_source(None, None, None, None, interval=interval)
    briefing = compose_briefing(source)
    scenario_list = [item.strip() for item in scenarios.split(",") if item.strip()] if isinstance(scenarios, str) and scenarios.strip() else []
    report = run_what_if_simulation(briefing, scenario_list)
    return render_what_if_page(report)


@app.get("/knowledge-graph")
def get_knowledge_graph(
    scenarios: str | None = Query(default=None, description="Comma-separated scenarios"),
    interval: str = Query(default="1d", description="Data interval such as 1d or 1m"),
):
    source = collect_briefing_source(None, None, None, None, interval=interval)
    briefing = compose_briefing(source)
    scenario_list = [item.strip() for item in scenarios.split(",") if item.strip()] if isinstance(scenarios, str) and scenarios.strip() else []
    graph = build_knowledge_graph(briefing, scenarios=scenario_list)
    return graph


@app.get("/knowledge-graph/view", response_class=HTMLResponse)
def get_knowledge_graph_view(
    scenarios: str | None = Query(default=None, description="Comma-separated scenarios"),
    interval: str = Query(default="1d", description="Data interval such as 1d or 1m"),
):
    source = collect_briefing_source(None, None, None, None, interval=interval)
    briefing = compose_briefing(source)
    scenario_list = [item.strip() for item in scenarios.split(",") if item.strip()] if isinstance(scenarios, str) and scenarios.strip() else []
    graph = build_knowledge_graph(briefing, scenarios=scenario_list)
    return render_knowledge_graph_page(graph)


@app.get("/replay/compare", response_class=HTMLResponse)
def get_replay_compare(
    limit: int = Query(default=5, ge=1, le=10),
    interval: str = Query(default="1d", description="Data interval such as 1d or 1m"),
):
    source = collect_briefing_source(None, None, None, None, interval=interval)
    briefing = compose_briefing(source)
    similar_cases = find_similar_market_memory(briefing, limit=limit)
    latest_replay = find_latest_replay_summary()
    compare = {
        "current": {
            "market_state": briefing.get("market_state"),
            "fx_state": briefing.get("fx_state"),
            "confidence": briefing.get("confidence"),
            "risk_alerts": briefing.get("risk_alerts", []),
        },
        "latest_replay": latest_replay.get("replay_summary") if isinstance(latest_replay, dict) else {},
        "similar_cases": similar_cases,
    }
    return render_replay_compare_page(compare)


@app.post("/simulate")
def post_simulate(payload: dict[str, object] = Body(default_factory=dict)):
    lookback = payload.get("lookback_trading_days", 500)
    period = payload.get("period", "5y")
    symbols = payload.get("symbols")
    calibrate = payload.get("calibrate", True)
    validation_training_window = payload.get("validation_training_window", 19)
    validation_evaluation_window = payload.get("validation_evaluation_window", 5)
    interval = payload.get("interval", "1d")

    if not isinstance(lookback, int) or lookback < 1:
        lookback = 500

    if not isinstance(period, str) or not period.strip():
        period = "5y"

    if isinstance(symbols, list):
        requested_symbols = tuple(
            symbol.strip() for symbol in symbols if isinstance(symbol, str) and symbol.strip()
        )
        if not requested_symbols:
            requested_symbols = ()
    else:
        requested_symbols = ()

    if not isinstance(calibrate, bool):
        calibrate = True

    if not isinstance(validation_training_window, int) or validation_training_window < 1:
        validation_training_window = 19

    if not isinstance(validation_evaluation_window, int) or validation_evaluation_window < 1:
        validation_evaluation_window = 5

    if not isinstance(interval, str) or not interval.strip():
        interval = "1d"

    result = run_replay_simulation(
        lookback_trading_days=lookback,
        symbols=requested_symbols or (),
        period=period,
        calibrate=calibrate,
        validation_training_window=validation_training_window,
        validation_evaluation_window=validation_evaluation_window,
        interval=interval,
    )
    if result["sample_size"] == 0:
        raise HTTPException(status_code=503, detail="insufficient historical data for replay")
    try:
        record_replay_memory(result)
    except Exception as exc:
        logger.warning("Failed to record replay memory: %s", exc)
    return result


@app.post("/validate")
def post_validate(payload: dict[str, object] = Body(default_factory=dict)):
    return _run_validation_report(payload)


@app.get("/validate/view", response_class=HTMLResponse)
def get_validate_view(
    lookback_trading_days: int = Query(default=500, ge=1, le=5000),
    period: str = Query(default="5y"),
    symbols: str | None = Query(default=None, description="Comma-separated symbols"),
    calibrate: bool = Query(default=True),
    validation_training_window: int = Query(default=19, ge=1, le=250),
    validation_evaluation_window: int = Query(default=5, ge=1, le=60),
    transaction_cost_pct: float = Query(default=0.002, ge=0.0, le=0.1),
    horizons: str | None = Query(default=None, description="Comma-separated horizons"),
    interval: str = Query(default="1d", description="Data interval such as 1d or 1m"),
):
    payload: dict[str, object] = {
        "lookback_trading_days": lookback_trading_days,
        "period": period,
        "symbols": list(_parse_csv_list(symbols)),
        "calibrate": calibrate,
        "validation_training_window": validation_training_window,
        "validation_evaluation_window": validation_evaluation_window,
        "transaction_cost_pct": transaction_cost_pct,
        "interval": interval,
        "horizons": list(_parse_csv_list(horizons)) if isinstance(horizons, str) and horizons.strip() else ["daytrade", "swing", "long"],
    }
    report = _run_validation_report(payload)
    return render_validation_page(report)
