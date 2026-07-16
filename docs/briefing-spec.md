# Briefing Spec

## Purpose
Show the minimum market information needed to understand the current situation in a few seconds.
This output is a compact support layer, not the final buy-candidate ranking.

## Fields
- `headline`: One short line for a 5-second morning read.
- `market_state`: Overall market tone, such as bullish, bearish, or unknown.
- `fx_state`: Currency market tone, especially JPY/USD pressure.
- `news_item`: A single latest market news item, including what happened.
- `watchlist_status`: Status of watched symbols and themes.
- `risk_alerts`: Short warnings that need attention.
- `key_changes`: Important changes since the previous check.
- `reasons`: Short statements explaining why the current view was produced.
- `confidence`: A simple confidence label, such as low, medium, or high.
- `evidence`: Structured proof items that support the current view.
- `data_health`: Optional diagnostic state for external input availability and freshness.
- `data_warnings`: Optional short warnings when one or more upstream inputs fail.

## Agent Decision Contract
- `agent`: Name of the agent that produced the view.
- `stance`: Canonical stance label, such as supportive, balanced, defensive, neutral, or unknown.
- `score`: Normalized support score between 0 and 1.
- `confidence`: A simple confidence label, such as low, medium, or high.
- `reason`: One short explanation sentence.
- `evidence`: Structured proof items that justify the view.
- `summary`: Optional short recap of the agent view.
- `signals`: Optional short list of supporting signals.
- `views`: Optional list of subviews for ChairmanAI synthesis.

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

## News Rules
- Fetch only one latest market-related news item for the briefing.
- Keep the output short and human readable.
- Include the news title as part of the "what happened" layer when available.

## Reason And Confidence Rules
- Generate short reasons from the current market, FX, and watchlist signals.
- Estimate confidence from how many data-backed signals are available.
- Prefer simple confidence labels over numeric scores.

## Evidence Rules
- Preserve evidence as structured items instead of flattening everything into labels.
- Include the source, a short label, and the key value that drove the signal.
- Keep evidence compact enough for later AI coordination and learning.
- Use evidence to support future ChairmanAI, RiskAI, and presenter layers.
- Briefing-facing text should be derived from evidence-backed state whenever possible.

## Candidate Output Boundary
- Do not force buy recommendations into `/briefing`.
- Candidate ranking, entry timing, and day-trade mode should live in a separate opportunity-oriented layer.
- `/briefing` may reference that a candidate exists, but it should stay short and readable.

## Headline Rules
- Combine the most important market, FX, and watchlist signals into one short line.
- Prefer simple phrases over long explanations.
- Keep the headline readable in one glance.
