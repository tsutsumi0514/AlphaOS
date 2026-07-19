"""Live market refresh helpers for AlphaOS."""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from collections.abc import Callable
from typing import Any, Mapping

from ..agents.chairman_ai import compose_briefing
from ..collectors.briefing_inputs import collect_briefing_source

logger = logging.getLogger(__name__)

LIVE_REFRESH_ENABLED_ENV = "ALPHAOS_LIVE_REFRESH_ENABLED"
LIVE_REFRESH_INTERVAL_ENV = "ALPHAOS_LIVE_REFRESH_INTERVAL_SECONDS"
DEFAULT_LIVE_REFRESH_INTERVAL_SECONDS = 60
DEFAULT_BRIEFING_INTERVAL = "1d"


def live_refresh_enabled() -> bool:
    value = os.environ.get(LIVE_REFRESH_ENABLED_ENV, "1")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def live_refresh_interval_seconds() -> int:
    value = os.environ.get(LIVE_REFRESH_INTERVAL_ENV, "").strip()
    if not value:
        return DEFAULT_LIVE_REFRESH_INTERVAL_SECONDS
    try:
        interval = int(value)
    except ValueError:
        return DEFAULT_LIVE_REFRESH_INTERVAL_SECONDS
    if interval < 1:
        return DEFAULT_LIVE_REFRESH_INTERVAL_SECONDS
    return interval


def build_live_snapshot(
    interval: str = DEFAULT_BRIEFING_INTERVAL,
    *,
    refresh_interval_seconds: int | None = None,
) -> dict[str, Any]:
    """Build a live briefing snapshot and attach refresh metadata."""
    source = collect_briefing_source(interval=interval) or {}
    briefing = compose_briefing(source)
    if isinstance(briefing, Mapping):
        briefing = dict(briefing)
    else:
        briefing = {"briefing": briefing}

    attach_live_refresh_metadata(
        briefing,
        source,
        briefing_interval=interval,
        refresh_interval_seconds=refresh_interval_seconds,
        refreshed_at=datetime.now(timezone.utc).isoformat(),
    )
    return {
        "briefing": briefing,
        "source": source,
        "refresh_status": briefing.get("market_refresh", {}),
        "refreshed_at": briefing.get("market_refresh", {}).get("refreshed_at"),
    }


def attach_live_refresh_metadata(
    briefing: dict[str, Any],
    source: Mapping[str, Any] | None,
    *,
    briefing_interval: str,
    refresh_interval_seconds: int | None = None,
    refreshed_at: str | None = None,
) -> dict[str, Any]:
    data_health = source.get("data_health", {}) if isinstance(source, Mapping) else {}
    warnings = source.get("data_warnings", []) if isinstance(source, Mapping) else []
    metadata = {
        "enabled": live_refresh_enabled(),
        "briefing_interval": briefing_interval,
        "interval_seconds": _sanitize_interval_seconds(refresh_interval_seconds),
        "refreshed_at": refreshed_at or datetime.now(timezone.utc).isoformat(),
        "status": _refresh_status(data_health),
        "available_inputs": _available_inputs(data_health),
        "warnings": _warning_items(warnings),
    }
    briefing["market_refresh"] = metadata
    if "data_health" not in briefing and isinstance(data_health, Mapping):
        briefing["data_health"] = dict(data_health)
    if "data_warnings" not in briefing and metadata["warnings"]:
        briefing["data_warnings"] = list(metadata["warnings"])
    return metadata


async def run_live_refresh_loop(
    store_snapshot: Callable[[dict[str, Any]], None],
    *,
    interval_seconds_provider: Callable[[], int] | None = None,
    briefing_interval: str = DEFAULT_BRIEFING_INTERVAL,
    stop_event: asyncio.Event | None = None,
) -> None:
    """Refresh the live briefing on a fixed interval until stopped."""
    if stop_event is None:
        stop_event = asyncio.Event()

    while not stop_event.is_set():
        refresh_seconds = (
            interval_seconds_provider() if interval_seconds_provider is not None else live_refresh_interval_seconds()
        )
        refresh_seconds = _sanitize_interval_seconds(refresh_seconds)
        try:
            snapshot = await asyncio.to_thread(
                build_live_snapshot,
                briefing_interval,
                refresh_interval_seconds=refresh_seconds,
            )
            store_snapshot(snapshot)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Live market refresh failed: %s", exc)

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=refresh_seconds)
        except asyncio.TimeoutError:
            continue


def _refresh_status(data_health: Any) -> str:
    if not isinstance(data_health, Mapping):
        return "unknown"
    status = data_health.get("status")
    if isinstance(status, str) and status.strip():
        return status.strip()
    return "unknown"


def _available_inputs(data_health: Any) -> int:
    if not isinstance(data_health, Mapping):
        return 0
    try:
        return max(int(data_health.get("available_inputs", 0) or 0), 0)
    except Exception:
        return 0


def _warning_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            items.append(item.strip())
    return items


def _sanitize_interval_seconds(value: Any) -> int:
    try:
        interval = int(value)
    except Exception:
        return live_refresh_interval_seconds()
    if interval < 1:
        return live_refresh_interval_seconds()
    return interval
