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


def test_collect_briefing_source_adds_watchlist_diagnostics(monkeypatch):
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_usd_jpy_rate", lambda: 156.2)
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_nikkei_change_pct", lambda: 1.2)
    monkeypatch.setattr(
        "src.collectors.briefing_inputs.fetch_watchlist_status",
        lambda symbols, interval="1d": [
            {"symbol": "7203.T", "status": "strong", "change_pct": 2.4},
            {"symbol": "6758.T", "status": "weak", "change_pct": -3.1},
            {"symbol": "9984.T", "status": "steady", "change_pct": 0.2},
        ],
    )
    monkeypatch.setattr(
        "src.collectors.briefing_inputs.fetch_latest_market_news",
        lambda: {"title": "news", "source": "Archive", "query": "日本株"},
    )

    source = collect_briefing_source()

    data_health = source["data_health"]
    assert data_health["watchlist_count"] == 3
    assert data_health["strong_watchlist_count"] == 1
    assert data_health["weak_watchlist_count"] == 1
    assert data_health["top_watchlist_symbol"] == "6758.T"
    assert data_health["news_query"] == "日本株"


def test_collect_briefing_source_falls_back_to_daily_market_data(monkeypatch):
    seen = {"fx": [], "market": [], "watchlist": []}

    def fake_usd_jpy_rate(interval):
        seen["fx"].append(interval)
        return 156.2 if interval == "1d" else None

    def fake_nikkei_change_pct(interval):
        seen["market"].append(interval)
        return 1.2 if interval == "1d" else None

    def fake_watchlist_status(symbols, interval):
        seen["watchlist"].append(interval)
        if interval == "1d":
            return [{"symbol": symbols[0], "status": "strong"}]
        return []

    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_usd_jpy_rate", fake_usd_jpy_rate)
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_nikkei_change_pct", fake_nikkei_change_pct)
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_watchlist_status", fake_watchlist_status)
    monkeypatch.setattr("src.collectors.briefing_inputs.fetch_latest_market_news", lambda: None)

    source = collect_briefing_source(interval="1m")

    assert source["usd_jpy"] == 156.2
    assert source["market_change_pct"] == 1.2
    assert source["watchlist_status"] == [{"symbol": "7203.T", "status": "strong"}]
    assert seen["fx"] == ["1m", "1d"]
    assert seen["market"] == ["1m", "1d"]
    assert seen["watchlist"] == ["1m", "1d"]
