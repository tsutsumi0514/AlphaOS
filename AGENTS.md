# AGENTS.md

This repository is AlphaOS, an investment support OS for individual investors.

## Working Rules
- Keep the UI simple and the output compact.
- Prefer evidence, reasons, and confidence over raw prediction.
- Do not introduce auto-trading.
- Preserve the principle that the final decision is always human.
- When adding new logic, keep data collection, analysis, and presentation separable.
- Use tests to lock in behavior before expanding features.

## Current Architecture
- `src/app.py`: FastAPI API entry point.
- `src/briefing.py`: briefing orchestration and payload shaping.
- `src/cache.py`: in-process TTL cache.
- `src/fx.py`: USD/JPY collection.
- `src/market.py`: Nikkei collection.
- `src/news.py`: market news collection.
- `src/watchlist.py`: watchlist collection.
- `src/evidence.py`: structured evidence objects.
- `src/agents/`, `src/collectors/`, `src/analyzers/`, `src/presenters/`: future expansion points.

## Verification
- Run `python -m pytest` from the repo root.
- Keep tests green before pushing changes.
- If a change affects output shape, update docs and tests together.

## Safety Notes
- No secrets should be committed.
- The repository was audited for public release, and history was sanitized to remove email metadata.
- External data sources may fail or slow down tests; use monkeypatching or stubs in tests.
