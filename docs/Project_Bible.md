# Project Bible v1.0

## Project Name
AlphaOS

## Goal
個人投資家向けのAI投資支援OSを作る。

## Design Principles
- 情報を減らす
- 朝5秒で市場を理解できる
- AIは根拠と自信度を示す
- 利益よりリスク管理を重視する
- 最終判断は人間が行う

## MVP Scope
- 市場状況の要約
- 注目銘柄の簡易表示
- リスク警告
- LINEまたは簡易Web UI

## Non-Goals
- 自動売買
- 複雑すぎるダッシュボード
- すべての市場データを詰め込むこと

## Architecture Direction
- Evidence-first design
- Collectors, analyzers, agents, and presenters should be separable later
- RiskAI should be a first-class concept
- LINE専用にせず、Webや将来の音声UIへ展開できる形にする
- v1 は Morning Briefing 完成に集中し、v1.5 以降で AI Meeting と Learning を拡張する
