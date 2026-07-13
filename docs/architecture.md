# AlphaOS Architecture

## Purpose
AlphaOS is an investment support system that keeps the UI simple while preserving evidence, reasons, and risk awareness.

## Current Direction
The current `briefing` module is the v1 orchestration layer. It should remain small, but it must be easy to split into clearer roles later.
The current MVP uses a JSON `/briefing` API and a simple HTML `/` presenter.
Risk and evidence logic now live in a small analyzer module so the orchestration layer can stay compact.
The current v2 step adds explicit collector and agent entry points without changing the public API.
The current v3 step adds JSONL history storage and minimal backtesting helpers.
The current API layer also exposes `/history`, `/backtest`, `/outcome`, and `/learning` for reviewing stored briefings, recording outcomes, and scoring them against outcomes.

## Target Layering

```mermaid
flowchart TD
  A["Collectors"] --> B["Analyzers / Agents"]
  B --> C["RiskAI"]
  B --> D["ChairmanAI"]
  C --> D
  D --> E["Briefing"]
  E --> F["Presenter"]
  F --> G["LINE"]
  F --> H["Web"]
  F --> I["Voice"]
```

## Role Summary
- `collectors/`: fetch external data.
- `analyzers/`: derive signals and structured evidence.
- `agents/`: domain-specific AI workers such as NewsAI, MacroAI, RiskAI, and ChairmanAI.
- `briefing.py`: present a compact morning summary.
- `presenters/`: format the same briefing for LINE, Web, or future interfaces.
- `presenters/web.py`: current HTML presenter for the simple Web UI.
- `collectors/briefing_inputs.py`: current collector orchestration for the briefing inputs.
- `agents/chairman_ai.py`: current top-level briefing coordinator.
- `agents/risk_ai.py`: current risk review step.
- `storage/briefing_history.py`: briefing history persistence.
- `storage/outcome_history.py`: outcome history persistence.
- `learning/backtest.py`: score and backtest helpers.
- `learning/feedback.py`: learning summary helpers.

## Evidence First
AlphaOS should preserve evidence as structured objects, not only as final labels.
This makes later agent coordination, learning, and backtesting possible.

## Version Roadmap
- `v1`: Morning briefing, risk-first summary, simple API, simple Web UI.
- `v1.5`: Evidence and RiskAI refinement.
- `v2`: AI meeting / multi-agent coordination.
- `v3`: Learning loop, score tracking, and backtesting.
