# Market Data Spec

## Purpose
Provide the first real input path for AlphaOS briefing generation.

## First Source
- `usd_jpy`: USD/JPY rate
- `market_change_pct`: Nikkei 225 day-over-day percent change
- `watchlist_status`: single-symbol watchlist snapshot

## Derived Output
- `fx_state`
- `market_state`
- `watchlist_status[*].status`

## Current Mapping
- `usd_jpy >= 155` -> `weak yen`
- `usd_jpy <= 145` -> `strong yen`
- otherwise -> `neutral`
- `market_change_pct >= 0.7` -> `bullish`
- `market_change_pct <= -0.7` -> `bearish`
- otherwise -> `neutral`
- `watchlist_status[*].change_pct >= 2.0` -> `strong`
- `watchlist_status[*].change_pct <= -2.0` -> `weak`
- otherwise -> `steady`

## Next Sources
- Nikkei 225
- watchlist symbols
- news headlines
