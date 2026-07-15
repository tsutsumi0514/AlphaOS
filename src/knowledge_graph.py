"""Lightweight knowledge graph helpers for AlphaOS."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypedDict

from .opportunity import evaluate_candidate_pool
from .simulation.what_if import run_what_if_simulation


class GraphNode(TypedDict):
    id: str
    label: str
    kind: str
    summary: str


class GraphEdge(TypedDict):
    source: str
    target: str
    label: str
    strength: str


def build_knowledge_graph(
    briefing: Mapping[str, Any],
    *,
    scenarios: Sequence[str] | None = None,
    horizon: str = "swing",
) -> dict[str, Any]:
    scenario_report = run_what_if_simulation(briefing, scenarios or ())
    candidate_pool = evaluate_candidate_pool(briefing, horizon=horizon, limit=3)
    top_candidate = candidate_pool["candidates"][0] if candidate_pool["candidates"] else None

    nodes: list[GraphNode] = [
        {
            "id": "market",
            "label": _text(briefing.get("market_state"), "unknown"),
            "kind": "market",
            "summary": "Current broad market tone.",
        },
        {
            "id": "fx",
            "label": _text(briefing.get("fx_state"), "unknown"),
            "kind": "fx",
            "summary": "Current FX tone.",
        },
    ]
    edges: list[GraphEdge] = [
        {
            "source": "market",
            "target": "fx",
            "label": "macro flow",
            "strength": "medium",
        }
    ]

    decision_ai = briefing.get("decision_ai")
    if isinstance(decision_ai, Mapping):
        nodes.append(
            {
                "id": "decision",
                "label": _text(decision_ai.get("agent"), "Decision AI"),
                "kind": "decision",
                "summary": _text(decision_ai.get("reason"), "Decision support summary."),
            }
        )
        edges.append(
            {
                "source": "market",
                "target": "decision",
                "label": "evidence",
                "strength": "high",
            }
        )

    if top_candidate is not None:
        nodes.append(
            {
                "id": f"candidate:{top_candidate['symbol']}",
                "label": top_candidate["symbol"],
                "kind": "candidate",
                "summary": top_candidate.get("entry_reason", "Candidate entry summary."),
            }
        )
        edges.append(
            {
                "source": "decision",
                "target": f"candidate:{top_candidate['symbol']}",
                "label": "ranked candidate",
                "strength": "high" if top_candidate.get("confidence") == "high" else "medium",
            }
        )

    for scenario in scenario_report["scenarios"]:
        scenario_id = f"scenario:{scenario['name']}"
        nodes.append(
            {
                "id": scenario_id,
                "label": scenario["name"],
                "kind": "scenario",
                "summary": scenario["description"],
            }
        )
        edges.append(
            {
                "source": "market",
                "target": scenario_id,
                "label": scenario["opportunity_bias"],
                "strength": "medium" if scenario["opportunity_bias"] != "unknown" else "low",
            }
        )

    return {
        "nodes": nodes,
        "edges": edges,
        "top_candidate": top_candidate,
        "scenario_report": scenario_report,
    }


def _text(value: Any, default: str = "") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if value is None:
        return default
    return str(value)
