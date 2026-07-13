# Briefing Spec

## Purpose
Show the minimum market information needed to understand the current situation in a few seconds.

## Fields
- `market_state`: Overall market tone, such as bullish, bearish, or unknown.
- `fx_state`: Currency market tone, especially JPY/USD pressure.
- `watchlist_status`: Status of watched symbols and themes.
- `risk_alerts`: Short warnings that need attention.
- `key_changes`: Important changes since the previous check.

## Principles
- Keep the output short.
- Prefer simple labels over long explanations.
- Use the same field names every time.

## Key Change Rules
- Generate short human-readable sentences when `key_changes` is not explicitly provided.
- Prioritize market tone, FX tone, and the first watchlist symbol.
- Keep the list compact enough for a quick morning scan.

## Risk Alert Rules
- Generate short risk-first warnings when `risk_alerts` is not explicitly provided.
- Prioritize bearish market tone, exporter risk from strong yen, and weakness in the first watchlist symbol.
- Keep alerts actionable and concise.
