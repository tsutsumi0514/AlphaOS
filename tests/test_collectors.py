from src.collectors.briefing_inputs import (
    collect_briefing_source,
    parse_watchlist_symbols,
)


def test_parse_watchlist_symbols_prefers_csv():
    assert parse_watchlist_symbols("7203.T, 6758.T, ", "9984.T") == ["7203.T", "6758.T"]


def test_parse_watchlist_symbols_uses_default_for_blank_single_symbol():
    assert parse_watchlist_symbols(None, "   ") == ["7203.T", "6758.T", "9984.T"]


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

    assert source["usd_jpy"] == 156.2
    assert source["watchlist_status"] == [{"symbol": "9984.T", "status": "strong"}]
    assert source["data_health"]["status"] == "ok"
    assert source["data_health"]["available_inputs"] == 2
    assert source["data_health"]["requested_watchlist_symbols"] == ["9984.T"]
    assert "data_warnings" not in source


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

    source = collect_briefing_source()

    assert source is not None
    assert source["data_health"]["status"] == "degraded"
    assert source["data_health"]["available_inputs"] == 0
    assert source["data_warnings"]
    assert any("usd_jpy unavailable" in warning for warning in source["data_warnings"])
    assert any("market_change_pct unavailable" in warning for warning in source["data_warnings"])


def test_collect_briefing_source_passes_interval_to_fetchers(monkeypatch):
    seen = {}

    def fake_usd_jpy_rate(interval):
        seen["usd_jpy"] = interval
        return 156.2

    def fake_nikkei_change_pct(interval):
        seen["market"] = interval
        return 1.2

    def fake_watchlist_status(symbols, interval):
        seen["watchlist"] = interval
        return [{"symbol": symbols[0], "status": "strong"}]

    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_usd_jpy_rate", fake_usd_jpy_rate)
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_nikkei_change_pct", fake_nikkei_change_pct)
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_watchlist_status", fake_watchlist_status)
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_latest_market_news", lambda: None)

    source = collect_briefing_source(watchlist_symbol="9984.T", interval="1m")

    assert source["data_interval"] == "1m"
    assert seen == {"usd_jpy": "1m", "market": "1m", "watchlist": "1m"}
