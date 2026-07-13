from src.cache import get_cached_value


def test_get_cached_value_reuses_fresh_entry(monkeypatch):
    times = iter([0.0, 1.0, 6.0])
    monkeypatch.setattr("src.cache.monotonic", lambda: next(times))

    calls = []

    def producer():
        calls.append("called")
        return len(calls)

    first = get_cached_value("alpha", producer, ttl_seconds=5)
    second = get_cached_value("alpha", producer, ttl_seconds=5)
    third = get_cached_value("alpha", producer, ttl_seconds=5)

    assert first == 1
    assert second == 1
    assert third == 2
    assert calls == ["called", "called"]
