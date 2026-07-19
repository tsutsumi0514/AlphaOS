import asyncio
import logging
import os
from contextlib import asynccontextmanager
from contextlib import suppress
from datetime import datetime, timezone
from collections.abc import Mapping

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, Response

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
from .services.live_refresh import DEFAULT_BRIEFING_INTERVAL
from .services.live_refresh import attach_live_refresh_metadata
from .services.live_refresh import build_live_snapshot
from .services.live_refresh import live_refresh_enabled
from .services.live_refresh import live_refresh_interval_seconds
from .services.live_refresh import run_live_refresh_loop
from .storage.news_history import record_news_snapshot

logger = logging.getLogger(__name__)
PUBLIC_MODE_ENV = "ALPHAOS_PUBLIC_MODE"
_FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="8" fill="#20262e"/>
  <path d="M8 22L12.5 10H15.8L20 22H17.4L16.4 19.1H11.8L10.8 22H8ZM12.5 17.3H15.6L14.1 12.8L12.5 17.3Z" fill="#f5f3ef"/>
  <circle cx="23.5" cy="21.5" r="2.4" fill="#d4a94d"/>
</svg>"""


def _parse_csv_list(value: object) -> tuple[str, ...]:
    if not isinstance(value, str) or not value.strip():
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _public_mode_enabled() -> bool:
    return _text(os.environ.get(PUBLIC_MODE_ENV)).lower() in {"1", "true", "yes", "on"}


def _require_internal_surface() -> None:
    if _public_mode_enabled():
        raise HTTPException(status_code=404, detail="not found")


def _text(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _custom_briefing_inputs_provided(
    usd_jpy: float | None,
    market_change_pct: float | None,
    watchlist_symbols: str | None,
    watchlist_symbol: str | None,
) -> bool:
    return any(
        item is not None
        for item in (usd_jpy, market_change_pct, watchlist_symbols, watchlist_symbol)
    )


def _load_live_snapshot() -> dict[str, object] | None:
    snapshot = getattr(app.state, "live_market_snapshot", None)
    if not isinstance(snapshot, Mapping):
        return None
    return dict(snapshot)


def _store_live_briefing(snapshot: dict[str, object]) -> None:
    app.state.live_market_snapshot = snapshot
    app.state.live_market_updated_at = snapshot.get("refreshed_at")
    app.state.live_market_refresh_status = snapshot.get("refresh_status", {})


def _normalize_refresh_interval_seconds(value: object | None) -> int | None:
    if value is None:
        return None
    try:
        interval = int(value)
    except Exception:
        return None
    if interval < 1:
        return None
    return interval


def _live_refresh_interval_seconds() -> int:
    current = getattr(app.state, "live_market_refresh_interval_seconds", None)
    interval = _normalize_refresh_interval_seconds(current)
    if interval is not None:
        return interval
    interval = live_refresh_interval_seconds()
    app.state.live_market_refresh_interval_seconds = interval
    return interval


def _set_live_refresh_interval_seconds(value: object | None) -> int | None:
    interval = _normalize_refresh_interval_seconds(value)
    if interval is None:
        return None
    app.state.live_market_refresh_interval_seconds = interval
    refresh_status = getattr(app.state, "live_market_refresh_status", {})
    if isinstance(refresh_status, Mapping):
        updated_status = dict(refresh_status)
        updated_status["interval_seconds"] = interval
        app.state.live_market_refresh_status = updated_status
    return interval


def _refresh_live_snapshot(interval: str = DEFAULT_BRIEFING_INTERVAL) -> dict[str, object]:
    snapshot = build_live_snapshot(
        interval,
        refresh_interval_seconds=_live_refresh_interval_seconds(),
    )
    _store_live_briefing(snapshot)
    return snapshot


def _build_briefing(
    usd_jpy: float | None,
    market_change_pct: float | None,
    watchlist_symbols: str | None,
    watchlist_symbol: str | None,
    interval: str,
) -> tuple[dict[str, object], dict[str, object]]:
    if not _custom_briefing_inputs_provided(
        usd_jpy, market_change_pct, watchlist_symbols, watchlist_symbol
    ) and interval == DEFAULT_BRIEFING_INTERVAL:
        cached_snapshot = _load_live_snapshot()
        if cached_snapshot is not None:
            briefing = cached_snapshot.get("briefing")
            source = cached_snapshot.get("source")
            if isinstance(briefing, Mapping):
                return dict(briefing), dict(source) if isinstance(source, Mapping) else {}

    source = collect_briefing_source(
        usd_jpy, market_change_pct, watchlist_symbols, watchlist_symbol, interval=interval
    ) or {}
    briefing = compose_briefing(source)
    if isinstance(briefing, Mapping):
        briefing = dict(briefing)
    else:
        briefing = {"briefing": briefing}

    attach_live_refresh_metadata(
        briefing,
        source,
        briefing_interval=interval,
        refresh_interval_seconds=_live_refresh_interval_seconds(),
        refreshed_at=datetime.now(timezone.utc).isoformat(),
    )

    if (
        not _custom_briefing_inputs_provided(
            usd_jpy, market_change_pct, watchlist_symbols, watchlist_symbol
        )
        and interval == DEFAULT_BRIEFING_INTERVAL
    ):
        _store_live_briefing(
        {
            "briefing": briefing,
            "source": source,
            "refreshed_at": briefing.get("market_refresh", {}).get("refreshed_at"),
            "refresh_status": briefing.get("market_refresh", {}),
        }
        )

    return briefing, source


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


async def _startup_live_refresh() -> None:
    app.state.live_market_snapshot = None
    app.state.live_market_updated_at = None
    app.state.live_market_refresh_status = {"enabled": live_refresh_enabled(), "status": "idle"}
    app.state.live_market_refresh_interval_seconds = live_refresh_interval_seconds()

    if not live_refresh_enabled():
        return

    try:
        snapshot = await asyncio.to_thread(
            build_live_snapshot,
            DEFAULT_BRIEFING_INTERVAL,
            refresh_interval_seconds=_live_refresh_interval_seconds(),
        )
        _store_live_briefing(snapshot)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Failed to build initial live market snapshot: %s", exc)

    app.state.live_market_refresh_stop = asyncio.Event()
    app.state.live_market_refresh_task = asyncio.create_task(
        run_live_refresh_loop(
            _store_live_briefing,
            interval_seconds_provider=_live_refresh_interval_seconds,
            briefing_interval=DEFAULT_BRIEFING_INTERVAL,
            stop_event=app.state.live_market_refresh_stop,
        )
    )


async def _shutdown_live_refresh() -> None:
    stop_event = getattr(app.state, "live_market_refresh_stop", None)
    if isinstance(stop_event, asyncio.Event):
        stop_event.set()

    task = getattr(app.state, "live_market_refresh_task", None)
    if task is not None:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


@asynccontextmanager
async def lifespan(application: FastAPI):
    await _startup_live_refresh()
    try:
        yield
    finally:
        await _shutdown_live_refresh()


app = FastAPI(title="AlphaOS", lifespan=lifespan)


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
    refresh_interval_seconds: int | None = Query(
        default=None, ge=1, le=86400, description="Auto refresh interval in seconds"
    ),
):
    if refresh_interval_seconds is not None:
        _set_live_refresh_interval_seconds(refresh_interval_seconds)

    if (
        refresh_interval_seconds is not None
        and not _custom_briefing_inputs_provided(
            usd_jpy, market_change_pct, watchlist_symbols, watchlist_symbol
        )
        and interval == DEFAULT_BRIEFING_INTERVAL
    ):
        snapshot = _refresh_live_snapshot(interval)
        briefing = snapshot["briefing"]
        source = snapshot["source"]
    else:
        briefing, source = _build_briefing(
            usd_jpy, market_change_pct, watchlist_symbols, watchlist_symbol, interval
        )
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
    refresh_interval_seconds: int | None = Query(
        default=None, ge=1, le=86400, description="Auto refresh interval in seconds"
    ),
):
    if refresh_interval_seconds is not None:
        _set_live_refresh_interval_seconds(refresh_interval_seconds)

    if (
        refresh_interval_seconds is not None
        and not _custom_briefing_inputs_provided(
            usd_jpy, market_change_pct, watchlist_symbols, watchlist_symbol
        )
        and interval == DEFAULT_BRIEFING_INTERVAL
    ):
        snapshot = _refresh_live_snapshot(interval)
        briefing = snapshot["briefing"]
    else:
        briefing, _source = _build_briefing(
            usd_jpy, market_change_pct, watchlist_symbols, watchlist_symbol, interval
        )

    briefing = dict(briefing)
    candidate_pool = evaluate_candidate_pool(briefing, horizon="swing", limit=1)
    briefing["candidate_preview"] = (
        candidate_pool["candidates"][0] if candidate_pool["candidates"] else None
    )
    briefing["candidate_preview_summary"] = candidate_pool["summary"]
    briefing["candidate_preview_message"] = (
        candidate_pool["candidates"][0]["candidate_reason"]
        if candidate_pool["candidates"]
        else "No ranked candidate is available yet."
    )
    try:
        record_news_snapshot(briefing.get("news_item"), recorded_at=datetime.now(timezone.utc))
    except Exception as exc:
        logger.warning("Failed to record news snapshot: %s", exc)
    return render_homepage(briefing)


@app.get("/favicon.ico")
def get_favicon() -> Response:
    return Response(content=_FAVICON_SVG, media_type="image/svg+xml")


@app.get("/history")
def get_history(limit: int = Query(default=20, ge=1, le=200)):
    _require_internal_surface()
    records = load_briefing_history()
    recent_records = records[-limit:]
    return {"count": len(records), "records": recent_records}


@app.get("/history/view", response_class=HTMLResponse)
def get_history_view(limit: int = Query(default=10, ge=1, le=200)):
    _require_internal_surface()
    records = load_briefing_history()
    recent_records = records[-limit:]
    learning_summary = build_learning_summary()
    return render_history_page(recent_records, learning_summary)


@app.post("/backtest")
def post_backtest(payload: dict[str, object] = Body(default_factory=dict)):
    _require_internal_surface()
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
    _require_internal_surface()
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
    _require_internal_surface()
    return build_learning_summary()


@app.get("/memory")
def get_memory(limit: int = Query(default=20, ge=1, le=200)):
    _require_internal_surface()
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
    _require_internal_surface()
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


def _build_candidate_report(
    *,
    horizon: str,
    limit: int,
    holdings: str | None,
    investment_period: str | None,
    risk_tolerance: str | None,
    style: str | None,
    interested_markets: str | None,
    usd_jpy: float | None,
    market_change_pct: float | None,
    watchlist_symbols: str | None,
    watchlist_symbol: str | None,
    interval: str,
) -> dict[str, object]:
    source = collect_briefing_source(
        usd_jpy, market_change_pct, watchlist_symbols, watchlist_symbol, interval=interval
    )
    briefing = compose_briefing(source)
    candidate_pool = evaluate_candidate_pool(briefing, horizon=horizon, limit=limit)
    candidates = candidate_pool["candidates"]
    similar_cases = find_similar_market_memory(briefing, limit=limit)
    candidate_graph = build_knowledge_graph(briefing, scenarios=())
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
    strategy_mode = "daytrade" if horizon.strip().lower() == "daytrade" else "swing"
    sector_rotation_summary = _sector_rotation_summary(briefing, personalized["candidates"])
    graph_nodes = candidate_graph.get("nodes", [])
    graph_edges = candidate_graph.get("edges", [])
    return {
        "automation_mode": "advisory_only",
        "strategy_mode": strategy_mode,
        "count": len(personalized["candidates"]),
        "rejected_count": len(candidate_pool["excluded"]),
        "opportunity_summary": candidate_pool["summary"],
        "horizon": strategy_mode,
        "learning_summary": briefing.get("learning_summary"),
        "candidate_learning_profile": briefing.get("candidate_learning_profile"),
        "data_health": briefing.get("data_health"),
        "data_warnings": briefing.get("data_warnings", []),
        "candidate_graph": candidate_graph,
        "candidate_graph_summary": {
            "node_count": len(graph_nodes) if isinstance(graph_nodes, list) else 0,
            "edge_count": len(graph_edges) if isinstance(graph_edges, list) else 0,
            "scenario_count": len(candidate_graph.get("scenario_report", {}).get("scenarios", []))
            if isinstance(candidate_graph.get("scenario_report"), dict)
            else 0,
        },
        "sector_rotation_summary": sector_rotation_summary,
        "personal_profile": personalized["profile"],
        "personal_notes": personalized["notes"],
        "candidates": personalized["candidates"],
        "excluded_candidates": candidate_pool["excluded"],
        "similar_cases": similar_cases,
        "top_candidate": personalized["candidates"][0] if personalized["candidates"] else None,
        "briefing_id": briefing.get("briefing_id"),
    }


def _sector_rotation_summary(
    briefing: Mapping[str, object], candidates: list[Mapping[str, object]]
) -> list[str]:
    summary: list[str] = []
    rotation = briefing.get("sector_rotation")
    if isinstance(rotation, Mapping):
        for sector, strength in rotation.items():
            sector_text = _text(sector)
            strength_text = _text(strength)
            if sector_text:
                summary.append(f"{sector_text}: {strength_text or 'unrated'}")
    elif isinstance(rotation, list):
        for item in rotation:
            if not isinstance(item, Mapping):
                continue
            sector_text = _text(item.get("sector")) or _text(item.get("name"))
            if not sector_text:
                continue
            strength_text = _text(item.get("strength")) or _text(item.get("state"))
            summary.append(f"{sector_text}: {strength_text or 'unrated'}")

    top_candidate = candidates[0] if candidates else None
    if isinstance(top_candidate, Mapping):
        sector = _text(top_candidate.get("sector"))
        if sector:
            strength = _text(top_candidate.get("sector_strength"))
            note = f"Top candidate sector: {sector}"
            if strength:
                note = f"{note} ({strength})"
            summary.append(note)

    unique: list[str] = []
    for item in summary:
        if item not in unique:
            unique.append(item)
    return unique[:4]


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
    return _build_candidate_report(
        horizon=horizon,
        limit=limit,
        holdings=holdings,
        investment_period=investment_period,
        risk_tolerance=risk_tolerance,
        style=style,
        interested_markets=interested_markets,
        usd_jpy=usd_jpy,
        market_change_pct=market_change_pct,
        watchlist_symbols=watchlist_symbols,
        watchlist_symbol=watchlist_symbol,
        interval=interval,
    )


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
    report = _build_candidate_report(
        horizon=horizon,
        limit=limit,
        holdings=holdings,
        investment_period=investment_period,
        risk_tolerance=risk_tolerance,
        style=style,
        interested_markets=interested_markets,
        usd_jpy=usd_jpy,
        market_change_pct=market_change_pct,
        watchlist_symbols=watchlist_symbols,
        watchlist_symbol=watchlist_symbol,
        interval=interval,
    )
    return render_candidates_page(report)


@app.get("/daytrade-candidates")
def get_daytrade_candidates(
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
    return _build_candidate_report(
        horizon="daytrade",
        limit=limit,
        holdings=holdings,
        investment_period=investment_period,
        risk_tolerance=risk_tolerance,
        style=style,
        interested_markets=interested_markets,
        usd_jpy=usd_jpy,
        market_change_pct=market_change_pct,
        watchlist_symbols=watchlist_symbols,
        watchlist_symbol=watchlist_symbol,
        interval=interval,
    )


@app.get("/daytrade-candidates/view", response_class=HTMLResponse)
def get_daytrade_candidates_view(
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
    report = _build_candidate_report(
        horizon="daytrade",
        limit=limit,
        holdings=holdings,
        investment_period=investment_period,
        risk_tolerance=risk_tolerance,
        style=style,
        interested_markets=interested_markets,
        usd_jpy=usd_jpy,
        market_change_pct=market_change_pct,
        watchlist_symbols=watchlist_symbols,
        watchlist_symbol=watchlist_symbol,
        interval=interval,
    )
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
    _require_internal_surface()
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
        "latest_replay": latest_replay if isinstance(latest_replay, dict) else {},
        "similar_cases": similar_cases,
    }
    return render_replay_compare_page(compare)


@app.post("/simulate")
def post_simulate(payload: dict[str, object] = Body(default_factory=dict)):
    _require_internal_surface()
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
    _require_internal_surface()
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
    _require_internal_surface()
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
