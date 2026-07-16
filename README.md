# AlphaOS

個人投資家向けのAI投資意思決定支援OSです。

## Goal
- 情報を減らす
- 朝5秒で市場を理解する
- AIは根拠と自信度を示す
- 利益よりリスク管理を重視する
- 最終判断は人間が行う
- 市場要約よりも、購入候補銘柄の提案を優先する

## MVP
- 購入候補銘柄の提案
- 候補の根拠表示
- リスク警告
- Entry Timing の簡易提示
- LINEまたは簡易Web UI

## Key Docs
- [Project Bible](docs/Project_Bible.md)
- [Architecture](docs/architecture.md)
- [Opportunity Spec](docs/opportunity-spec.md)
- [Interval Support Note](docs/interval-support.md)
- [Codex Guide](prompts/Codex_Guide.md)
- [ADR-0001](decisions/ADR-0001.md)
- [Roadmap](roadmap/roadmap.md)

## Project Structure
- `src/` Application source code
- `tests/` Automated tests

## Setup
- Install dependencies:
  - `pip install -r requirements.txt`

## Run
- Start the app:
  - `python -m src.main`
- Open the web UI:
  - `http://127.0.0.1:8000/`
- Open the candidate UI:
  - `http://127.0.0.1:8000/candidates/view`
- Use the JSON API:
  - `http://127.0.0.1:8000/briefing`
- Use minute-granularity inputs when needed:
  - `http://127.0.0.1:8000/briefing?interval=1m`
- Replay and validation endpoints also accept `interval=1m` for daytrade-oriented checks.

## Test
- Run tests:
  - `pytest`
## Current Implementation
- `src/app.py`: FastAPI entrypoint for `/` and `/briefing`
- `src/app.py`: history, history view, and backtest API endpoints
- `src/app.py`: outcome and learning API endpoints
- `src/app.py`: replay and validation simulation API endpoint
- `src/app.py`: opportunity validation API endpoint
- `src/app.py`: candidate proposal API endpoint
- `src/app.py`: market memory and similar-case search endpoints
- `src/app.py`: what-if, knowledge graph, and replay comparison endpoints
- `src/app.py`: interval-aware input collection for `1d` and `1m` views
- `src/simulation/replay.py`: interval-aware replay and walk-forward validation
- `src/simulation/validation.py`: interval-aware candidate validation for daytrade, swing, and long horizons
- `src/agents/contracts.py`: shared AgentDecision contract
- `src/agents/`: decision synthesis and future opportunity layer entry points
- `src/collectors/briefing_inputs.py`: briefing input collection
- `src/agents/chairman_ai.py`: briefing orchestration
- `src/agents/risk_ai.py`: risk review step
- `src/agents/macro_ai.py`: macro perspective for V4
- `src/agents/news_ai.py`: news perspective for V4
- `src/agents/technical_ai.py`: technical perspective for V4
- `src/agents/company_ai.py`: company perspective for V4
- `src/agents/decision_ai.py`: V4 decision synthesis
- `src/briefing.py`: Briefing data builder
- `src/analyzers/briefing_signals.py`: Risk and evidence helpers
- `src/storage/briefing_history.py`: JSONL briefing history
- `src/storage/outcome_history.py`: JSONL outcome history
- `src/storage/news_history.py`: JSONL news archive
- `src/storage/market_memory.py`: JSONL market memory and replay summaries
- `src/learning/backtest.py`: Simple scoring and weighted backtest helpers
- `src/learning/feedback.py`: Learning summary helpers with period snapshots
- `src/simulation/replay.py`: Historical replay, validation, and simulation helpers
- `src/simulation/validation.py`: Virtual-trading validation for candidates
- `src/simulation/what_if.py`: Simple scenario simulator
- `src/opportunity.py`: Ranked buy-candidate proposal helpers with exclusion and summary counts
- `src/presenters/v6.py`: candidate UI with personal context, entry detail, entry reason, counter evidence, and exclusion tags
- `src/storage/market_memory.py`: Market memory persistence and similar-case retrieval
- `src/knowledge_graph.py`: Lightweight causal graph builder
- `src/personal.py`: Personal profile filters for candidate ranking
- `src/evidence.py`: Structured evidence objects
- `src/presenters/web.py`: Simple HTML presenter
- `src/presenters/history.py`: HTML history presenter
- `src/presenters/v6.py`: V6 HTML presenters
- `tests/test_app.py`: API and web UI tests
- `tests/test_simulation.py`: calibrated replay and 500-sample validation tests
- `tests/test_opportunity.py`: candidate ranking and proposal API tests

## Design Boundary
- `/briefing` remains backward compatible for market overview and risk-first summary use.
- Candidate-oriented features should be added in the next opportunity layer above the current briefing stack.
