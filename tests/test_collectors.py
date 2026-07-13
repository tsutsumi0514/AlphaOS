from src.collectors.briefing_inputs import (
    collect_briefing_source,
    parse_watchlist_symbols,
)


def test_parse_watchlist_symbols_prefers_csv():
    assert parse_watchlist_symbols("7203.T, 6758.T, ", "9984.T") == ["7203.T", "6758.T"]


def test_collect_briefing_source_returns_partial_data(monkeypatch):
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_usd_jpy_rate", lambda: 156.2)
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_nikkei_change_pct", lambda: None)
    monkeypatch.setattr(
        "src.collectors.briefing_inputs.fetch_watchlist_status",
        lambda symbols: [{"symbol": symbols[0], "status": "strong"}],
    )
    monkeypatch.setattr(
        "src.collectors.briefing_inputs.fetch_latest_market_news",
        lambda: None,
    )

    source = collect_briefing_source(watchlist_symbol="9984.T")

    assert source == {
        "usd_jpy": 156.2,
        "watchlist_status": [{"symbol": "9984.T", "status": "strong"}],
    }


def test_collect_briefing_source_survives_failures(monkeypatch):
    monkeypatch.setattr(
        "src.collectors.briefing_inputs.fetch_usd_jpy_rate",
        lambda: (_ for _ in ()).throw(RuntimeError("fx down")),
    )
    monkeypatch.setattr(
        "src.collectors.briefing_inputs.fetch_nikkei_change_pct",
        lambda: (_ for _ in ()).throw(RuntimeError("market down")),
    )
    monkeypatch.setattr(
        "src.collectors.briefing_inputs.fetch_watchlist_status",
        lambda symbols: (_ for _ in ()).throw(RuntimeError("watchlist down")),
    )
    monkeypatch.setattr(
        "src.collectors.briefing_inputs.fetch_latest_market_news",
        lambda: (_ for _ in ()).throw(RuntimeError("news down")),
    )

    assert collect_briefing_source() is None
