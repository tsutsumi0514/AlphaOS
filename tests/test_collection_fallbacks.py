from __future__ import annotations

from src.fx import fetch_usd_jpy_rate
from src.market import fetch_nikkei_change_pct
from src.news import fetch_latest_market_news


def test_fetch_usd_jpy_rate_falls_back_to_daily(monkeypatch):
    seen: list[str] = []

    def fake_uncached(interval: str):
        seen.append(interval)
        return 156.2 if interval == "1d" else None

    monkeypatch.setattr("src.fx._fetch_usd_jpy_rate_uncached", fake_uncached)

    assert fetch_usd_jpy_rate("1m") == 156.2
    assert seen == ["1m", "1d"]


def test_fetch_nikkei_change_pct_falls_back_to_daily(monkeypatch):
    seen: list[str] = []

    def fake_uncached(interval: str):
        seen.append(interval)
        return 1.2 if interval == "1d" else None

    monkeypatch.setattr("src.market._fetch_nikkei_change_pct_uncached", fake_uncached)

    assert fetch_nikkei_change_pct("1m") == 1.2
    assert seen == ["1m", "1d"]


def test_fetch_latest_market_news_tries_multiple_queries(monkeypatch):
    seen: list[str] = []

    def fake_cache(key, producer, ttl_seconds):
        return producer()

    def fake_uncached(query: str):
        seen.append(query)
        if query == "日経平均":
            return None
        return {
            "title": "日本株に買い",
            "source": "Google News",
            "url": "https://example.com/news",
            "query": query,
        }

    monkeypatch.setattr("src.news.get_cached_value", fake_cache)
    monkeypatch.setattr("src.news._fetch_latest_market_news_uncached", fake_uncached)

    result = fetch_latest_market_news(["日本株"])

    assert result is not None
    assert result["query"] == "日本株"
    assert seen == ["日経平均", "日本株"]
