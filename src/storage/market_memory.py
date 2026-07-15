"""JSONL market memory storage for AlphaOS."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


DEFAULT_MEMORY_PATH = Path.home() / ".alphaos" / "market-memory.jsonl"
MEMORY_PATH_ENV = "ALPHAOS_MEMORY_PATH"


def resolve_memory_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)

    env_path = os.environ.get(MEMORY_PATH_ENV)
    if env_path:
        return Path(env_path)

    return DEFAULT_MEMORY_PATH


def record_market_memory(
    briefing: Mapping[str, Any],
    source: Mapping[str, Any] | None = None,
    outcome: Mapping[str, Any] | None = None,
    replay_summary: Mapping[str, Any] | None = None,
    path: str | Path | None = None,
) -> dict[str, Any]:
    """Append a market memory snapshot to a JSONL file."""
    memory_path = resolve_memory_path(path)
    memory_path.parent.mkdir(parents=True, exist_ok=True)

    record = _build_record(
        briefing=briefing,
        source=source,
        outcome=outcome,
        replay_summary=replay_summary,
    )
    records = [
        existing
        for existing in load_market_memory(memory_path)
        if existing.get("briefing_id") != record["briefing_id"] or record["type"] == "replay_summary"
    ]
    records.append(record)
    _write_jsonl_records(memory_path, records)
    return record


def update_market_memory(
    briefing_id: str,
    outcome: Mapping[str, Any],
    path: str | Path | None = None,
) -> dict[str, Any] | None:
    memory_path = resolve_memory_path(path)
    records = load_market_memory(memory_path)
    updated = False
    latest_record: dict[str, Any] | None = None
    for index, record in enumerate(records):
        if record.get("briefing_id") != briefing_id:
            continue
        merged = dict(record)
        merged["outcome"] = _to_jsonable(outcome)
        merged["recorded_at"] = datetime.now(timezone.utc).isoformat()
        merged["type"] = record.get("type", "market_memory")
        records[index] = merged
        latest_record = merged
        updated = True
        break

    if not updated:
        latest_record = {
            "memory_id": str(uuid4()),
            "briefing_id": briefing_id,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "type": "market_memory",
            "outcome": _to_jsonable(outcome),
        }
        records.append(latest_record)

    memory_path.parent.mkdir(parents=True, exist_ok=True)
    _write_jsonl_records(memory_path, records)
    return latest_record


def record_replay_memory(
    replay_result: Mapping[str, Any],
    path: str | Path | None = None,
) -> dict[str, Any]:
    memory_path = resolve_memory_path(path)
    memory_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "memory_id": str(uuid4()),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "type": "replay_summary",
        "replay_summary": _to_jsonable(replay_result),
    }

    records = load_market_memory(memory_path)
    records.append(record)
    _write_jsonl_records(memory_path, records)
    return record


def load_market_memory(path: str | Path | None = None) -> list[dict[str, Any]]:
    memory_path = resolve_memory_path(path)
    if not memory_path.exists():
        return []

    records: list[dict[str, Any]] = []
    with memory_path.open("r", encoding="utf-8") as handle:
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


def find_similar_market_memory(
    query: Mapping[str, Any],
    *,
    limit: int = 5,
    path: str | Path | None = None,
) -> list[dict[str, Any]]:
    query_snapshot = _snapshot(query)
    records = [
        record
        for record in load_market_memory(path)
        if record.get("type") == "market_memory"
    ]

    scored: list[dict[str, Any]] = []
    for record in records:
        score, reasons = _similarity_score(query_snapshot, record)
        scored.append(
            {
                "memory_id": record.get("memory_id"),
                "briefing_id": record.get("briefing_id"),
                "recorded_at": record.get("recorded_at"),
                "score": round(score, 3),
                "match_reasons": reasons,
                "market_state": record.get("market_state"),
                "fx_state": record.get("fx_state"),
                "confidence": record.get("confidence"),
                "risk_alerts": record.get("risk_alerts", []),
                "reasons": record.get("reasons", []),
                "evidence": record.get("evidence", []),
                "news_item": record.get("news_item"),
                "decision_ai": record.get("decision_ai"),
                "watchlist_status": record.get("watchlist_status", []),
                "outcome": record.get("outcome"),
                "replay_summary": record.get("replay_summary"),
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[: max(limit, 0)]


def load_replay_summaries(path: str | Path | None = None) -> list[dict[str, Any]]:
    records = load_market_memory(path)
    summaries: list[dict[str, Any]] = []
    for record in records:
        replay_summary = record.get("replay_summary")
        if isinstance(replay_summary, Mapping):
            summaries.append(
                {
                    "memory_id": record.get("memory_id"),
                    "recorded_at": record.get("recorded_at"),
                    "replay_summary": dict(replay_summary),
                }
            )
    return summaries


def find_latest_replay_summary(path: str | Path | None = None) -> dict[str, Any] | None:
    summaries = load_replay_summaries(path)
    if not summaries:
        return None
    return summaries[-1]


def _build_record(
    briefing: Mapping[str, Any],
    source: Mapping[str, Any] | None,
    outcome: Mapping[str, Any] | None,
    replay_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    record = _snapshot(briefing)
    record["memory_id"] = str(uuid4())
    record["recorded_at"] = datetime.now(timezone.utc).isoformat()
    record["type"] = "replay_summary" if replay_summary is not None else "market_memory"
    if source is not None:
        record["source"] = _to_jsonable(source)
    if outcome is not None:
        record["outcome"] = _to_jsonable(outcome)
    if replay_summary is not None:
        record["replay_summary"] = _to_jsonable(replay_summary)
    return record


def _snapshot(data: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "briefing_id": _text(data.get("briefing_id")),
        "market_state": _text(data.get("market_state")),
        "fx_state": _text(data.get("fx_state")),
        "confidence": _text(data.get("confidence")),
        "risk_alerts": _string_list(data.get("risk_alerts")),
        "reasons": _string_list(data.get("reasons")),
        "evidence": _evidence_list(data.get("evidence")),
        "news_item": _to_jsonable(data.get("news_item")),
        "decision_ai": _to_jsonable(data.get("decision_ai")),
        "watchlist_status": _to_jsonable(data.get("watchlist_status")),
    }


def _similarity_score(query: Mapping[str, Any], record: Mapping[str, Any]) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 0.0

    if query.get("market_state") and query.get("market_state") == record.get("market_state"):
        score += 0.32
        reasons.append("market_state")
    if query.get("fx_state") and query.get("fx_state") == record.get("fx_state"):
        score += 0.2
        reasons.append("fx_state")
    if query.get("confidence") and query.get("confidence") == record.get("confidence"):
        score += 0.1
        reasons.append("confidence")

    risk_overlap = _set_overlap(query.get("risk_alerts", []), record.get("risk_alerts", []))
    if risk_overlap:
        score += min(0.2, risk_overlap * 0.08)
        reasons.append("risk_alerts")

    reason_overlap = _set_overlap(query.get("reasons", []), record.get("reasons", []))
    if reason_overlap:
        score += min(0.1, reason_overlap * 0.03)
        reasons.append("reasons")

    evidence_overlap = _evidence_overlap(query.get("evidence", []), record.get("evidence", []))
    if evidence_overlap:
        score += min(0.18, evidence_overlap * 0.06)
        reasons.append("evidence")

    watchlist_overlap = _watchlist_overlap(
        query.get("watchlist_status", []), record.get("watchlist_status", [])
    )
    if watchlist_overlap:
        score += min(0.1, watchlist_overlap * 0.04)
        reasons.append("watchlist_status")

    if not reasons and query.get("briefing_id") and query.get("briefing_id") == record.get("briefing_id"):
        score += 0.2
        reasons.append("briefing_id")

    return min(score, 1.0), reasons[:4]


def _set_overlap(left: Any, right: Any) -> int:
    left_items = {item for item in _string_list(left)}
    right_items = {item for item in _string_list(right)}
    return len(left_items & right_items)


def _evidence_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    items: list[str] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        label = _text(item.get("label"))
        source = _text(item.get("source"))
        if label or source:
            items.append(f"{source}:{label}".strip(":"))
    return items


def _evidence_overlap(left: Any, right: Any) -> int:
    return _set_overlap(_evidence_list(left), _evidence_list(right))


def _watchlist_overlap(left: Any, right: Any) -> int:
    if not isinstance(left, list) or not isinstance(right, list):
        return 0

    def symbols(items: list[Any]) -> set[str]:
        result: set[str] = set()
        for item in items:
            if not isinstance(item, Mapping):
                continue
            symbol = _text(item.get("symbol"))
            if symbol:
                result.add(symbol)
        return result

    return len(symbols(left) & symbols(right))


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    items: list[str] = []
    for item in value:
        text = _text(item)
        if text:
            items.append(text)
    return items


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


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
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")
