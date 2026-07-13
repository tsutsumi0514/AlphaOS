from pathlib import Path

from src.storage.briefing_history import load_briefing_history, record_briefing_snapshot
from src.storage.briefing_history import resolve_history_path


def test_record_briefing_snapshot_appends_jsonl(tmp_path):
    path = tmp_path / "history.jsonl"

    record = record_briefing_snapshot(
        {"headline": "demo"},
        {"market_change_pct": 1.2},
        path=path,
    )

    assert record["type"] == "briefing"
    assert path.exists()

    records = load_briefing_history(path)
    assert len(records) == 1
    assert records[0]["briefing"]["headline"] == "demo"
    assert records[0]["source"]["market_change_pct"] == 1.2


def test_load_briefing_history_ignores_bad_lines(tmp_path):
    path = tmp_path / "history.jsonl"
    path.write_text('{"ok": true}\nnot-json\n', encoding="utf-8")

    records = load_briefing_history(path)

    assert records == [{"ok": True}]


def test_resolve_history_path_defaults_outside_repo():
    path = resolve_history_path()

    assert path == Path.home() / ".alphaos" / "briefing-history.jsonl"
