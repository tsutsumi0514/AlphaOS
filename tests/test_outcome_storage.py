from pathlib import Path

from src.storage.outcome_history import load_market_outcomes, record_market_outcome
from src.storage.outcome_history import resolve_outcome_path


def test_record_market_outcome_replaces_duplicate_briefing_id(tmp_path):
    path = tmp_path / "outcomes.jsonl"

    first = record_market_outcome(
        "briefing-1",
        {"market_change_pct": 1.2, "usd_jpy": 156.2},
        path=path,
    )
    second = record_market_outcome(
        "briefing-1",
        {"market_change_pct": -0.8, "usd_jpy": 144.0},
        path=path,
    )

    assert first["type"] == "outcome"
    assert second["type"] == "outcome"
    records = load_market_outcomes(path)
    assert len(records) == 1
    assert records[0]["briefing_id"] == "briefing-1"
    assert records[0]["outcome"]["usd_jpy"] == 144.0


def test_load_market_outcomes_ignores_bad_lines(tmp_path):
    path = tmp_path / "outcomes.jsonl"
    path.write_text('{"ok": true}\nnot-json\n', encoding="utf-8")

    records = load_market_outcomes(path)

    assert records == [{"ok": True}]


def test_resolve_outcome_path_defaults_outside_repo():
    path = resolve_outcome_path()

    assert path == Path.home() / ".alphaos" / "outcome-history.jsonl"
