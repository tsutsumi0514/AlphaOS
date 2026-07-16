# AlphaOS AI1 Development Packet

## 目的
AlphaOSは、個人投資家向けのAI投資支援OSです。  
最終目的は、自動売買ではなく、買い候補銘柄を提案し、Evidence・Confidence・Risk・Entry Timing を示して、人間の最終判断を支援することです。

## 最重要方針
- 情報を減らす
- 根拠を示す
- Riskを利益より先に評価する
- 最終判断は人間
- 自動売買はしない
- `/briefing` の後方互換を壊さない
- `briefing.py` は集約専用に保つ
- `Opportunity Engine` を銘柄提案の中心に置く
- 候補除外・流動性フィルタ・反証表示を候補レイヤーで扱う
- デイトレと中長期は共通コアの後で分岐する
- 候補提案の入口は `/candidates` と `/daytrade-candidates` に分ける

## 現在の骨格
- `collectors/` : USD/JPY、日経、ニュース、watchlist の取得
- `analyzers/` / `agents/` : 判断ロジック
- `presenters/` : LINE / Web / 将来出力先
- `storage/` : history / replay / memory
- `learning/` : backtest / 学習
- `briefing.py` : 最終集約のみ

## 実装済みの中心機能
- `/briefing`
- `/briefing` の土台となる Evidence / Risk / Confidence / Decision 契約
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
- `Opportunity Engine` は `Decision AI` の上に載る別レイヤーとする
- `Candidate Ranking` と `Entry Timing` を先に固める
- 根拠が弱い銘柄は出さない
- 候補は短い理由と反証を併記する

## V4 の実装順
1. `AgentDecision / Evidence` 契約を固定
2. `RiskAI` を独立化
3. `MacroAI` を追加
4. `NewsAI` を追加
5. `ChairmanAI` で集約
6. golden test を追加

## V5 以降の実装順
1. `Opportunity Engine` の出力契約を固定
2. `Candidate Ranking` を追加
3. `Entry Timing` を追加
4. デイトレ用の分岐ポイントを設計
5. `Market Memory` は効果が見える場合のみ追加
6. `Learning` は実データで改善が確認できた領域から伸ばす
7. `What-if Simulator` と `Knowledge Graph` は検証基盤の結果を見ながら最小構成で追加する
8. `Personal AI` は候補提案のフィルタ層として追加する

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
- V5-01 `Opportunity Candidate 共通契約を定義`
- V5-02 `Evidence / Risk / Confidence から候補評価を生成`
- V5-03 `Candidate Ranking を追加`
- V5-04 `Entry Timing の最小ロジックを追加`
- V5-05 `日中モードと中長期モードの分岐点を追加`

## 注意点
- 過剰設計を避ける
- 自動売買は禁止
- Evidence なしの判断を増やさない
- docs/HANDOFF.md, docs/architecture.md, docs/briefing-spec.md, docs/opportunity-spec.md と実装を同期する
- `/briefing` は維持しつつ、候補提案は別レイヤーで育てる

## 一言
AlphaOSは予測AIではなく、意思決定支援OSです。  
最優先は「崩れない設計」です。
