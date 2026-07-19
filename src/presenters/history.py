"""HTML history presenter for AlphaOS briefing snapshots."""

from __future__ import annotations

from html import escape
from typing import Any, Mapping

from fastapi.responses import HTMLResponse


def render_history_page(
    records: list[dict[str, Any]],
    learning_summary: Mapping[str, Any] | None = None,
) -> HTMLResponse:
    return HTMLResponse(_render_page(records, learning_summary))


def _render_page(
    records: list[dict[str, Any]],
    learning_summary: Mapping[str, Any] | None,
) -> str:
    total = len(records)
    status = _text(learning_summary.get("status"), "insufficient") if isinstance(learning_summary, Mapping) else "insufficient"
    sample_size = learning_summary.get("sample_size", 0) if isinstance(learning_summary, Mapping) else 0
    accuracy = learning_summary.get("accuracy") if isinstance(learning_summary, Mapping) else None
    accuracy_text = "n/a" if accuracy is None else f"{float(accuracy) * 100:.0f}%"

    recent_records = list(reversed(records[-10:]))
    cards = "".join(_render_record_card(record) for record in recent_records)
    if not cards:
        cards = "<p class='empty'>まだ履歴はありません。</p>"

    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AlphaOS ブリーフィング履歴</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #eef3f8;
      --panel: #ffffff;
      --ink: #1f2a37;
      --muted: #5f6b7a;
      --accent: #2457d6;
      --accent-soft: rgba(36, 87, 214, 0.12);
      --border: rgba(31, 42, 55, 0.12);
      --shadow: 0 20px 60px rgba(31, 42, 55, 0.12);
    }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "Hiragino Sans", "Yu Gothic", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top right, rgba(36, 87, 214, 0.16), transparent 30%),
        linear-gradient(180deg, #f8fbff 0%, var(--bg) 100%);
      min-height: 100vh;
    }}
    main {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    .shell {{
      background: rgba(255, 255, 255, 0.92);
      border: 1px solid var(--border);
      border-radius: 28px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }}
    header {{
      padding: 28px 28px 0;
    }}
    .topbar {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
    }}
    .home-link {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: #fff;
      color: var(--ink);
      text-decoration: none;
      font-weight: 700;
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
      font-size: clamp(28px, 4vw, 44px);
      line-height: 1.05;
    }}
    .subhead {{
      margin: 12px 0 0;
      color: var(--muted);
      max-width: 72ch;
    }}
    .summary {{
      padding: 22px 28px 8px;
      display: grid;
      gap: 12px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
    }}
    .card {{
      border: 1px solid var(--border);
      border-radius: 18px;
      background: var(--panel);
      padding: 16px;
    }}
    .card h2 {{
      margin: 0 0 8px;
      font-size: 13px;
      color: var(--accent);
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .card .value {{
      font-size: 28px;
      font-weight: 700;
      line-height: 1.1;
    }}
    .record-list {{
      padding: 12px 28px 28px;
      display: grid;
      gap: 14px;
    }}
    .record {{
      border: 1px solid var(--border);
      border-radius: 20px;
      background: linear-gradient(180deg, #fff 0%, #f9fbff 100%);
      padding: 18px;
    }}
    .record-head {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 12px;
      align-items: baseline;
    }}
    .record h2 {{
      margin: 0;
      font-size: 18px;
    }}
    .meta {{
      color: var(--muted);
      font-size: 13px;
      margin-top: 6px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }}
    .chips {{
      margin-top: 12px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .chip {{
      border-radius: 999px;
      border: 1px solid var(--border);
      background: var(--accent-soft);
      color: var(--ink);
      padding: 6px 12px;
      font-size: 13px;
    }}
    .section {{
      margin-top: 14px;
    }}
    .section h3 {{
      margin: 0 0 8px;
      font-size: 13px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: var(--accent);
    }}
    ul {{
      margin: 0;
      padding-left: 20px;
      display: grid;
      gap: 6px;
    }}
    .empty {{
      color: var(--muted);
      margin: 0;
    }}
    footer {{
      padding: 0 28px 28px;
      color: var(--muted);
      font-size: 13px;
      display: flex;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }}
    a {{
      color: var(--accent);
      text-decoration: none;
    }}
    @media (max-width: 640px) {{
      header, .summary, .record-list, footer {{
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
        <div class="topbar">
          <div>
            <p class="eyebrow">AlphaOS 履歴</p>
            <h1>最近のブリーフィングを一覧できます。</h1>
          </div>
          <a class="home-link" href="/">ホームへ戻る</a>
        </div>
        <p class="subhead">履歴は簡潔に保ちつつ、学習と検証に使えるブリーフィング内容を残します。</p>
      </header>
      <div class="summary">
        <div class="grid">
          <div class="card"><h2>件数</h2><div class="value">{escape(str(total))}</div></div>
          <div class="card"><h2>学習</h2><div class="value">{escape(status)}</div></div>
          <div class="card"><h2>サンプル</h2><div class="value">{escape(str(sample_size))}</div></div>
          <div class="card"><h2>精度</h2><div class="value">{escape(accuracy_text)}</div></div>
        </div>
      </div>
      <div class="record-list">
        {cards}
      </div>
      <footer>
        <span>最新10件を新しい順で表示しています。</span>
      </footer>
    </div>
  </main>
</body>
</html>"""


def _render_record_card(record: Mapping[str, Any]) -> str:
    recorded_at = _text(record.get("recorded_at"), "unknown")
    briefing_id = _text(record.get("briefing_id"), "unknown")
    briefing = record.get("briefing")
    briefing_map = briefing if isinstance(briefing, Mapping) else {}

    headline = _text(briefing_map.get("headline"), "市場要約はまだ準備できていません。")
    market_state = _text(briefing_map.get("market_state"), "unknown")
    fx_state = _text(briefing_map.get("fx_state"), "unknown")
    confidence = _text(briefing_map.get("confidence"), "low")

    risk_alerts = _list_items(briefing_map.get("risk_alerts"))
    key_changes = _list_items(briefing_map.get("key_changes"))
    reasons = _list_items(briefing_map.get("reasons"))
    data_health = briefing_map.get("data_health")
    data_warnings = _list_items(briefing_map.get("data_warnings"))

    return f"""
      <article class="record">
        <div class="record-head">
          <div>
            <h2>{escape(headline)}</h2>
            <div class="meta">
              <span>{escape(recorded_at)}</span>
              <span>Briefing {escape(briefing_id)}</span>
            </div>
          </div>
          <div class="chips">
            <span class="chip">市場: {escape(market_state)}</span>
            <span class="chip">為替: {escape(fx_state)}</span>
            <span class="chip">自信度: {escape(confidence)}</span>
          </div>
        </div>
        {_render_data_section(data_health, data_warnings)}
        {_render_item_section("リスク警告", risk_alerts)}
        {_render_item_section("主な変化", key_changes)}
        {_render_item_section("理由", reasons)}
      </article>
    """


def _render_item_section(title: str, value: Any) -> str:
    items = _list_items(value)
    if not items:
        return f"<div class='section'><h3>{escape(title)}</h3><p class='empty'>なし</p></div>"

    return (
        f"<div class='section'><h3>{escape(title)}</h3><ul>"
        + "".join(f"<li>{escape(_text(item, ''))}</li>" for item in items[:3])
        + "</ul></div>"
    )


def _render_data_section(data_health: Any, data_warnings: Any) -> str:
    if not isinstance(data_health, Mapping) and not data_warnings:
        return ""

    status = _text(data_health.get("status"), "unknown") if isinstance(data_health, Mapping) else "unknown"
    available_inputs = data_health.get("available_inputs", 0) if isinstance(data_health, Mapping) else 0
    interval = _text(data_health.get("interval"), "1d") if isinstance(data_health, Mapping) else "1d"
    warnings = _list_items(data_warnings)
    if status == "ok" and not warnings:
        return ""
    warning_markup = "".join(f"<li>{escape(_text(item, ''))}</li>" for item in warnings[:3]) or "<li class='empty'>なし</li>"
    return (
        "<div class='section'>"
        "<h3>データ品質</h3>"
        f"<p class='empty'>状態: {escape(status)}, 利用可能: {escape(str(available_inputs))}, 間隔: {escape(interval)}</p>"
        f"<ul>{warning_markup}</ul>"
        "</div>"
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
