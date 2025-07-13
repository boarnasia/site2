# Task 20: パイプライン統合テストの実装

## 背景
task 3（詳細設計）に進む前に、基本的なパイプラインが正しく連携することを確認する必要がある。
TestContainerとモックサービスを使用して、エンドツーエンドの動作を検証する。

## 目的
- DIコンテナを使用したパイプライン全体の動作確認
- 各サービス間のインターフェース整合性の検証
- 早期の問題発見と修正

## 実装内容

### 1. モックサービスの作成
- `tests/mocks/services.py` に以下を実装:
  - `MockFetchService`: simple-siteのHTMLを返す
  - `MockDetectService`: メインコンテンツとナビゲーションを検出
  - `MockBuildService`: 簡単なMarkdownを生成
  - `MockRepository`: メモリ内でのキャッシュ管理

### 2. TestContainerの具体化
- `tests/integration/test_container.py`:
  - TestContainerにモックサービスを設定
  - 依存関係の注入が正しく動作することを確認

### 3. パイプライン統合テスト
- `tests/integration/test_pipeline_integration.py`:
  - autoコマンドの流れをシミュレート
  - fetch → detect → build の連携確認
  - 期待される出力の検証

### 4. BDDテストの準備
- `tests/features/pipeline.feature` 用のステップ定義
- 最小限のステップ実装（モックを使用）

## 成功基準
- [ ] モックサービスが期待通りの動作をする
- [ ] DIコンテナ経由でサービスが正しく注入される
- [ ] パイプライン全体が通しで動作する
- [ ] simple-siteを入力として、期待されるMarkdownが出力される
- [ ] エラーケースも適切にハンドリングされる

## 注意事項
- 実装の詳細よりも、インターフェースの検証に重点を置く
- 発見された問題は記録し、task 3で対処する
- モックは最小限の実装に留める（本実装はtask 3以降）

## 期待される成果物
1. モックサービス実装（tests/mocks/services.py）
2. TestContainer設定（tests/integration/test_container.py）
3. 統合テスト（tests/integration/test_pipeline_integration.py）
4. 問題点のリスト（必要に応じて）
