# Interval Support Note

AlphaOS now accepts an `interval` parameter for market data collection and validation flows.

## Supported intervals
- `1d`
- `1m`
- `2m`
- `5m`
- `15m`
- `30m`
- `60m`

## Behavior
- `/briefing` continues to work as before when `interval` is omitted.
- `interval=1m` enables minute-granularity inputs for daytrade-oriented checks.
- Replay and opportunity validation reuse the same interval-aware loaders.
- Candidate proposal and presentation layers remain unchanged for the `/briefing` contract.

## Compatibility
- Existing `/briefing` JSON keys remain stable.
- The minute interval is additive and does not change default daily behavior.
- Validation and replay tests should keep passing for both daily and minute-based inputs.
