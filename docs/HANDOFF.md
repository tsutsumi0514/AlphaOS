# AlphaOS Handoff

## Project Purpose
AlphaOS is an AI-assisted investment support operating system for individual investors.
Its goal is not to predict markets perfectly or automate trading.
Its goal is to help a human understand the market quickly, see evidence clearly, and make safer decisions.

## Core Design Philosophy
- Reduce information overload.
- Help the user understand the market in about 5 seconds.
- Show reasons and confidence.
- Prioritize risk management over profit chasing.
- Keep the final decision with the human.
- Build a design that can survive future model and UI changes.

## Current Architecture

### Data Collection Layer
Current collectors fetch external inputs:
- `src/fx.py` for USD/JPY
- `src/market.py` for Nikkei change
- `src/watchlist.py` for watched symbols
- `src/news.py` for latest market news
- `src/collectors/briefing_inputs.py` for briefing input orchestration

### Cache Layer
- `src/cache.py` provides a short TTL cache to avoid repeated fetches.

### Evidence Layer
- `src/evidence.py` defines structured evidence objects.
- Evidence is used to preserve the proof behind a signal instead of flattening everything into labels.

### Analysis Layer
- `src/analyzers/briefing_signals.py` derives risk alerts, reasons, evidence, and confidence.
- This keeps `src/briefing.py` smaller while preserving the v1 output contract.

### Agent Layer
- `src/agents/chairman_ai.py` coordinates the top-level briefing assembly.
- `src/agents/risk_ai.py` owns the risk review step.

### Storage and Learning Layer
- `src/storage/briefing_history.py` stores briefing snapshots in JSONL under the user's home directory by default.
- `src/storage/outcome_history.py` stores realized outcomes in JSONL under the user's home directory by default.
- `src/learning/backtest.py` scores briefings against later outcomes and aggregates results.
- `src/learning/feedback.py` summarizes recent learning performance for the next briefing.

### Briefing Orchestration Layer
- `src/briefing.py` merges signals into a compact briefing payload.
- It derives:
  - `headline`
  - `market_state`
  - `fx_state`
  - `watchlist_status`
  - `news_item`
  - `risk_alerts`
  - `key_changes`
  - `reasons`
  - `confidence`
  - `evidence`

### API Layer
- `src/app.py` exposes the `/briefing` endpoint.
- `src/app.py` also exposes `/` as the simple Web presenter.
- `src/app.py` also exposes `/history` and `/backtest` for learning loop review.
- `src/app.py` also exposes `/outcome` and `/learning`.
- The endpoint can accept manual overrides such as `usd_jpy`, `market_change_pct`, and watchlist symbols.
- If values are omitted, the app auto-fetches them.

### Execution Layer
- `src/main.py` is the local launcher for `python -m src.main`.

### Validation Layer
- `tests/` contains unit and endpoint tests.
- `python -m pytest` is the canonical verification command.

### Expansion Points
- `src/agents/`
- `src/collectors/`
- `src/analyzers/`
- `src/presenters/`

These folders exist so the current v1 design can grow into multi-agent and multi-presenter architecture without breaking the public API.

## Implemented Features
- FastAPI `/briefing` endpoint.
- Simple HTML `/` presenter.
- `/history` endpoint for stored briefing snapshots.
- `/backtest` endpoint for scoring a briefing set against outcomes.
- `/outcome` endpoint for recording realized outcomes.
- `/learning` endpoint for reading the current learning summary.
- Briefing input collector under `src/collectors/briefing_inputs.py`.
- Top-level coordinator under `src/agents/chairman_ai.py`.
- Risk review step under `src/agents/risk_ai.py`.
- JSONL history storage under `src/storage/briefing_history.py`.
- JSONL outcome storage under `src/storage/outcome_history.py`.
- Minimal backtesting helpers under `src/learning/backtest.py`.
- Learning summary helpers under `src/learning/feedback.py`.
- Automatic USD/JPY fetching.
- Automatic Nikkei change fetching.
- Automatic watchlist fetching for multiple symbols.
- Automatic latest market news fetching.
- `market_state` derivation.
- `fx_state` derivation.
- `watchlist_status` derivation.
- `risk_alerts` generation.
- `key_changes` generation.
- `reasons` generation.
- `confidence` estimation.
- `headline` generation.
- Structured `evidence` generation.
- TTL cache for fetched market inputs.
- Test suite for briefing, app behavior, cache, watchlist, and launcher behavior.

## Not Yet Implemented
- LINE integration.
- Voice or wearable presenters.
- User-specific rule settings.
- Multi-user support.
- Real `ChairmanAI`, `RiskAI`, `NewsAI`, or `MacroAI` modules.

## Important Decisions
- The project is a decision-support OS, not an auto-trading system.
- `briefing.py` is intentionally small in v1, but it now preserves structured evidence.
- `src/analyzers/briefing_signals.py` holds the first dedicated analysis helpers.
- `src/collectors/briefing_inputs.py` and `src/agents/chairman_ai.py` establish the first explicit collector/agent split.
- `src/storage/briefing_history.py` and `src/learning/backtest.py` establish the first persistence and learning loop.
- `src/storage/outcome_history.py` and `src/learning/feedback.py` close the learning loop enough to inspect and reflect on outcomes.
- The architecture must allow future separation into collectors, analyzers, agents, and presenters.
- Evidence should be first-class so that later AI coordination and learning are possible.
- LINE should not be the only UI target; the output must be presenter-friendly.
- Risk should remain a first-class concern, not a derived side effect.

## Current Roadmap
### v1
- Morning briefing.
- Compact API.
- Risk-first summary.
- Simple manual and automatic data inputs.

### v1.5
- Strengthen evidence handling.
- Introduce dedicated RiskAI logic.
- Improve collector/analyzer separation.

### v2
- Add AI meeting / multi-agent coordination.
- Introduce ChairmanAI style orchestration.

### v3
- Add learning loop.
- Preserve predictions, results, and scores.
- Support backtesting and refinement.

## Priority Order
1. Keep the current v1 briefing stable.
2. Expand evidence and risk logic carefully.
3. Introduce clearer collector/analyzer separation.
4. Add presenters such as LINE and Web.
5. Add learning and backtesting later.

## Cautions
- External market and news sources can be slow or unavailable.
- Tests should stub network calls where possible.
- Do not introduce secrets, API keys, or personal tokens.
- Keep the repo public-safe.
- Default history and outcome files live outside the repository tree; env vars can override them.
- When changing payload shape, update docs and tests together.

## Verification
- Run `python -m pytest`.
- Confirm the briefing endpoint still returns the full payload.
- Confirm docs stay aligned with implementation.

## Public-Safe Status
The repository was audited before public release.
Git history was sanitized to remove email metadata.
No secrets were found in the tracked source at the time of the audit.
