from datetime import datetime, timezone
from pathlib import Path

from src.storage.news_history import (
    find_latest_news_before,
    load_news_history,
    record_news_snapshot,
    resolve_news_path,
)


def test_record_news_snapshot_appends_jsonl(tmp_path):
    path = tmp_path / "news.jsonl"

    record = record_news_snapshot(
        {
            "title": "日経平均、寄り付き後に上昇",
            "source": "Google News",
            "url": "https://example.com/news",
            "published_at": "2026-07-10T01:00:00+00:00",
        },
        path=path,
        recorded_at=datetime(2026, 7, 10, 2, 0, tzinfo=timezone.utc),
    )

    assert record["type"] == "news"
    records = load_news_history(path)
    assert len(records) == 1
    assert records[0]["news_item"]["title"] == "日経平均、寄り付き後に上昇"


def test_find_latest_news_before_returns_most_recent_item(tmp_path):
    path = tmp_path / "news.jsonl"
    record_news_snapshot(
        {
            "title": "older",
            "source": "Google News",
            "url": "https://example.com/older",
            "published_at": "2026-07-08T01:00:00+00:00",
        },
        path=path,
        recorded_at=datetime(2026, 7, 8, 2, 0, tzinfo=timezone.utc),
    )
    record_news_snapshot(
        {
            "title": "newer",
            "source": "Google News",
            "url": "https://example.com/newer",
            "published_at": "2026-07-10T01:00:00+00:00",
        },
        path=path,
        recorded_at=datetime(2026, 7, 10, 2, 0, tzinfo=timezone.utc),
    )

    news_item = find_latest_news_before("2026-07-09", path=path)

    assert news_item is not None
    assert news_item["title"] == "older"


def test_resolve_news_path_defaults_outside_repo():
    path = resolve_news_path()

    assert path == Path.home() / ".alphaos" / "news-history.jsonl"
