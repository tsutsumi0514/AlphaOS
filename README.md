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
  - `uvicorn src.app:app --reload`

## Test
- Run tests:
  - `pytest`
## Current Implementation
- `src/app.py`: FastAPI entrypoint
- `src/briefing.py`: Briefing data builder
- `tests/test_app.py`: API test

## Run
- Start the app:
  - `python -m src.main`
