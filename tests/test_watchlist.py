from src.watchlist import derive_watch_status, fetch_watchlist_status


def test_derive_watch_status_returns_strong_for_large_gain():
    assert derive_watch_status(2.4) == "strong"


def test_derive_watch_status_returns_weak_for_large_loss():
    assert derive_watch_status(-2.1) == "weak"


def test_derive_watch_status_returns_steady_for_small_move():
    assert derive_watch_status(0.6) == "steady"


def test_fetch_watchlist_status_returns_multiple_symbols(monkeypatch):
    seen_keys: list[str] = []

    def fake_get_cached_value(key, producer, ttl_seconds):
        seen_keys.append(key)
        return producer()

    def fake_fetch(symbol, interval):
        return [
            {
                "symbol": symbol,
                "price": 100.0,
                "change_pct": 1.0,
                "volume": 250000,
                "avg_volume": 225000,
                "status": "steady",
            }
        ]

    monkeypatch.setattr("src.watchlist.get_cached_value", fake_get_cached_value)
    monkeypatch.setattr("src.watchlist._fetch_watchlist_status_uncached", fake_fetch)

    statuses = fetch_watchlist_status(["7203.T", "6758.T"], interval="1m")

    assert [item["symbol"] for item in statuses] == ["7203.T", "6758.T"]
    assert all("volume" in item for item in statuses)
    assert seen_keys == ["watchlist.1m.7203.T", "watchlist.1m.6758.T"]
