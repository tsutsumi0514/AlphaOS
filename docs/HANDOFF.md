# AlphaOS Handoff

## Project Purpose
AlphaOS is an AI-assisted investment decision support operating system for individual investors.
Its goal is not to automate trading.
Its goal is to help a human find buy candidates, see evidence clearly, understand risk, and decide quickly.
Its primary output is candidate-oriented decision support, not market summary alone.

## Core Design Philosophy
- Reduce information overload.
- Help the user understand the market in about 5 seconds.
- Show reasons and confidence.
- Prioritize risk management over profit chasing.
- Keep the final decision with the human.
- Support buy-candidate ranking and entry timing.
- Treat day-trade and swing-trade as separate output modes with shared core data.
- Build a design that can survive future model and UI changes.

## Current Architecture

### Data Collection Layer
Current collectors fetch external inputs:
- `src/fx.py` for USD/JPY
- `src/market.py` for Nikkei change
- `src/watchlist.py` for watched symbols
- `src/news.py` for latest market news
- `src/collectors/briefing_inputs.py` for briefing input orchestration
- The collector layer now accepts an optional `interval` so live views can switch between daily and minute-granularity market inputs.

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
- `src/agents/macro_ai.py`, `src/agents/news_ai.py`, `src/agents/technical_ai.py`, and `src/agents/company_ai.py` provide the V4 subviews.
- `src/agents/decision_ai.py` synthesizes those views into one decision support block.
- `src/agents/contracts.py` defines the shared AgentDecision contract for agent outputs.
- The next layer after `decision_ai` is the `Opportunity Engine`, which should turn evidence-backed decisions into ranked buy candidates and entry timing hints.
- The Opportunity Engine should also filter out weak or illiquid candidates before ranking and keep counter-evidence short.

### Storage and Learning Layer
- `src/storage/briefing_history.py` stores briefing snapshots in JSONL under the user's home directory by default.
- `src/storage/outcome_history.py` stores realized outcomes in JSONL under the user's home directory by default.
- `src/storage/news_history.py` stores archived market news in JSONL under the user's home directory by default.
- `src/storage/market_memory.py` stores market memories and replay summaries in JSONL under the user's home directory by default.
- `src/learning/backtest.py` scores briefings against later outcomes and aggregates weighted results.
- `src/learning/feedback.py` summarizes recent learning performance for the next briefing and exposes period snapshots.

### Briefing Orchestration Layer
- `src/briefing.py` merges signals into a compact briefing payload.
- `src/briefing.py` must remain a thin orchestrator and not absorb candidate-ranking logic.
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
- `src/app.py` accepts `interval=1d` or `interval=1m` on the briefing and candidate-oriented routes.
- `src/app.py` also exposes `/` as the simple Web presenter.
- `src/app.py` also exposes `/history` and `/backtest` for learning loop review.
- `src/app.py` also exposes `/history/view` as a simple Web review surface.
- `src/app.py` also exposes `/outcome` and `/learning`.
- `src/app.py` also exposes `/simulate` for historical replay and validation.
- `src/app.py` also exposes `/validate` for opportunity candidate virtual-trading validation.
- `src/app.py` also exposes `/memory` and `/memory/search` for market memory review and similar-case retrieval.
- `src/app.py` also exposes `/what-if`, `/knowledge-graph`, and `/replay/compare` for V6 exploration.
- `src/app.py` also exposes `/candidates` for ranked buy-candidate proposals.
- `src/app.py` also exposes `/daytrade-candidates` for dedicated daytrade-oriented candidate proposals.
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
- `/history/view` HTML page for browsing recent briefing snapshots.
- `/backtest` endpoint for scoring a briefing set against outcomes.
- `/outcome` endpoint for recording realized outcomes.
- `/learning` endpoint for reading the current learning summary.
- `/simulate` endpoint for replaying historical market inputs without future leakage.
- Replay mode calibrates threshold labels on the selected historical window, reports a baseline comparison, and includes 500-sample walk-forward validation by default when the archive is large enough.
- Briefing input collector under `src/collectors/briefing_inputs.py`.
- Top-level coordinator under `src/agents/chairman_ai.py`.
- Risk review step under `src/agents/risk_ai.py`.
- JSONL history storage under `src/storage/briefing_history.py`.
- JSONL outcome storage under `src/storage/outcome_history.py`.
- Weighted backtesting helpers under `src/learning/backtest.py`.
- Learning summary helpers with period snapshots under `src/learning/feedback.py`.
- Archived news helpers under `src/storage/news_history.py`.
- Historical replay helpers under `src/simulation/replay.py`.
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

## Preserved Base Assets
- `Evidence`
- `Confidence`
- `RiskAI`
- `ChairmanAI`
- `Replay`
- `Learning`
- `Market Memory`
- `Backtest`

These base assets must remain intact while the opportunity layer is added above them.

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
- Keep the review surface simple with Web history browsing.

### v4
- Add Decision AI with MacroAI, NewsAI, TechnicalAI, CompanyAI, RiskAI, and ChairmanAI synthesis.
- Support historical replay against archived market inputs.
- Keep the final decision human-facing and compact.

### v5
- Add Opportunity Engine.
- Build candidate ranking from Evidence, Confidence, and Risk.
- Add entry timing hints.
- Keep `/briefing` backward compatible.

### v6
- Add Market Memory and similar-case retrieval if it improves candidate quality.
- Store outcomes and replay results with the candidate history.

### v7
- Add Learning AI and backtest-driven refinement.

### v8
- Add simple Knowledge Graph and personalization only if they improve candidate proposals.

## Priority Order
1. Keep the current v1 briefing stable.
2. Add the candidate proposal layer above the current decision stack.
3. Expand evidence and risk logic carefully.
4. Split day-trade and swing-trade only after the shared candidate contract is stable.
5. Add memory and learning only when they improve real candidate quality.

## Cautions
- External market and news sources can be slow or unavailable.
- Tests should stub network calls where possible.
- Do not introduce secrets, API keys, or personal tokens.
- Keep the repo public-safe.
- Default history and outcome files live outside the repository tree; env vars can override them.
- Replay mode should not use future information. If archived news is unavailable, it should be reported as unavailable rather than guessed.
- Replay calibration is allowed only inside the selected replay window and must be reported alongside the baseline result.
- Walk-forward validation must use only past data for threshold selection and future data for evaluation.
- Replay defaults now target a 500-day lookback and a 5y period to make consistency checks less noisy and closer to product-scale validation.
- When changing payload shape, update docs and tests together.

## Verification
- Run `python -m pytest`.
- Confirm the briefing endpoint still returns the full payload.
- Confirm docs stay aligned with implementation.
- Candidate-oriented work should also keep `docs/opportunity-spec.md` in sync.

## Public-Safe Status
The repository was audited before public release.
Git history was sanitized to remove email metadata.
No secrets were found in the tracked source at the time of the audit.
## Interval Support

- `/briefing` keeps the existing daily behavior when `interval` is omitted.
- `interval=1m` is supported for daytrade-oriented data collection and validation.
- Replay and walk-forward validation reuse the same interval-aware loaders as live collection.
- The `/briefing` contract remains backward compatible; existing keys and summary behavior stay stable.
