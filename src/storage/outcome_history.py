"""JSONL outcome storage for AlphaOS learning."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


DEFAULT_OUTCOME_PATH = Path(".alphaos") / "outcome-history.jsonl"
OUTCOME_PATH_ENV = "ALPHAOS_OUTCOME_PATH"


def resolve_outcome_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)

    env_path = os.environ.get(OUTCOME_PATH_ENV)
    if env_path:
        return Path(env_path)

    return DEFAULT_OUTCOME_PATH


def record_market_outcome(
    briefing_id: str,
    outcome: Mapping[str, Any],
    path: str | Path | None = None,
) -> dict[str, Any]:
    """Append a market outcome to a JSONL history file."""
    outcome_path = resolve_outcome_path(path)
    outcome_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "outcome_id": str(uuid4()),
        "briefing_id": briefing_id,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "outcome": _to_jsonable(outcome),
        "type": "outcome",
    }

    with outcome_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False))
        handle.write("\n")

    return record


def load_market_outcomes(path: str | Path | None = None) -> list[dict[str, Any]]:
    outcome_path = resolve_outcome_path(path)
    if not outcome_path.exists():
        return []

    records: list[dict[str, Any]] = []
    with outcome_path.open("r", encoding="utf-8") as handle:
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
