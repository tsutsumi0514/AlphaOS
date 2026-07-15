from datetime import date, datetime, timedelta, timezone

from src.learning.backtest import ReplayThresholds
from src.simulation.replay import _compose_replay_briefing
from src.simulation.replay import run_replay_simulation
from src.simulation.replay import run_walk_forward_validation


def test_run_walk_forward_validation_uses_fixed_rolling_training_window(monkeypatch):
    records = []
    for index in range(8):
        briefing_date = date.fromordinal(date(2026, 1, 1).toordinal() + index)
        outcome_date = date.fromordinal(date(2026, 1, 1).toordinal() + index + 1)
        records.append(
            {
                "briefing_date": briefing_date,
                "outcome_date": outcome_date,
                "source": {
                    "briefing_date": briefing_date,
                    "market_change_pct": 1.0,
                    "usd_jpy": 150.0,
                    "watchlist_status": [],
                },
                "outcome": {
                    "market_change_pct": 1.0,
                    "usd_jpy": 150.0,
                    "watchlist_status": [],
                },
            }
        )

    captured_lengths: list[int] = []

    def fake_calibrate(window_records):
        captured_lengths.append(len(window_records))
        return ReplayThresholds()

    monkeypatch.setattr("src.simulation.replay.calibrate_replay_thresholds", fake_calibrate)

    result = run_walk_forward_validation(records, training_window=3, evaluation_window=2)

    assert result["mode"] == "walk_forward"
    assert captured_lengths == [3, 3, 3]
    assert result["sample_size"] == 5


def test_compose_replay_briefing_uses_live_briefing_path(monkeypatch):
    captured_source = {}

    def fake_compose_briefing(source, learning_summary=None):
        captured_source.update(source)
        return {
            "headline": "live headline",
            "market_state": "balanced",
            "fx_state": "neutral",
            "watchlist_status": [],
            "risk_alerts": [],
            "key_changes": [],
            "reasons": [],
            "evidence": [],
            "confidence": "medium",
            "decision_ai": {"agent": "ChairmanAI", "views": []},
        }

    monkeypatch.setattr("src.simulation.replay.compose_briefing", fake_compose_briefing)
    monkeypatch.setattr(
        "src.simulation.replay.find_latest_news_before",
        lambda target_date: {
            "title": "archive",
            "source": "Archive",
            "url": "https://example.com/archive",
            "published_at": "2026-01-01T00:00:00+00:00",
        },
    )

    result = _compose_replay_briefing(
        {
            "briefing_date": date(2026, 1, 5),
            "market_change_pct": 1.2,
            "usd_jpy": 156.2,
            "watchlist_status": [
                {"symbol": "7203.T", "change_pct": 2.1, "status": "strong"}
            ],
            "source": "live",
        },
        ReplayThresholds(),
    )

    assert result["headline"] == "live headline"
    assert result["decision_ai"]["agent"] == "ChairmanAI"
    assert captured_source["market_state_override"] in {"bullish", "bearish", "neutral"}
    assert "key_changes" not in captured_source


def test_run_replay_simulation_supports_five_hundred_sample_validation(monkeypatch):
    start = date(2026, 1, 1)
    dates = [date.fromordinal(start.toordinal() + offset) for offset in range(522)]

    def build_series(base: float, step: float):
        return [(trade_date, base + step * index) for index, trade_date in enumerate(dates)]

    series = {
        "^N225": build_series(40000.0, 8.0),
        "JPY=X": build_series(150.0, 0.15),
        "7203.T": build_series(2500.0, 4.0),
        "6758.T": build_series(13000.0, 3.0),
        "9984.T": build_series(9000.0, 5.0),
    }

    def loader(symbol: str, period: str):
        return series[symbol]

    monkeypatch.setattr(
        "src.simulation.replay.find_latest_news_before",
        lambda target_date: {
            "title": f"archive {target_date}",
            "source": "Archive",
            "url": "https://example.com/archive",
            "published_at": "2026-01-01T00:00:00+00:00",
        },
    )
    monkeypatch.setattr(
        "src.simulation.replay.compose_briefing",
        lambda source, learning_summary=None: {
            "headline": "replay",
            "market_state": source.get("market_state_override", "neutral"),
            "fx_state": source.get("fx_state_override", "neutral"),
            "news_item": source.get("news_item"),
            "watchlist_status": source.get("watchlist_status_override", []),
            "risk_alerts": [],
            "key_changes": [],
            "reasons": [],
            "evidence": [],
            "confidence": "medium",
            "decision_ai": {"agent": "ChairmanAI", "views": []},
        },
    )
    monkeypatch.setattr(
        "src.simulation.replay.score_briefing_against_outcome",
        lambda briefing, outcome, thresholds=None: {
            "matched": 5,
            "total": 5,
            "accuracy": 1.0,
            "active_checks": 5,
            "active_matched": 5,
            "coverage": 1.0,
            "active_accuracy": 1.0,
            "weighted_matched": 7.0,
            "weighted_total": 7.0,
            "weighted_accuracy": 1.0,
        },
    )

    result = run_replay_simulation(
        lookback_trading_days=500,
        period="5y",
        symbols=("7203.T", "6758.T", "9984.T"),
        history_loader=loader,
    )

    assert result["sample_size"] == 500
    assert result["summary"]["total"] == 500
    assert result["summary"]["accuracy"] >= 0.8
    assert result["validation"]["sample_size"] >= 500
    assert result["validation"]["summary"]["accuracy"] >= 0.8


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


def test_run_replay_simulation_passes_minute_interval_to_loader(monkeypatch):
    start = datetime(2026, 7, 8, 9, 0, tzinfo=timezone.utc)
    points = [start + timedelta(minutes=offset) for offset in range(8)]

    def build_series(base: float, step: float):
        return [(point, base + step * index) for index, point in enumerate(points)]

    series = {
        "^N225": build_series(40000.0, 8.0),
        "JPY=X": build_series(150.0, 0.15),
        "7203.T": build_series(2500.0, 4.0),
    }

    seen: list[tuple[str, str, str]] = []

    def loader(symbol: str, period: str, interval: str = "1d"):
        seen.append((symbol, period, interval))
        return series[symbol]

    monkeypatch.setattr(
        "src.simulation.replay.compose_briefing",
        lambda source, learning_summary=None: {
            "headline": "replay",
            "market_state": source.get("market_state_override", "neutral"),
            "fx_state": source.get("fx_state_override", "neutral"),
            "news_item": source.get("news_item"),
            "watchlist_status": source.get("watchlist_status_override", []),
            "risk_alerts": [],
            "key_changes": [],
            "reasons": [],
            "evidence": [],
            "confidence": "medium",
            "decision_ai": {"agent": "ChairmanAI", "views": []},
        },
    )
    monkeypatch.setattr(
        "src.simulation.replay.find_latest_news_before",
        lambda target_date: {
            "title": "minute news",
            "source": "Archive",
            "url": "https://example.com/archive",
            "published_at": "2026-07-08T00:00:00+00:00",
        },
    )

    result = run_replay_simulation(
        lookback_trading_days=4,
        symbols=("7203.T",),
        period="5d",
        history_loader=loader,
        interval="1m",
    )

    assert result["interval"] == "1m"
    assert result["sample_size"] > 0
    assert any(interval == "1m" for _, _, interval in seen)
