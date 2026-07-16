# Opportunity Spec

## Purpose
Turn evidence-backed decision support into ranked buy candidates and entry timing hints.
This layer sits above the existing briefing stack and does not replace `/briefing`.

## Inputs
- `evidence`: Structured proof items from the briefing layer.
- `confidence`: Briefing confidence label.
- `risk_alerts`: Risk-first warnings from RiskAI and the analyzer layer.
- `decision_ai`: Multi-view synthesis from ChairmanAI.
- `learning_summary`: Recent learning performance and period snapshots.
- `candidate_learning_profile`: Candidate-specific learning bias derived from the current learning summary.
- `replay_summary`: Historical replay and validation signals when available.
- `watchlist_status`: Current tracked symbols and their states.
- `market_state`: Current broad market tone.
- `fx_state`: Current FX tone.

## Outputs
- `candidates`: Ordered buy-candidate proposals.
- `excluded_candidates`: Filtered-out watchlist items with a short exclusion reason.
- `candidate_rank`: Normalized score and ordering metadata.
- `entry_timing`: Simple entry timing hints such as `buy_now`, `wait`, or `avoid`.
- `candidate_reason`: Short explanation for why the candidate exists.
- `candidate_risk`: Short risk summary.
- `candidate_evidence`: Evidence subset supporting the candidate.
- `counter_evidence`: Short counter-evidence list that explains why the candidate may fail.
- `liquidity`: Simple liquidity state used by the candidate filter.
- `learning_profile`: Light-weight bias derived from learning history for score, confidence, and timing adjustments.
- `candidate_graph`: Lightweight Knowledge Graph context that helps explain the candidate path.

## Rules
- Do not force buy recommendations into `/briefing`.
- Keep the shared core evidence-first and risk-first.
- Keep the candidate layer thin and composable.
- Preserve backward compatibility for the existing briefing contract.
- Keep day-trade logic separate until the shared candidate contract is stable.
- Filter out weak or illiquid candidates before ranking.
- Keep the candidate entry reason short and one-line.

## Candidate Ranking
- Favor evidence-backed candidates with clearer momentum, lower risk, and stronger learning support.
- Use simple, explainable score components.
- Break ties with risk first, then evidence strength, then timing confidence.
- Candidate exclusion should remove low-confidence, thin-liquidity, and low-evidence noise.
- Learning should adjust ranking only through a small, explainable bias derived from past outcomes.
- Graph context should stay lightweight and explanatory, not become a second ranking engine.

## Entry Timing
- `buy_now`: Candidate conditions are favorable now.
- `wait`: Candidate is valid but timing is not yet favorable.
- `avoid`: Risk or signal quality is too weak.

## Presentation Boundary
- `/briefing` remains the compact support view.
- Candidate ranking should be shown in a separate opportunity-oriented view.
- The candidate layer may reference the existing briefing, but it should not mutate the `/briefing` contract.
