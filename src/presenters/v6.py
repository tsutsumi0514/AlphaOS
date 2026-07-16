"""HTML presenters for AlphaOS V6 surfaces."""

from __future__ import annotations

from html import escape
from typing import Any, Mapping

from fastapi.responses import HTMLResponse


def render_what_if_page(report: Mapping[str, Any]) -> HTMLResponse:
    return HTMLResponse(_render_what_if_page(report))


def render_knowledge_graph_page(graph: Mapping[str, Any]) -> HTMLResponse:
    return HTMLResponse(_render_knowledge_graph_page(graph))


def render_replay_compare_page(compare: Mapping[str, Any]) -> HTMLResponse:
    return HTMLResponse(_render_replay_compare_page(compare))


def render_validation_page(report: Mapping[str, Any]) -> HTMLResponse:
    return HTMLResponse(_render_validation_page(report))


def render_candidates_page(report: Mapping[str, Any]) -> HTMLResponse:
    return HTMLResponse(_render_candidates_page(report))


def _render_what_if_page(report: Mapping[str, Any]) -> str:
    scenarios = report.get("scenarios", [])
    cards = []
    if isinstance(scenarios, list):
        for scenario in scenarios:
            if not isinstance(scenario, Mapping):
                continue
            cards.append(
                "<article class='card'>"
                f"<h2>{escape(_text(scenario.get('name'), 'scenario'))}</h2>"
                f"<p>{escape(_text(scenario.get('description'), ''))}</p>"
                f"<p><strong>Market</strong> {escape(_text(scenario.get('market_bias'), 'mixed'))}</p>"
                f"<p><strong>FX</strong> {escape(_text(scenario.get('fx_bias'), 'neutral'))}</p>"
                f"<p><strong>Risk</strong> {escape(_text(scenario.get('risk_bias'), 'moderate'))}</p>"
                f"<p><strong>Timing</strong> {escape(', '.join(_list_items(scenario.get('affected_horizons'))))}</p>"
                f"<ul>{''.join(f'<li>{escape(item)}</li>' for item in _list_items(scenario.get('rationale'))[:3])}</ul>"
                "</article>"
            )
    if not cards:
        cards.append("<p class='empty'>No what-if scenarios yet.</p>")
    return _wrap_page("AlphaOS What-if Simulator", "".join(cards))


def _render_knowledge_graph_page(graph: Mapping[str, Any]) -> str:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_cards = []
    if isinstance(nodes, list):
        for node in nodes:
            if not isinstance(node, Mapping):
                continue
            node_cards.append(
                "<article class='card'>"
                f"<h2>{escape(_text(node.get('label'), 'node'))}</h2>"
                f"<p>{escape(_text(node.get('kind'), ''))}</p>"
                f"<p>{escape(_text(node.get('summary'), ''))}</p>"
                "</article>"
            )
    edge_lines = []
    if isinstance(edges, list):
        for edge in edges:
            if not isinstance(edge, Mapping):
                continue
            edge_lines.append(
                f"<li>{escape(_text(edge.get('source'), ''))} → {escape(_text(edge.get('target'), ''))} "
                f"({escape(_text(edge.get('label'), ''))}, {escape(_text(edge.get('strength'), ''))})</li>"
            )
    if not node_cards:
        node_cards.append("<p class='empty'>No graph data yet.</p>")
    if not edge_lines:
        edge_lines.append("<li class='empty'>No edges yet.</li>")
    body = (
        "<div class='grid'>" + "".join(node_cards) + "</div>"
        "<section class='panel'><h2>Edges</h2><ul>" + "".join(edge_lines) + "</ul></section>"
    )
    return _wrap_page("AlphaOS Knowledge Graph", body)


def _render_replay_compare_page(compare: Mapping[str, Any]) -> str:
    current = compare.get("current", {})
    replay = compare.get("latest_replay", {})
    matches = compare.get("similar_cases", [])
    current_line = _render_kv_list(current)
    replay_line = _render_kv_list(replay)
    match_lines = []
    if isinstance(matches, list):
        for match in matches[:5]:
            if not isinstance(match, Mapping):
                continue
            match_lines.append(
                "<li>"
                f"<strong>{escape(_text(match.get('briefing_id'), 'unknown'))}</strong> "
                f"score {escape(str(match.get('score', 0.0)))} "
                f"{escape(', '.join(_list_items(match.get('match_reasons'))))}"
                "</li>"
            )
    if not match_lines:
        match_lines.append("<li class='empty'>No similar cases yet.</li>")
    body = (
        "<div class='grid'>"
        f"<section class='panel'><h2>Current</h2><ul>{current_line}</ul></section>"
        f"<section class='panel'><h2>Latest Replay</h2><ul>{replay_line}</ul></section>"
        "</div>"
        "<section class='panel'><h2>Similar Cases</h2><ul>"
        + "".join(match_lines)
        + "</ul></section>"
    )
    return _wrap_page("AlphaOS Replay Comparison", body)


def _render_validation_page(report: Mapping[str, Any]) -> str:
    horizons = report.get("by_horizon", {})
    cards = []
    if isinstance(horizons, Mapping):
        for horizon, payload in horizons.items():
            if not isinstance(payload, Mapping):
                continue
            summary = payload.get("summary", {})
            baseline = payload.get("baseline", {}).get("summary", {}) if isinstance(payload.get("baseline"), Mapping) else {}
            cards.append(
                "<article class='card'>"
                f"<h2>{escape(str(horizon))}</h2>"
                f"<p><strong>Trades</strong> {escape(str(summary.get('total', 0)))}</p>"
                f"<p><strong>Win rate</strong> {escape(_percent(summary.get('win_rate')))}</p>"
                f"<p><strong>Total return</strong> {escape(_percent(summary.get('total_return_pct')))}</p>"
                f"<p><strong>Profit factor</strong> {escape(_number(summary.get('profit_factor')))}</p>"
                f"<p><strong>Sharpe</strong> {escape(_number(summary.get('sharpe')))}</p>"
                f"<p><strong>Max DD</strong> {escape(_percent(summary.get('max_drawdown_pct')))}</p>"
                f"<p><strong>Baseline return</strong> {escape(_percent(baseline.get('total_return_pct')))}</p>"
                "</article>"
            )
    if not cards:
        cards.append("<p class='empty'>No validation data yet.</p>")

    walk_forward = report.get("walk_forward", {})
    wf_cards = []
    if isinstance(walk_forward, Mapping):
        wf_horizons = walk_forward.get("by_horizon", {})
        if isinstance(wf_horizons, Mapping):
            for horizon, payload in wf_horizons.items():
                if not isinstance(payload, Mapping):
                    continue
                summary = payload.get("summary", {})
                wf_cards.append(
                    "<li>"
                    f"<strong>{escape(str(horizon))}</strong>: "
                    f"trades {escape(str(summary.get('total', 0)))} / "
                    f"win {escape(_percent(summary.get('win_rate')))} / "
                    f"return {escape(_percent(summary.get('total_return_pct')))}"
                    "</li>"
                )
    if not wf_cards:
        wf_cards.append("<li class='empty'>No walk-forward data yet.</li>")

    body = (
        f"<p class='subhead'>Interval: {escape(_text(report.get('interval'), '1d'))}. "
        f"Cost: {escape(_percent(report.get('transaction_cost_pct')))}. "
        f"Sample size: {escape(str(report.get('sample_size', 0)))}.</p>"
        "<div class='grid'>" + "".join(cards) + "</div>"
        "<section class='panel'><h2>Walk-forward</h2><ul>" + "".join(wf_cards) + "</ul></section>"
    )
    return _wrap_page("AlphaOS Opportunity Validation", body)


def _render_candidates_page(report: Mapping[str, Any]) -> str:
    candidates = report.get("candidates", [])
    excluded = report.get("excluded_candidates", [])
    personal_profile = report.get("personal_profile", {})
    personal_notes = report.get("personal_notes", [])
    top_candidate = report.get("top_candidate", {})
    cards = []
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                continue
            evidence_lines = []
            for item in _mapping_items(candidate.get("evidence"))[:4]:
                evidence_lines.append(
                    f"<li>{escape(_text(item.get('label'), 'evidence'))}: "
                    f"{escape(_text(item.get('value'), ''))}</li>"
                )
            if not evidence_lines:
                evidence_lines.append("<li class='empty'>No evidence yet.</li>")
            cards.append(
                "<article class='card'>"
                f"<h2>#{escape(str(candidate.get('rank', '')))} {escape(_text(candidate.get('symbol'), 'candidate'))}</h2>"
                f"<p><strong>Name</strong> {escape(_text(candidate.get('name'), ''))}</p>"
                f"<p><strong>Horizon</strong> {escape(_text(candidate.get('horizon'), ''))}</p>"
                f"<p><strong>Score</strong> {escape(_number(candidate.get('score')))}</p>"
                f"<p><strong>Confidence</strong> {escape(_text(candidate.get('confidence'), ''))}</p>"
                f"<p><strong>Entry timing</strong> {escape(_text(candidate.get('entry_timing'), ''))}</p>"
                f"<p><strong>Entry detail</strong> {escape(_text(candidate.get('entry_detail'), ''))}</p>"
                f"<p><strong>Entry reason</strong> {escape(_text(candidate.get('entry_reason'), ''))}</p>"
                f"<p><strong>Status</strong> {escape(_text(candidate.get('status'), ''))}</p>"
                f"<p><strong>Liquidity</strong> {escape(_text(candidate.get('liquidity'), ''))}</p>"
                f"<p><strong>Note</strong> {escape(_text(candidate.get('note'), ''))}</p>"
                f"<p><strong>Sector</strong> {escape(_text(candidate.get('sector'), ''))}</p>"
                f"<p><strong>Sector strength</strong> {escape(_text(candidate.get('sector_strength'), ''))}</p>"
                f"<div><strong>Reasons</strong><ul>{''.join(f'<li>{escape(item)}</li>' for item in _list_items(candidate.get('reasons'))[:4])}</ul></div>"
                f"<div><strong>Risk alerts</strong><ul>{''.join(f'<li>{escape(item)}</li>' for item in _list_items(candidate.get('risk_alerts'))[:4])}</ul></div>"
                f"<div><strong>Counter evidence</strong><ul>{''.join(f'<li>{escape(item)}</li>' for item in _list_items(candidate.get('counter_evidence'))[:4])}</ul></div>"
                f"<div><strong>Evidence</strong><ul>{''.join(evidence_lines)}</ul></div>"
                "</article>"
            )
    if not cards:
        cards.append("<p class='empty'>No candidates yet.</p>")

    excluded_lines = []
    if isinstance(excluded, list):
        for item in excluded[:8]:
            if not isinstance(item, Mapping):
                continue
            tags = ", ".join(_list_items(item.get("tags")))
            tag_markup = ""
            if tags:
                tag_markup = f" <span class='empty'>[{escape(tags)}]</span>"
            excluded_lines.append(
                "<li>"
                f"<strong>{escape(_text(item.get('symbol'), 'unknown'))}</strong> "
                f"{escape(_text(item.get('reason'), ''))}"
                f"{tag_markup}"
                "</li>"
            )
    if not excluded_lines:
        excluded_lines.append("<li class='empty'>No excluded candidates yet.</li>")

    summary = report.get("opportunity_summary", {})
    summary_line = _render_kv_list(summary)
    breakdown = summary.get("exclusion_breakdown", {}) if isinstance(summary, Mapping) else {}
    breakdown_line = _render_kv_list(breakdown)
    top_candidate_block = _render_top_candidate_block(top_candidate)
    profile_line = _render_personal_profile_list(personal_profile)
    notes_line = "".join(f"<li>{escape(item)}</li>" for item in _list_items(personal_notes))
    if not notes_line:
        notes_line = "<li class='empty'>No personal notes yet.</li>"
    body = (
        f"<p class='subhead'>Horizon: {escape(_text(report.get('horizon'), 'swing'))}. "
        f"Count: {escape(str(report.get('count', 0)))}. "
        f"Rejected: {escape(str(report.get('rejected_count', 0)))}. "
        f"Strategy: {escape(_text(report.get('strategy_mode'), _text(report.get('horizon'), 'swing')))}. "
        f"Mode: {escape(_text(report.get('automation_mode'), 'advisory_only'))}.</p>"
        f"{top_candidate_block}"
        f"<section class='panel'><h2>Personal Context</h2><ul>{profile_line}</ul><ul>{notes_line}</ul></section>"
        f"<section class='panel'><h2>Opportunity Summary</h2><ul>{summary_line}</ul></section>"
        f"<section class='panel'><h2>Exclusion Breakdown</h2><ul>{breakdown_line}</ul></section>"
        "<div class='grid'>" + "".join(cards) + "</div>"
        "<section class='panel'><h2>Excluded Candidates</h2><ul>" + "".join(excluded_lines) + "</ul></section>"
    )
    return _wrap_page("AlphaOS Candidates", body)


def _wrap_page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    body {{ margin: 0; font-family: "Segoe UI", "Hiragino Sans", "Yu Gothic", sans-serif; background: #f5f3ef; color: #20262e; }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 28px 18px 40px; }}
    .shell {{ background: white; border: 1px solid rgba(32,38,46,.12); border-radius: 24px; box-shadow: 0 18px 50px rgba(32,38,46,.08); padding: 24px; }}
    h1 {{ margin: 0 0 18px; font-size: clamp(28px, 4vw, 42px); }}
    .grid {{ display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }}
    .card, .panel {{ border: 1px solid rgba(32,38,46,.12); border-radius: 18px; padding: 16px; background: #fffdf8; }}
    h2 {{ margin: 0 0 10px; font-size: 16px; color: #845a00; }}
    ul {{ margin: 0; padding-left: 20px; display: grid; gap: 6px; }}
    .empty {{ color: #68707b; }}
  </style>
</head>
<body>
  <main>
    <div class="shell">
      <h1>{escape(title)}</h1>
      {body}
    </div>
  </main>
</body>
</html>"""


def _render_kv_list(value: Mapping[str, Any] | Any) -> str:
    if not isinstance(value, Mapping):
        return "<li class='empty'>None</li>"
    items: list[str] = []
    for key in ("market_state", "fx_state", "confidence", "horizon", "win_rate", "profit_factor", "sharpe"):
        item = value.get(key)
        if item is None:
            continue
        items.append(f"<li><strong>{escape(key)}</strong>: {escape(str(item))}</li>")
    if isinstance(value, Mapping):
        detail_breakdown = value.get("entry_detail_breakdown")
        if isinstance(detail_breakdown, Mapping):
            for key, item in detail_breakdown.items():
                items.append(f"<li><strong>{escape(str(key))}</strong>: {escape(str(item))}</li>")
    if not items:
        items.append("<li class='empty'>None</li>")
    return "".join(items)


def _render_personal_profile_list(value: Mapping[str, Any] | Any) -> str:
    if not isinstance(value, Mapping):
        return "<li class='empty'>None</li>"
    items: list[str] = []
    for key in ("holdings", "investment_period", "risk_tolerance", "style", "interested_markets"):
        item = value.get(key)
        if item is None:
            continue
        if isinstance(item, list):
            item = ", ".join(str(entry) for entry in item)
        items.append(f"<li><strong>{escape(key)}</strong>: {escape(str(item))}</li>")
    if not items:
        items.append("<li class='empty'>None</li>")
    return "".join(items)


def _render_top_candidate_block(value: Mapping[str, Any] | Any) -> str:
    if not isinstance(value, Mapping):
        return "<section class='panel'><h2>Top Candidate</h2><p class='empty'>No top candidate yet.</p></section>"

    counter_evidence = "".join(
        f"<li>{escape(item)}</li>" for item in _list_items(value.get("counter_evidence"))[:4]
    )
    if not counter_evidence:
        counter_evidence = "<li class='empty'>No counter evidence yet.</li>"

    evidence_lines = []
    for item in _mapping_items(value.get("evidence"))[:4]:
        evidence_lines.append(
            f"<li>{escape(_text(item.get('label'), 'evidence'))}: {escape(_text(item.get('value'), ''))}</li>"
        )
    if not evidence_lines:
        evidence_lines.append("<li class='empty'>No evidence yet.</li>")

    why_now = _build_why_now_line(value)

    return (
        "<section class='panel'>"
        "<h2>Top Candidate</h2>"
        "<p><strong>Mode</strong> advisory_only</p>"
        f"<p><strong>Strategy</strong> {escape(_text(value.get('horizon'), 'swing'))}</p>"
        f"<p><strong>{escape(_text(value.get('symbol'), 'unknown'))}</strong> "
        f"{escape(_text(value.get('name'), ''))}</p>"
        f"<p><strong>Why now</strong> {escape(why_now)}</p>"
        f"<p><strong>Entry detail</strong> {escape(_text(value.get('entry_detail'), ''))}</p>"
        f"<p><strong>Entry reason</strong> {escape(_text(value.get('entry_reason'), ''))}</p>"
        f"<p><strong>Score</strong> {escape(_number(value.get('score')))}</p>"
        f"<p><strong>Confidence</strong> {escape(_text(value.get('confidence'), ''))}</p>"
        f"<p><strong>Liquidity</strong> {escape(_text(value.get('liquidity'), ''))}</p>"
        f"<div><strong>Counter evidence</strong><ul>{counter_evidence}</ul></div>"
        f"<div><strong>Evidence</strong><ul>{''.join(evidence_lines)}</ul></div>"
        "</section>"
    )


def _build_why_now_line(value: Mapping[str, Any]) -> str:
    detail = _text(value.get("entry_detail"), "")
    reason = _text(value.get("entry_reason"), "")
    parts = [part for part in (detail, reason) if part]
    if parts:
        return " / ".join(parts)
    return "No short summary yet."


def _mapping_items(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    items: list[Mapping[str, Any]] = []
    for item in value:
        if isinstance(item, Mapping):
            items.append(item)
    return items


def _percent(value: Any) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except Exception:
        return "n/a"


def _number(value: Any) -> str:
    try:
        return f"{float(value):.4f}"
    except Exception:
        return "n/a"


def _list_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in (str(v).strip() for v in value) if item]


def _text(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if value is None:
        return default
    return str(value)
