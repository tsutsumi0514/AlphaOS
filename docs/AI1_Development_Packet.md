# AlphaOS AI1 Development Packet

## 目的
AlphaOSは、個人投資家向けのAI投資支援OSです。  
目的は自動売買ではなく、朝5秒で市場を理解し、Evidence・Confidence・Riskを示して、人間の最終判断を支援することです。

## 最重要方針
- 情報を減らす
- 根拠を示す
- Riskを利益より先に評価する
- 最終判断は人間
- 自動売買はしない
- `/briefing` の後方互換を壊さない
- `briefing.py` は集約専用に保つ

## 現在の骨格
- `collectors/` : USD/JPY、日経、ニュース、watchlist の取得
- `analyzers/` / `agents/` : 判断ロジック
- `presenters/` : LINE / Web / 将来出力先
- `storage/` : history / replay / memory
- `learning/` : backtest / 学習
- `briefing.py` : 最終集約のみ

## 実装済みの中心機能
- `/briefing`
- `headline`
- `market_state`
- `fx_state`
- `watchlist_status`
- `news_item`
- `risk_alerts`
- `key_changes`
- `reasons`
- `confidence`
- `evidence`
- USD/JPY 自動取得
- 日経平均の変化率取得
- watchlist 複数銘柄対応
- ニュース取得
- キャッシュ
- テスト

## 重要な設計判断
- `AgentDecision` と `Evidence` を共通契約にする
- `RiskAI` は独立評価
- `ChairmanAI` は最終集約のみ
- `Presenter` はUI依存を吸収
- `Replay` は live と同じ経路に寄せる
- V6 の Knowledge Graph は簡易版から始める

## V4 の実装順
1. `AgentDecision / Evidence` 契約を固定
2. `RiskAI` を独立化
3. `MacroAI` を追加
4. `NewsAI` を追加
5. `ChairmanAI` で集約
6. golden test を追加

## AI1への実装指示
- 新しい分析ロジックを `briefing.py` に戻さない
- 追加機能は `agents/` または `analyzers/` に置く
- まず契約を固定し、次に実装する
- docs と tests を同時更新する
- 既存 `/briefing` の出力形を維持する

## 優先チケット
- V4-01 `AgentDecision / Evidence 共通契約を定義`
- V4-02 `RiskAI を独立モジュール化`
- V4-03 `MacroAI の structured decision を追加`
- V4-04 `NewsAI の structured decision を追加`
- V4-05 `ChairmanAI で決定を集約`
- V4-06 `Decision AI の golden test を追加`

## 注意点
- 過剰設計を避ける
- 自動売買は禁止
- Evidence なしの判断を増やさない
- docs/HANDOFF.md, docs/architecture.md, docs/briefing-spec.md と実装を同期する

## 一言
AlphaOSは予測AIではなく、意思決定支援OSです。  
最優先は「崩れない設計」です。
