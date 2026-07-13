"""JSONL news archive storage for AlphaOS."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


DEFAULT_NEWS_PATH = Path.home() / ".alphaos" / "news-history.jsonl"
NEWS_PATH_ENV = "ALPHAOS_NEWS_PATH"


def resolve_news_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)

    env_path = os.environ.get(NEWS_PATH_ENV)
    if env_path:
        return Path(env_path)

    return DEFAULT_NEWS_PATH


def record_news_snapshot(
    news_item: Mapping[str, Any] | None,
    path: str | Path | None = None,
    recorded_at: datetime | None = None,
) -> dict[str, Any] | None:
    if not isinstance(news_item, Mapping):
        return None

    title = news_item.get("title")
    if not isinstance(title, str) or not title.strip():
        return None

    news_path = resolve_news_path(path)
    news_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "news_id": str(uuid4()),
        "recorded_at": _ensure_utc(recorded_at or datetime.now(timezone.utc)).isoformat(),
        "news_item": _to_jsonable(news_item),
        "type": "news",
    }

    with news_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False))
        handle.write("\n")

    return record


def load_news_history(path: str | Path | None = None) -> list[dict[str, Any]]:
    news_path = resolve_news_path(path)
    if not news_path.exists():
        return []

    records: list[dict[str, Any]] = []
    with news_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
    return records


def find_latest_news_before(
    target: date | datetime | str | None,
    path: str | Path | None = None,
) -> dict[str, Any] | None:
    if target is None:
        return None

    target_date = _to_date(target)
    if target_date is None:
        return None

    records = load_news_history(path)
    best_record: dict[str, Any] | None = None
    best_date: date | None = None

    for record in records:
        news_item = record.get("news_item")
        if not isinstance(news_item, Mapping):
            continue

        published_at = _news_item_date(news_item)
        if published_at is None or published_at > target_date:
            continue

        if best_date is None or published_at > best_date:
            best_record = record
            best_date = published_at

    if best_record is None:
        return None

    news_item = best_record.get("news_item")
    if not isinstance(news_item, Mapping):
        return None

    return dict(news_item)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _news_item_date(news_item: Mapping[str, Any]) -> date | None:
    published_at = news_item.get("published_at")
    return _to_date(published_at)


def _to_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed.date()
    return None


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _to_jsonable(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value
