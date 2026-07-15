"""Simple what-if simulation helpers for AlphaOS."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypedDict


class WhatIfScenario(TypedDict):
    name: str
    description: str
    market_bias: str
    fx_bias: str
    opportunity_bias: str
    risk_bias: str
    confidence: str
    affected_horizons: list[str]
    rationale: list[str]


DEFAULT_SCENARIOS = (
    "yen_appreciation",
    "rate_cut",
    "oil_spike",
    "taiwan_conflict",
    "us_recession",
)


def run_what_if_simulation(
    briefing: Mapping[str, Any],
    scenarios: Sequence[str] = DEFAULT_SCENARIOS,
) -> dict[str, Any]:
    items = [_evaluate_scenario(briefing, scenario) for scenario in _normalize_scenarios(scenarios)]
    return {
        "scenario_count": len(items),
        "scenarios": items,
        "briefing_context": {
            "market_state": briefing.get("market_state"),
            "fx_state": briefing.get("fx_state"),
            "confidence": briefing.get("confidence"),
            "risk_alerts": briefing.get("risk_alerts", []),
        },
    }


def _evaluate_scenario(briefing: Mapping[str, Any], scenario: str) -> WhatIfScenario:
    market_state = _text(briefing.get("market_state"))
    fx_state = _text(briefing.get("fx_state"))
    baseline_confidence = _text(briefing.get("confidence"), "low")

    if scenario == "yen_appreciation":
        return {
            "name": scenario,
            "description": "円高が進んだ場合の波及",
            "market_bias": "bearish",
            "fx_bias": "strong yen",
            "opportunity_bias": "negative",
            "risk_bias": "high",
            "confidence": baseline_confidence,
            "affected_horizons": ["daytrade", "swing", "long"],
            "rationale": [
                "輸出関連の候補に逆風がかかりやすい。",
                "既存の weak yen 前提は弱まる。",
                "risk_alerts を強める方向に働く。",
            ],
        }
    if scenario == "rate_cut":
        return {
            "name": scenario,
            "description": "利下げが実施された場合の波及",
            "market_bias": "bullish",
            "fx_bias": "weak yen",
            "opportunity_bias": "positive",
            "risk_bias": "moderate",
            "confidence": baseline_confidence,
            "affected_horizons": ["swing", "long"],
            "rationale": [
                "リスク資産の評価を押し上げやすい。",
                "弱い円と組み合わさると輸出候補を支えやすい。",
            ],
        }
    if scenario == "oil_spike":
        return {
            "name": scenario,
            "description": "原油高が進んだ場合の波及",
            "market_bias": "bearish",
            "fx_bias": fx_state or "neutral",
            "opportunity_bias": "mixed",
            "risk_bias": "high",
            "confidence": baseline_confidence,
            "affected_horizons": ["daytrade", "swing"],
            "rationale": [
                "コスト圧力で利益見通しが悪化しやすい。",
                "インフレ懸念が再燃すると評価倍率が下がりやすい。",
            ],
        }
    if scenario == "taiwan_conflict":
        return {
            "name": scenario,
            "description": "台湾有事が発生した場合の波及",
            "market_bias": "bearish",
            "fx_bias": "strong yen",
            "opportunity_bias": "negative",
            "risk_bias": "very_high",
            "confidence": "low",
            "affected_horizons": ["daytrade", "swing", "long"],
            "rationale": [
                "地政学リスクで全面的な risk-off になりやすい。",
                "輸出・半導体・サプライチェーン全体が不安定化しやすい。",
            ],
        }
    if scenario == "us_recession":
        return {
            "name": scenario,
            "description": "米国景気後退が強まった場合の波及",
            "market_bias": "bearish",
            "fx_bias": "strong yen",
            "opportunity_bias": "negative",
            "risk_bias": "high",
            "confidence": "medium" if market_state else baseline_confidence,
            "affected_horizons": ["swing", "long"],
            "rationale": [
                "外需依存の候補に逆風がかかりやすい。",
                "安全資産需要で円高圧力が強まる可能性がある。",
            ],
        }

    return {
        "name": scenario,
        "description": f"Unknown scenario: {scenario}",
        "market_bias": "mixed",
        "fx_bias": fx_state or "neutral",
        "opportunity_bias": "unknown",
        "risk_bias": "moderate",
        "confidence": "low",
        "affected_horizons": ["daytrade", "swing", "long"],
        "rationale": ["The scenario is not in the built-in library."],
    }


def _normalize_scenarios(scenarios: Sequence[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for scenario in scenarios:
        text = _text(scenario).lower()
        if text and text not in normalized:
            normalized.append(text)
    return tuple(normalized or DEFAULT_SCENARIOS)


def _text(value: Any, default: str = "") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if value is None:
        return default
    return str(value)
