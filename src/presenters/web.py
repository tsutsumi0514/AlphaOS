"""HTML presenter for the AlphaOS briefing."""

from __future__ import annotations

from html import escape
from datetime import datetime
from typing import Any, Mapping

from fastapi.responses import HTMLResponse


def render_homepage(briefing: Mapping[str, Any]) -> HTMLResponse:
    return HTMLResponse(_render_page(briefing))


def _render_page(briefing: Mapping[str, Any]) -> str:
    headline = _text(briefing.get("headline"), "市場要約はまだ準備できていません。")
    market_state = _text(briefing.get("market_state"), "unknown")
    fx_state = _text(briefing.get("fx_state"), "unknown")
    confidence = _text(briefing.get("confidence"), "low")
    refresh_chip = _render_refresh_chip(briefing.get("market_refresh"))
    refresh_panel = _render_refresh_panel(briefing.get("market_refresh"))

    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AlphaOS トップページ</title>
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
    .refresh-panel {{
      margin: 0 28px;
      padding: 16px 18px;
      border-radius: 18px;
      border: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.9);
      display: grid;
      gap: 10px;
    }}
    .refresh-panel h2 {{
      margin: 0;
      font-size: 15px;
      color: var(--accent);
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    .refresh-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 10px;
    }}
    .refresh-item {{
      border-radius: 14px;
      border: 1px solid var(--border);
      padding: 12px 14px;
      background: #fffdf8;
    }}
    .refresh-label {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 4px;
    }}
    .refresh-value {{
      font-weight: 700;
    }}
    .refresh-form {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: end;
      margin-top: 6px;
    }}
    .refresh-form label {{
      display: grid;
      gap: 4px;
      color: var(--muted);
      font-size: 12px;
    }}
    .refresh-form input {{
      width: 160px;
      border-radius: 12px;
      border: 1px solid var(--border);
      padding: 10px 12px;
      font: inherit;
      background: white;
      color: var(--ink);
    }}
    .refresh-form button {{
      border: 1px solid rgba(138, 90, 0, 0.2);
      border-radius: 12px;
      padding: 10px 14px;
      background: linear-gradient(180deg, #fff8e8, #f4d7a3);
      color: #1e232b;
      font-weight: 700;
      cursor: pointer;
    }}
    .refresh-help {{
      margin: 0;
      color: var(--muted);
      font-size: 12px;
    }}
    .candidate-panel {{
      margin: 0 28px;
      padding: 18px;
      border-radius: 20px;
      border: 1px solid rgba(138, 90, 0, 0.18);
      background: linear-gradient(180deg, #fffdf8, #fff4dc);
      display: grid;
      gap: 10px;
    }}
    .candidate-panel h2 {{
      margin: 0;
      font-size: 16px;
      color: var(--accent);
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    .candidate-panel .candidate-title {{
      font-size: 22px;
      font-weight: 800;
      line-height: 1.2;
    }}
    .candidate-panel .candidate-subtitle {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }}
    .candidate-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }}
    .candidate-badge {{
      border-radius: 999px;
      border: 1px solid var(--border);
      background: white;
      padding: 6px 10px;
      font-size: 12px;
      color: var(--muted);
    }}
    .grid {{
      padding: 20px 28px 28px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
    }}
    .nav-grid {{
      padding: 24px 28px 4px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 12px;
    }}
    .nav-card {{
      display: grid;
      gap: 6px;
      padding: 14px 16px;
      border-radius: 18px;
      border: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.9);
      color: var(--ink);
      box-shadow: 0 10px 24px rgba(30, 35, 43, 0.06);
      min-height: 88px;
    }}
    .nav-card.primary {{
      background: linear-gradient(180deg, #ffffff, #fff4dc);
      border-color: rgba(138, 90, 0, 0.18);
    }}
    .nav-title {{
      font-weight: 700;
      font-size: 15px;
    }}
    .nav-desc {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
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
        <p class="eyebrow">AlphaOS トップページ</p>
        <h1>市場要約と銘柄提案を切り替える入口です。</h1>
        <p class="subhead">市場要約、候補銘柄、デイトレ、検証をまとめて開けます。JSON API は <code>/briefing</code> です。</p>
        <nav class="nav-grid" aria-label="ホームナビゲーション">
          <a class="nav-card primary" href="/briefing">
          <span class="nav-title">市場要約ホーム</span>
          <span class="nav-desc">根拠・リスク・自信度を確認</span>
        </a>
        <a class="nav-card" href="/candidates/view">
          <span class="nav-title">銘柄提案ホーム</span>
          <span class="nav-desc">買い候補と理由を確認</span>
        </a>
        <a class="nav-card" href="/daytrade-candidates/view">
          <span class="nav-title">デイトレホーム</span>
          <span class="nav-desc">短期候補と寄り付き判断を確認</span>
        </a>
        <a class="nav-card" href="/what-if">
          <span class="nav-title">仮説シミュレーター</span>
          <span class="nav-desc">仮定の市場影響を確認</span>
        </a>
        <a class="nav-card" href="/knowledge-graph/view">
          <span class="nav-title">知識グラフ</span>
          <span class="nav-desc">因果関係を俯瞰</span>
        </a>
        <a class="nav-card" href="/replay/compare">
          <span class="nav-title">Replay比較</span>
          <span class="nav-desc">当時判断と結果を比較</span>
        </a>
        <a class="nav-card" href="/validate/view">
          <span class="nav-title">検証</span>
          <span class="nav-desc">勝率・DD・PF を確認</span>
        </a>
        <a class="nav-card" href="/history/view">
          <span class="nav-title">履歴</span>
          <span class="nav-desc">ブリーフィング履歴を確認</span>
        </a>
      </nav>
      </header>
      <div class="hero">
        <div class="headline">{escape(headline)}</div>
        <div class="meta">
          <div class="chip"><strong>市場</strong> {escape(market_state)}</div>
          <div class="chip"><strong>為替</strong> {escape(fx_state)}</div>
          <div class="chip confidence"><strong>自信度</strong> {escape(confidence)}</div>
          <div class="chip"><strong>自動更新</strong> {escape(refresh_chip)}</div>
        </div>
      </div>
      {_render_candidate_preview(briefing.get("candidate_preview"), briefing.get("candidate_preview_message"), briefing.get("candidate_preview_summary"))}
      {refresh_panel}
      {_render_data_quality_section(briefing.get("data_health"), briefing.get("data_warnings"))}
      <div class="grid">
        { _render_decision_section(briefing.get("decision_ai")) }
        { _render_section("リスク警告", briefing.get("risk_alerts")) }
        { _render_section("主な変化", briefing.get("key_changes")) }
        { _render_section("理由", briefing.get("reasons")) }
        { _render_learning_section(briefing.get("learning_summary")) }
        { _render_evidence_section(briefing.get("evidence")) }
      </div>
      <footer>
        <span>最終判断は人間が行います。</span>
        <span><a href="/history/view">履歴を見る</a></span>
      </footer>
    </div>
  </main>
</body>
</html>"""


def _render_section(title: str, value: Any) -> str:
    items = _list_items(value)
    if not items:
        return f"<section><h2>{escape(title)}</h2><p class='empty'>なし</p></section>"

    return (
        f"<section><h2>{escape(title)}</h2><ul>"
        + "".join(f"<li>{escape(item)}</li>" for item in items)
        + "</ul></section>"
    )


def _render_evidence_section(value: Any) -> str:
    items = _list_items(value)
    if not items:
        return "<section><h2>根拠</h2><p class='empty'>なし</p></section>"

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

    return "<section><h2>根拠</h2><ul>" + "".join(rendered_items) + "</ul></section>"


def _render_decision_section(value: Any) -> str:
    if not isinstance(value, Mapping):
        return "<section><h2>意思決定AI</h2><p class='empty'>なし</p></section>"

    stance = _text(value.get("stance"), "balanced")
    summary = _text(value.get("summary"), "意思決定サマリはまだありません。")
    views = value.get("views")
    rendered_views: list[str] = []
    if isinstance(views, list):
        for view in views[:5]:
            if isinstance(view, Mapping):
                agent = _text(view.get("agent"), "Agent")
                view_stance = _text(view.get("stance"), "balanced")
                view_summary = _text(view.get("summary"), "")
                rendered_views.append(
                    f"<li><strong>{escape(agent)}</strong> ({escape(view_stance)}): {escape(view_summary)}</li>"
                )

    if not rendered_views:
        rendered_views.append("<li class='empty'>なし</li>")

    return (
        "<section><h2>意思決定AI</h2>"
        f"<p class='empty'>合意: {escape(stance)}. {escape(summary)}</p>"
        "<ul>"
        + "".join(rendered_views)
        + "</ul></section>"
    )


def _render_learning_section(value: Any) -> str:
    if not isinstance(value, Mapping):
        return "<section><h2>学習</h2><p class='empty'>なし</p></section>"

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
        rendered_notes = "<p class='empty'>なし</p>"

    accuracy_text = "n/a" if accuracy is None else f"{float(accuracy) * 100:.0f}%"
    return (
        "<section><h2>学習</h2>"
        f"<p class='empty'>状態: {escape(status)}, サンプル: {escape(str(sample_size))}, 精度: {escape(accuracy_text)}</p>"
        f"{rendered_notes}"
        "</section>"
    )


def _render_data_quality_section(data_health: Any, warnings: Any) -> str:
    status = "ok"
    available_inputs = 0
    interval = "1d"
    watchlist_count = 0
    strong_watchlist_count = 0
    weak_watchlist_count = 0
    top_watchlist_symbol = ""
    top_watchlist_change_pct = None
    news_query = ""
    warning_items: list[str] = []

    if isinstance(data_health, Mapping):
        status = _text(data_health.get("status"), "ok")
        available_inputs = int(data_health.get("available_inputs", 0) or 0)
        interval = _text(data_health.get("interval"), "1d")
        watchlist_count = int(data_health.get("watchlist_count", 0) or 0)
        strong_watchlist_count = int(data_health.get("strong_watchlist_count", 0) or 0)
        weak_watchlist_count = int(data_health.get("weak_watchlist_count", 0) or 0)
        top_watchlist_symbol = _text(data_health.get("top_watchlist_symbol"), "")
        top_watchlist_change_pct = data_health.get("top_watchlist_change_pct")
        news_query = _text(data_health.get("news_query"), "")
    if isinstance(warnings, list):
        warning_items = [item for item in (_text(warning, "") for warning in warnings) if item]

    if status == "ok" and not warning_items:
        if not any((watchlist_count, strong_watchlist_count, weak_watchlist_count, top_watchlist_symbol, news_query)):
            return ""

    warning_lines = "".join(f"<li>{escape(item)}</li>" for item in warning_items[:4]) or "<li class='empty'>なし</li>"
    diagnostics: list[str] = [
        f"<li><strong>watchlist_count</strong>: {escape(str(watchlist_count))}</li>",
        f"<li><strong>strong_watchlist_count</strong>: {escape(str(strong_watchlist_count))}</li>",
        f"<li><strong>weak_watchlist_count</strong>: {escape(str(weak_watchlist_count))}</li>",
    ]
    if top_watchlist_symbol:
        change_text = "n/a"
        if isinstance(top_watchlist_change_pct, (int, float)):
            change_text = f"{float(top_watchlist_change_pct):.2f}%"
        diagnostics.append(
            f"<li><strong>top_watchlist</strong>: {escape(top_watchlist_symbol)} ({escape(change_text)})</li>"
        )
    if news_query:
        diagnostics.append(f"<li><strong>news_query</strong>: {escape(news_query)}</li>")
    return (
        "<section>"
        "<h2>データ品質</h2>"
        f"<p class='empty'>状態: {escape(status)}, 利用可能入力: {escape(str(available_inputs))}, 間隔: {escape(interval)}</p>"
        f"<ul>{''.join(diagnostics)}</ul>"
        f"<ul>{warning_lines}</ul>"
        "</section>"
    )


def _list_items(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _render_refresh_chip(value: Any) -> str:
    if not isinstance(value, Mapping):
        return "待機中"

    enabled = bool(value.get("enabled", False))
    status = "稼働中" if enabled else "停止"
    refreshed_at = _format_refresh_time(value.get("refreshed_at"))
    interval_seconds = value.get("interval_seconds")
    if interval_seconds is None:
        return f"{status} / 最終更新 {refreshed_at}"
    return f"{status} / {interval_seconds}秒ごと / 最終更新 {refreshed_at}"


def _render_refresh_panel(value: Any) -> str:
    if not isinstance(value, Mapping):
        return ""

    enabled = "有効" if bool(value.get("enabled", False)) else "無効"
    interval_seconds = value.get("interval_seconds")
    interval_text = f"{interval_seconds}秒" if interval_seconds is not None else "未設定"
    refreshed_at = _format_refresh_time(value.get("refreshed_at"))
    status = _text(value.get("status"), "unknown")
    available_inputs = value.get("available_inputs", 0)
    warnings = _list_items(value.get("warnings"))
    warning_text = "なし" if not warnings else " / ".join(warnings[:2])

    return (
        "<section class='refresh-panel'>"
        "<h2>自動更新設定</h2>"
        "<div class='refresh-grid'>"
        f"<div class='refresh-item'><span class='refresh-label'>状態</span><span class='refresh-value'>{escape(enabled)}</span></div>"
        f"<div class='refresh-item'><span class='refresh-label'>間隔</span><span class='refresh-value'>{escape(interval_text)}</span></div>"
        f"<div class='refresh-item'><span class='refresh-label'>最終更新</span><span class='refresh-value'>{escape(refreshed_at)}</span></div>"
        f"<div class='refresh-item'><span class='refresh-label'>データ状態</span><span class='refresh-value'>{escape(status)}</span></div>"
        f"<div class='refresh-item'><span class='refresh-label'>利用可能入力</span><span class='refresh-value'>{escape(str(available_inputs))}</span></div>"
        f"<div class='refresh-item'><span class='refresh-label'>警告</span><span class='refresh-value'>{escape(warning_text)}</span></div>"
        "</div>"
        "<form class='refresh-form' method='get' action='/'>"
        "<label for='refresh-interval-seconds'>更新間隔（秒）"
        f"<input id='refresh-interval-seconds' name='refresh_interval_seconds' type='number' min='1' max='86400' value='{escape(str(interval_seconds or 60))}'>"
        "</label>"
        "<button type='submit'>変更</button>"
        "<p class='refresh-help'>変更後はすぐに新しい間隔で更新します。</p>"
        "</form>"
        "</section>"
    )


def _render_candidate_preview(candidate: Any, message: Any, summary: Any) -> str:
    if isinstance(candidate, Mapping):
        symbol = _text(candidate.get("symbol"), "unknown")
        name = _text(candidate.get("name"), "")
        horizon = _text(candidate.get("horizon"), "swing")
        score = _text(candidate.get("score"), "0")
        confidence = _text(candidate.get("confidence"), "low")
        timing = _text(candidate.get("entry_timing"), "wait")
        liquidity = _text(candidate.get("liquidity"), "unknown")
        reason = _text(candidate.get("candidate_reason"), "")
        entry_detail = _text(candidate.get("entry_detail"), "")
        return (
            "<section class='candidate-panel'>"
            "<h2>最有力候補</h2>"
            f"<div class='candidate-title'>{escape(symbol)} {escape(name)}</div>"
            f"<div class='candidate-subtitle'>{escape(reason or '候補の要約はまだありません。')}</div>"
            "<div class='candidate-meta'>"
            f"<span class='candidate-badge'>期間 {escape(horizon)}</span>"
            f"<span class='candidate-badge'>判断 {escape(timing)}</span>"
            f"<span class='candidate-badge'>確信度 {escape(confidence)}</span>"
            f"<span class='candidate-badge'>流動性 {escape(liquidity)}</span>"
            f"<span class='candidate-badge'>スコア {escape(score)}</span>"
            "</div>"
            f"<p class='candidate-subtitle'><strong>エントリー詳細:</strong> {escape(entry_detail)}</p>"
            f"<p class='candidate-subtitle'><strong>補足:</strong> {escape(_text(message, ''))}</p>"
            "<p class='candidate-subtitle'><a href='/candidates/view'>候補一覧を見る</a></p>"
            "</section>"
        )

    summary_line = "候補サマリはまだありません。"
    if isinstance(summary, Mapping):
        total = summary.get("total_candidates", 0)
        ranked = summary.get("ranked_count", 0)
        excluded = summary.get("excluded_count", 0)
        summary_line = f"候補 {total} 件 / 表示 {ranked} 件 / 除外 {excluded} 件"
    return (
        "<section class='candidate-panel'>"
        "<h2>最有力候補</h2>"
        "<div class='candidate-title'>まだ最有力候補はありません。</div>"
        f"<div class='candidate-subtitle'>{escape(summary_line)}</div>"
        f"<div class='candidate-subtitle'>{escape(_text(message, '候補は現在準備中です。'))}</div>"
        "<p class='candidate-subtitle'><a href='/candidates/view'>候補一覧を見る</a></p>"
        "</section>"
    )


def _format_refresh_time(value: Any) -> str:
    text = _text(value, "未更新")
    if text == "未更新":
        return text
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return text
    return parsed.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def _text(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if value is None:
        return default
    return str(value)
