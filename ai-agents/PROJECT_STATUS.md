# site2プロジェクト - 現在の状態

最終更新: 2025-01-13

## 📍 現在のフェーズ

**Task 21完了** - パイプライン統合テスト修正済み

## ✅ 完了したタスク

### Task 01-02: 基礎設計
- プロジェクト基本設計完了
- Pydanticベースのドメインモデル設計
- 契約（Protocol）定義

### Task 20: パイプライン統合テスト
- モックサービス実装
- DIコンテナ（TestContainer）設定
- 統合テスト作成（24個全てPASSED）

### Task 21: データフロー修正
- Protocol定義の修正
  - `IDetectService.detect_order`にNavigationパラメータ追加
  - `IBuildService.build_markdown`にDocumentOrderパラメータ追加
- モックサービスの更新
- 統合テストの修正

## 🎯 次のタスク

**Task 3: 詳細設計**

## 🔧 技術的な状態

### 解決済みの課題
- ✅ Protocol命名規則の統一（`I`プレフィックスで統一）
- ✅ データフロー設計：Navigation → DocumentOrder → MarkdownDocument
- ✅ モックベースでのパイプライン動作確認

### 未解決の技術課題
- [ ] エラーハンドリングパターンの統一
- [ ] 実サービスの実装
- [ ] 非同期処理の最適化

## 📊 実装優先順位

1. **FetchService実装** (`src/site2/core/use_cases/fetch_use_case.py`)
   - `IFetchService`の実装
   - リポジトリとクローラーの依存性注入

2. **WgetCrawler実装** (`src/site2/adapters/crawlers/wget_crawler.py`)
   - `IWebCrawler`の実装
   - subprocessでwgetを呼び出し

3. **FileRepository実装** (`src/site2/adapters/storage/file_repository.py`)
   - `IWebsiteCacheRepository`の実装
   - キャッシュの保存・読み込み

4. **CLI統合** (`src/site2/adapters/cli/fetch_command.py`)
   - CLIとユースケースの接続
   - 依存性注入の設定

## 📝 重要な技術的決定事項

1. **Pydantic採用**
   - dataclassからPydanticへ移行中
   - 新規モデルは全てPydanticで実装

2. **非同期処理**
   - 全サービスメソッドをasync/awaitで統一
   - pytest-asyncioでテスト

3. **依存性注入**
   - dependency-injectorを使用
   - TestContainerでモック注入

## 🚀 開発サイクル

```
TODO実行 → Report作成 → 評価 → PROJECT_STATUS更新 → 次のTODO
```

1. **TODO実行**: Sonnetがタスクを実装
2. **Report作成**: 実行結果を`ai-agents/reports/`に保存
3. **評価**: ユーザーとOpusで結果を評価
4. **PROJECT_STATUS更新**: このファイルを更新
5. **次のTODO**: 次のタスクへ進む

## 📁 関連ファイル

- タスク定義: `ai-agents/todos/`
- 実行レポート: `ai-agents/reports/`
- 基本方針: `ai-agents/AGENT_CONTEXT.md`
- タスク一覧: `ai-agents/todos.md`
