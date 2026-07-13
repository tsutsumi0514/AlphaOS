from src.storage.outcome_history import load_market_outcomes, record_market_outcome


def test_record_market_outcome_appends_jsonl(tmp_path):
    path = tmp_path / "outcomes.jsonl"

    record = record_market_outcome(
        "briefing-1",
        {"market_change_pct": 1.2, "usd_jpy": 156.2},
        path=path,
    )

    assert record["type"] == "outcome"
    records = load_market_outcomes(path)
    assert len(records) == 1
    assert records[0]["briefing_id"] == "briefing-1"
    assert records[0]["outcome"]["usd_jpy"] == 156.2


def test_load_market_outcomes_ignores_bad_lines(tmp_path):
    path = tmp_path / "outcomes.jsonl"
    path.write_text('{"ok": true}\nnot-json\n', encoding="utf-8")

    records = load_market_outcomes(path)

    assert records == [{"ok": True}]
