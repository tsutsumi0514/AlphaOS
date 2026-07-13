"""JSONL history storage for AlphaOS briefings."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


DEFAULT_HISTORY_PATH = Path(".alphaos") / "briefing-history.jsonl"
HISTORY_PATH_ENV = "ALPHAOS_HISTORY_PATH"


def resolve_history_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)

    env_path = os.environ.get(HISTORY_PATH_ENV)
    if env_path:
        return Path(env_path)

    return DEFAULT_HISTORY_PATH


def record_briefing_snapshot(
    briefing: Mapping[str, Any],
    source: Mapping[str, Any] | None = None,
    path: str | Path | None = None,
) -> dict[str, Any]:
    """Append a briefing snapshot to a JSONL history file."""
    history_path = resolve_history_path(path)
    history_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "briefing_id": str(uuid4()),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "briefing": _to_jsonable(briefing),
        "source": _to_jsonable(source) if source is not None else None,
        "type": "briefing",
    }

    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False))
        handle.write("\n")

    return record


def load_briefing_history(path: str | Path | None = None) -> list[dict[str, Any]]:
    history_path = resolve_history_path(path)
    if not history_path.exists():
        return []

    records: list[dict[str, Any]] = []
    with history_path.open("r", encoding="utf-8") as handle:
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
