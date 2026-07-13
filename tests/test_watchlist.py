from src.watchlist import derive_watch_status


def test_derive_watch_status_returns_strong_for_large_gain():
    assert derive_watch_status(2.4) == "strong"


def test_derive_watch_status_returns_weak_for_large_loss():
    assert derive_watch_status(-2.1) == "weak"


def test_derive_watch_status_returns_steady_for_small_move():
    assert derive_watch_status(0.6) == "steady"
