"""JSONL outcome storage for AlphaOS learning."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4


DEFAULT_OUTCOME_PATH = Path.home() / ".alphaos" / "outcome-history.jsonl"
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
    """Store a market outcome in a JSONL history file.

    When the same briefing_id is recorded again, the latest outcome replaces
    the previous one so the learning loop stays idempotent.
    """
    outcome_path = resolve_outcome_path(path)
    outcome_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "outcome_id": str(uuid4()),
        "briefing_id": briefing_id,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "outcome": _to_jsonable(outcome),
        "type": "outcome",
    }

    records = [
        existing
        for existing in load_market_outcomes(outcome_path)
        if existing.get("briefing_id") != briefing_id
    ]
    records.append(record)
    _write_jsonl_records(outcome_path, records)

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


def _write_jsonl_records(path: Path, records: list[dict[str, Any]]) -> None:
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as handle:
        temp_path = Path(handle.name)
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")

    temp_path.replace(path)
