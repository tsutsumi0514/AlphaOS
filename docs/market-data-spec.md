# Market Data Spec

## Purpose
Provide the first real input path for AlphaOS briefing generation.

## First Source
- `usd_jpy`: USD/JPY rate

## Derived Output
- `fx_state`

## Current Mapping
- `usd_jpy >= 155` -> `weak yen`
- `usd_jpy <= 145` -> `strong yen`
- otherwise -> `neutral`

## Next Sources
- Nikkei 225
- watchlist symbols
- news headlines
