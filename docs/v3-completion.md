# AlphaOS v3 Completion Criteria

v3 is considered complete when the following are true:

- The briefing flow still returns the compact `/briefing` payload with `headline`, `market_state`, `fx_state`, `risk_alerts`, `key_changes`, `reasons`, `confidence`, `evidence`, `briefing_id`, and `learning_summary`.
- Outcome recording is idempotent for the same `briefing_id`.
- Learning summaries include weighted accuracy and period snapshots.
- The JSON review endpoints remain available:
  - `GET /history`
  - `POST /backtest`
  - `POST /outcome`
  - `GET /learning`
- The Web UI stays simple and includes a dedicated history view.
- Default persistence stays outside the repository tree.
- `python -m pytest` passes.

These criteria lock the current v3 baseline so later work can extend it without silently breaking the learning loop.
