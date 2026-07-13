"""HTML presenter for the AlphaOS briefing."""

from __future__ import annotations

from html import escape
from typing import Any, Mapping

from fastapi.responses import HTMLResponse


def render_homepage(briefing: Mapping[str, Any]) -> HTMLResponse:
    return HTMLResponse(_render_page(briefing))


def _render_page(briefing: Mapping[str, Any]) -> str:
    headline = _text(briefing.get("headline"), "Market overview is not ready yet.")
    market_state = _text(briefing.get("market_state"), "unknown")
    fx_state = _text(briefing.get("fx_state"), "unknown")
    confidence = _text(briefing.get("confidence"), "low")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AlphaOS Briefing</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4efe6;
      --panel: #fffaf2;
      --ink: #1e232b;
      --muted: #616b79;
      --accent: #8a5a00;
      --accent-soft: #f4d7a3;
      --border: rgba(30, 35, 43, 0.12);
      --shadow: 0 20px 60px rgba(30, 35, 43, 0.12);
    }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "Hiragino Sans", "Yu Gothic", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(244, 215, 163, 0.65), transparent 35%),
        radial-gradient(circle at top right, rgba(138, 90, 0, 0.08), transparent 30%),
        linear-gradient(180deg, #fbf7f0 0%, var(--bg) 100%);
      min-height: 100vh;
    }}
    main {{
      max-width: 1080px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    .shell {{
      background: rgba(255, 250, 242, 0.88);
      border: 1px solid var(--border);
      border-radius: 28px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }}
    header {{
      padding: 28px 28px 0;
    }}
    .eyebrow {{
      text-transform: uppercase;
      letter-spacing: 0.2em;
      font-size: 12px;
      color: var(--accent);
      margin: 0 0 10px;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(28px, 4vw, 48px);
      line-height: 1.05;
    }}
    .subhead {{
      margin: 12px 0 0;
      color: var(--muted);
      max-width: 70ch;
    }}
    .hero {{
      padding: 24px 28px 8px;
      display: grid;
      gap: 16px;
    }}
    .headline {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 22px;
      padding: 22px;
      font-size: clamp(22px, 3vw, 34px);
      line-height: 1.2;
      font-weight: 700;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }}
    .chip {{
      border-radius: 999px;
      border: 1px solid var(--border);
      background: white;
      padding: 8px 14px;
      font-size: 14px;
      color: var(--muted);
    }}
    .chip strong {{
      color: var(--ink);
    }}
    .grid {{
      padding: 20px 28px 28px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
    }}
    section {{
      background: rgba(255, 255, 255, 0.72);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 18px;
      min-height: 140px;
    }}
    section h2 {{
      margin: 0 0 12px;
      font-size: 16px;
      color: var(--accent);
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    ul {{
      margin: 0;
      padding-left: 20px;
      display: grid;
      gap: 8px;
    }}
    li {{
      line-height: 1.45;
    }}
    .empty {{
      color: var(--muted);
      margin: 0;
    }}
    .confidence {{
      font-weight: 700;
    }}
    footer {{
      padding: 0 28px 28px;
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 640px) {{
      header, .hero, .grid, footer {{
        padding-left: 18px;
        padding-right: 18px;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <div class="shell">
      <header>
        <p class="eyebrow">AlphaOS Morning Briefing</p>
        <h1>Fast market understanding for individual investors.</h1>
        <p class="subhead">Compact briefing view with evidence, reasons, confidence, and risk-first warnings. The JSON API remains available at <code>/briefing</code>.</p>
      </header>
      <div class="hero">
        <div class="headline">{escape(headline)}</div>
        <div class="meta">
          <div class="chip"><strong>Market</strong> {escape(market_state)}</div>
          <div class="chip"><strong>FX</strong> {escape(fx_state)}</div>
          <div class="chip confidence"><strong>Confidence</strong> {escape(confidence)}</div>
        </div>
      </div>
      <div class="grid">
        { _render_section("Risk Alerts", briefing.get("risk_alerts")) }
        { _render_section("Key Changes", briefing.get("key_changes")) }
        { _render_section("Reasons", briefing.get("reasons")) }
        { _render_learning_section(briefing.get("learning_summary")) }
        { _render_evidence_section(briefing.get("evidence")) }
      </div>
      <footer>Final decision remains with the human.</footer>
    </div>
  </main>
</body>
</html>"""


def _render_section(title: str, value: Any) -> str:
    items = _list_items(value)
    if not items:
        return f"<section><h2>{escape(title)}</h2><p class='empty'>None</p></section>"

    return (
        f"<section><h2>{escape(title)}</h2><ul>"
        + "".join(f"<li>{escape(item)}</li>" for item in items)
        + "</ul></section>"
    )


def _render_evidence_section(value: Any) -> str:
    items = _list_items(value)
    if not items:
        return "<section><h2>Evidence</h2><p class='empty'>None</p></section>"

    rendered_items: list[str] = []
    for item in items:
        if isinstance(item, Mapping):
            source = _text(item.get("source"), "unknown")
            label = _text(item.get("label"), "item")
            value_text = _text(item.get("value"), "")
            note = item.get("note")
            line = f"<strong>{escape(source)}</strong> {escape(label)}"
            if value_text:
                line += f": {escape(value_text)}"
            if isinstance(note, str) and note.strip():
                line += f" <span class='empty'>({escape(note.strip())})</span>"
            rendered_items.append(f"<li>{line}</li>")
        else:
            rendered_items.append(f"<li>{escape(str(item))}</li>")

    return "<section><h2>Evidence</h2><ul>" + "".join(rendered_items) + "</ul></section>"


def _render_learning_section(value: Any) -> str:
    if not isinstance(value, Mapping):
        return "<section><h2>Learning</h2><p class='empty'>None</p></section>"

    status = _text(value.get("status"), "insufficient")
    sample_size = value.get("sample_size", 0)
    accuracy = value.get("accuracy")
    notes = _list_items(value.get("notes"))

    rendered_notes = ""
    if notes:
        rendered_notes = "<ul>" + "".join(
            f"<li>{escape(_text(note, ''))}</li>" for note in notes
        ) + "</ul>"
    else:
        rendered_notes = "<p class='empty'>None</p>"

    accuracy_text = "n/a" if accuracy is None else f"{float(accuracy) * 100:.0f}%"
    return (
        "<section><h2>Learning</h2>"
        f"<p class='empty'>status: {escape(status)}, sample: {escape(str(sample_size))}, accuracy: {escape(accuracy_text)}</p>"
        f"{rendered_notes}"
        "</section>"
    )


def _list_items(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _text(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if value is None:
        return default
    return str(value)
