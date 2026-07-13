# AlphaOS

個人投資家向けのAI投資支援OSです。

## Goal
- 情報を減らす
- 朝5秒で市場を理解する
- AIは根拠と自信度を示す
- 利益よりリスク管理を重視する
- 最終判断は人間が行う

## MVP
- 市場状況の要約
- 注目銘柄の簡易表示
- リスク警告
- LINEまたは簡易Web UI

## Key Docs
- [Project Bible](docs/Project_Bible.md)
- [Architecture](docs/architecture.md)
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
- Use the JSON API:
  - `http://127.0.0.1:8000/briefing`

## Test
- Run tests:
  - `pytest`
## Current Implementation
- `src/app.py`: FastAPI entrypoint for `/` and `/briefing`
- `src/collectors/briefing_inputs.py`: briefing input collection
- `src/agents/chairman_ai.py`: briefing orchestration
- `src/agents/risk_ai.py`: risk review step
- `src/briefing.py`: Briefing data builder
- `src/analyzers/briefing_signals.py`: Risk and evidence helpers
- `src/storage/briefing_history.py`: JSONL briefing history
- `src/learning/backtest.py`: Simple scoring and backtest helpers
- `src/evidence.py`: Structured evidence objects
- `src/presenters/web.py`: Simple HTML presenter
- `tests/test_app.py`: API and web UI tests
