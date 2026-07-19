from __future__ import annotations

import asyncio

from src.services.live_refresh import build_live_snapshot
from src.services.live_refresh import run_live_refresh_loop


def test_build_live_snapshot_attaches_refresh_metadata(monkeypatch):
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_usd_jpy_rate", lambda: 156.2)
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_nikkei_change_pct", lambda: 1.2)
    monkeypatch.setattr(
        "src.collectors.briefing_inputs.fetch_watchlist_status",
        lambda symbols: [
            {
                "symbol": symbol,
                "price": 2810.0,
                "change_pct": 2.4,
                "status": "strong",
            }
            for symbol in symbols
        ],
    )
    monkeypatch.setattr(
        "src.collectors.briefing_inputs.fetch_latest_market_news",
        lambda: {
            "title": "日経平均、寄り付き後に上昇",
            "source": "Google News",
            "url": "https://example.com/news",
        },
    )

    snapshot = build_live_snapshot()

    assert "briefing" in snapshot
    assert snapshot["briefing"]["market_refresh"]["enabled"] is True
    assert snapshot["briefing"]["market_refresh"]["briefing_interval"] == "1d"
    assert snapshot["briefing"]["headline"]


def test_live_refresh_loop_stops_after_one_refresh(monkeypatch):
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_usd_jpy_rate", lambda: 156.2)
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_nikkei_change_pct", lambda: 1.2)
    monkeypatch.setattr(
        "src.collectors.briefing_inputs.fetch_watchlist_status",
        lambda symbols: [
            {
                "symbol": symbol,
                "price": 2810.0,
                "change_pct": 2.4,
                "status": "strong",
            }
            for symbol in symbols
        ],
    )
    monkeypatch.setattr(
        "src.collectors.briefing_inputs.fetch_latest_market_news",
        lambda: {
            "title": "日経平均、寄り付き後に上昇",
            "source": "Google News",
            "url": "https://example.com/news",
        },
    )

    snapshots: list[dict[str, object]] = []
    stop_event = asyncio.Event()

    def store_snapshot(snapshot: dict[str, object]) -> None:
        snapshots.append(snapshot)
        stop_event.set()

    asyncio.run(
        run_live_refresh_loop(
            store_snapshot,
            interval_seconds_provider=lambda: 1,
            stop_event=stop_event,
        )
    )

    assert len(snapshots) == 1
    assert snapshots[0]["briefing"]["market_refresh"]["enabled"] is True
    assert snapshots[0]["briefing"]["market_refresh"]["interval_seconds"] == 1
