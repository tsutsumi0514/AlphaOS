# Market Data Spec

## Purpose
Provide the first real input path for AlphaOS briefing generation.

## First Source
- `usd_jpy`: USD/JPY rate
- `market_change_pct`: Nikkei 225 day-over-day percent change

## Derived Output
- `fx_state`
- `market_state`

## Current Mapping
- `usd_jpy >= 155` -> `weak yen`
- `usd_jpy <= 145` -> `strong yen`
- otherwise -> `neutral`
- `market_change_pct >= 0.7` -> `bullish`
- `market_change_pct <= -0.7` -> `bearish`
- otherwise -> `neutral`

## Next Sources
- Nikkei 225
- watchlist symbols
- news headlines
