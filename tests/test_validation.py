from datetime import date

from src.simulation.validation import run_opportunity_validation


def test_run_opportunity_validation_simulates_profitable_trades(monkeypatch):
    start = date(2026, 1, 1)
    dates = [date.fromordinal(start.toordinal() + offset) for offset in range(40)]

    def build_series(base: float, step: float):
        return [(trade_date, base + step * index) for index, trade_date in enumerate(dates)]

    series = {
        "^N225": build_series(40000.0, 5.0),
        "JPY=X": build_series(156.0, 0.02),
        "7203.T": build_series(2500.0, 120.0),
        "6758.T": build_series(13000.0, 1.0),
    }

    def loader(symbol: str, period: str):
        return series[symbol]

    monkeypatch.setattr(
        "src.simulation.validation._compose_replay_briefing",
        lambda source, thresholds: {
            "briefing_id": "alpha",
            "market_state": "neutral",
            "fx_state": "weak yen",
            "confidence": "high",
            "risk_alerts": ["Market tone is calm."],
            "reasons": ["Momentum is improving."],
            "evidence": [
                {"source": "market", "label": "Nikkei", "value": 1.2},
                {"source": "fx", "label": "USD/JPY", "value": 156.0},
                {"source": "news", "label": "News", "value": 1},
                {"source": "watchlist", "label": "watchlist", "value": 1},
            ],
            "decision_ai": {"stance": "supportive", "reason": "Decision support leans constructive."},
            "watchlist_status": [
                {**item, "volume": 2_000_000}
                for item in source["watchlist_status"]
            ],
        },
    )

    result = run_opportunity_validation(
        lookback_trading_days=12,
        symbols=("7203.T", "6758.T"),
        period="5y",
        history_loader=loader,
        transaction_cost_pct=0.001,
        horizons=("daytrade", "swing", "long"),
    )

    assert result["mode"] == "opportunity_validation"
    assert result["sample_size"] == 12
    assert result["by_horizon"]["daytrade"]["executed_trades"] > 0
    assert result["by_horizon"]["swing"]["summary"]["win_rate"] >= 0.0
    assert result["by_horizon"]["swing"]["baseline"]["summary"]["total"] == result["by_horizon"]["swing"]["summary"]["total"]
    first_trade = result["by_horizon"]["swing"]["trades"][0]
    assert first_trade["net_return_pct"] < first_trade["gross_return_pct"]
    assert result["walk_forward"]["mode"] == "walk_forward"
    assert "daytrade" in result["walk_forward"]["by_horizon"]
