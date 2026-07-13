# Market Data Spec

## Purpose
Provide the first real input path for AlphaOS briefing generation.

## First Source
- `usd_jpy`: USD/JPY rate
- `market_change_pct`: Nikkei 225 day-over-day percent change
- `watchlist_status`: small multi-symbol watchlist snapshot
- `news_item`: one latest market-related headline and source

## Derived Output
- `fx_state`
- `market_state`
- `watchlist_status[*].status`
- `news_item` -> `key_changes` one-line "what happened" summary

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

## News Source
- Use a single latest market-related headline.
- Keep the news item short enough for the morning briefing.
- Prefer a headline that explains what happened, not a full article digest.

## Next Sources
- Nikkei 225
- watchlist symbols
- news headlines

## Watchlist Defaults
- Use a short list of core symbols first.
- Prefer large, liquid names that are meaningful for a daily scan.
- Keep the initial list small enough to read in a few seconds.
