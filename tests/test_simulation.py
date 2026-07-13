from datetime import date

from src.simulation.replay import run_replay_simulation


def test_run_replay_simulation_scores_historical_pairs(monkeypatch):
    series = {
        "^N225": [
            (date(2026, 7, 8), 40000.0),
            (date(2026, 7, 9), 40400.0),
            (date(2026, 7, 10), 40800.0),
            (date(2026, 7, 13), 41200.0),
        ],
        "JPY=X": [
            (date(2026, 7, 8), 150.0),
            (date(2026, 7, 9), 151.0),
            (date(2026, 7, 10), 152.0),
            (date(2026, 7, 13), 153.0),
        ],
        "7203.T": [
            (date(2026, 7, 8), 2500.0),
            (date(2026, 7, 9), 2550.0),
            (date(2026, 7, 10), 2600.0),
            (date(2026, 7, 13), 2650.0),
        ],
        "6758.T": [
            (date(2026, 7, 8), 13000.0),
            (date(2026, 7, 9), 12900.0),
            (date(2026, 7, 10), 12800.0),
            (date(2026, 7, 13), 12700.0),
        ],
        "9984.T": [
            (date(2026, 7, 8), 9000.0),
            (date(2026, 7, 9), 9100.0),
            (date(2026, 7, 10), 9200.0),
            (date(2026, 7, 13), 9300.0),
        ],
    }

    def loader(symbol: str, period: str):
        return series[symbol]

    def archived_news(target_date):
        return {
            "title": f"news for {target_date}",
            "source": "Archive",
            "url": "https://example.com/archive",
            "published_at": "2026-07-09T00:00:00+00:00",
        }

    monkeypatch.setattr("src.simulation.replay.find_latest_news_before", archived_news)

    result = run_replay_simulation(
        lookback_trading_days=2,
        symbols=("7203.T", "6758.T", "9984.T"),
        period="6mo",
        history_loader=loader,
    )

    assert result["mode"] == "replay"
    assert result["sample_size"] == 2
    assert result["summary"]["total"] == 2
    assert result["calibration"]["enabled"] is True
    assert result["calibration"]["summary"]["total"] == 2
    assert result["baseline"]["summary"]["total"] == 2
    assert result["results"][0]["briefing"]["decision_ai"]["agent"] == "ChairmanAI"
    assert result["results"][0]["briefing"]["news_item"]["title"].startswith("news for")
    assert result["validation"]["mode"] == "walk_forward"
