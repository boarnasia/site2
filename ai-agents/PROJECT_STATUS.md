# site2プロジェクト - 現在の状態

最終更新: 2025-01-15

## 📍 現在のフェーズ

**Task 24準備中** - CLIのfetch/fetch:listコマンド実装

## ✅ 完了したタスク

### Task 01-02: 基礎設計
- プロジェクト基本設計完了
- Pydanticベースのドメインモデル設計
- 契約（Protocol）定義

### Task 03: FetchService実装
- FetchService（コアユースケース）
- WgetCrawler（wgetを使用したクローラー）
- FileRepository（キャッシュリポジトリ、読み取り専用）
- 全30テストがPASS

### Task 20: パイプライン統合テスト（問題あり→差し戻し）
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

### Task 23: パイプライン統合テストの再実装
- インターフェース準拠の実装
- `CachedPage.read_text()`メソッドの活用
- 正しいデータフロー実装
- 全6統合テストがPASS

## 🎯 次のタスク

**Task 24: CLIのfetch/fetch:listコマンド実装**
- 実装したFetchServiceを実際に使用可能に
- 動作確認しながら開発を進める

## 🔧 技術的な状態

### 解決済みの課題
- ✅ Protocol定義の統一（`*_contracts.py`に集約）
- ✅ データフロー設計：Navigation → DocumentOrder → MarkdownDocument
- ✅ Protocol命名規則（Pythonらしく`*Protocol`サフィックス）
- ✅ パイプライン統合テストのインターフェース準拠
- ✅ FetchService実装完了

### 未解決の技術課題
- [ ] エラーハンドリングパターンの統一
- [ ] Detectサービスの実装
- [ ] Buildサービスの実装
- [ ] 非同期処理の最適化

## 📊 実装優先順位

1. **Task 24: CLI実装**
   - `site2 fetch <url>`コマンド
   - `site2 fetch:list`コマンド

2. **Phase 2: 検出機能**
   - Task 04: HTMLパーサーの実装
   - Task 05: Detect:Mainサービスの実装
   - Task 06: Detect:Navサービスの実装
   - Task 07: Detect:Orderサービスの実装

3. **Phase 3: 変換機能**
   - Task 08: Markdownコンバーターの実装
   - Task 09: PDFコンバーターの実装
   - Task 10: Buildサービスの実装

## 📝 重要な技術的決定事項

1. **Pydantic採用**
   - dataclassからPydanticへ移行完了
   - 新規モデルは全てPydanticで実装

2. **非同期処理**
   - サービスメソッドは状況に応じて同期/非同期を選択
   - FetchServiceProtocolは同期的

3. **依存性注入**
   - dependency-injectorを使用
   - TestContainerでモック注入

4. **インターフェース設計**
   - 統合型アプローチ（`*_contracts.py`）
   - Contract-First開発

5. **リポジトリパターン**
   - WebsiteCacheRepositoryは読み取り専用
   - FetchServiceが内部でキャッシュ保存

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
