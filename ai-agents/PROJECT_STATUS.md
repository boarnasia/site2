# site2プロジェクト - 現在の状態

最終更新: 2025-01-14

## 📍 現在のフェーズ

**Task 22完了** - インターフェース定義の統合完了
**Task 23準備中** - パイプライン統合テストの再実装

## ✅ 完了したタスク

### Task 01-02: 基礎設計
- プロジェクト基本設計完了
- Pydanticベースのドメインモデル設計
- 契約（Protocol）定義

### Task 20: パイプライン統合テスト（問題あり）
- モックサービス実装
- DIコンテナ（TestContainer）設定
- 統合テスト作成
- **問題**: インターフェース違反（`_html_content`使用）

### Task 21: データフロー修正
- Protocol定義の修正
  - `DetectServiceProtocol.detect_order`にNavigationパラメータ追加
  - `BuildServiceProtocol.build_markdown`にDocumentOrderパラメータ追加
- モックサービスの更新
- 統合テストの修正

### Task 22: インターフェース定義の統合
- `services.py`を削除
- `*_contracts.py`に統一（統合型アプローチ）
- Protocol命名は`*Protocol`サフィックスを維持（Python慣習）

## 🎯 次のタスク

**Task 23: パイプライン統合テストの再実装**
- Task 20の問題を解決
- 正しいインターフェースに準拠した実装

## 🔧 技術的な状態

### 解決済みの課題
- ✅ Protocol定義の統一（`*_contracts.py`に集約）
- ✅ データフロー設計：Navigation → DocumentOrder → MarkdownDocument
- ✅ Protocol命名規則（Pythonらしく`*Protocol`サフィックス）

### 未解決の技術課題
- [ ] パイプライン統合テストのインターフェース準拠
- [ ] エラーハンドリングパターンの統一
- [ ] 実サービスの実装
- [ ] 非同期処理の最適化

### Task 23で解決予定
- `WebsiteCacheRepositoryProtocol.save`メソッドの削除
- `CachedPage.read_text()`メソッドの追加
- 正しいデータフロー：FetchResult → Repository → CachedPage → HTML

## 📊 実装優先順位

1. **Task 23完了**
   - インターフェース準拠の統合テスト
   - 正しいデータフローの確立

2. **FetchService実装** (`src/site2/core/use_cases/fetch_service.py`)
   - `FetchServiceProtocol`の実装
   - リポジトリとクローラーの依存性注入

3. **WgetCrawler実装** (`src/site2/adapters/crawlers/wget_crawler.py`)
   - `WebCrawlerProtocol`の実装
   - subprocessでwgetを呼び出し

4. **FileRepository実装** (`src/site2/adapters/storage/file_repository.py`)
   - `WebsiteCacheRepositoryProtocol`の実装
   - キャッシュの読み込み（saveは不要）

## 📝 重要な技術的決定事項

1. **Pydantic採用**
   - dataclassからPydanticへ移行完了
   - 新規モデルは全てPydanticで実装

2. **非同期処理**
   - 全サービスメソッドをasync/awaitで統一
   - pytest-asyncioでテスト

3. **依存性注入**
   - dependency-injectorを使用
   - TestContainerでモック注入

4. **インターフェース設計**
   - 統合型アプローチ（`*_contracts.py`）
   - Contract-First開発

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
