# site2プロジェクト - AIエージェント総合コンテキスト

## 📋 プロジェクト概要

**site2**は、Webサイトを単一のMarkdownまたはPDFファイルに変換するCLIツールです。

- **GitHub**: https://github.com/boarnasia/site2/
- **前身プロジェクト**: site2pdf（PDF出力のみ）
- **主要改善点**: Markdown出力対応、Clean Architecture採用、開発プロセスの明確化
- **最終目標**: Markdown出力（ツール名の site2pdf は古い名残）

## 🏗️ 技術スタック & 開発環境

### 技術スタック
- **言語**: Python 3.12
- **プロジェクト管理**: Rye
- **CLI**: Typer
- **テスト**: pytest, pytest-bdd, pytest-cov, pytest-asyncio
- **Webクローリング**: wget (subprocess経由)
- **HTML解析**: BeautifulSoup4
- **PDF生成**: Playwright（HTMLからPDF生成）
- **型チェック**: 型ヒント使用（将来的にmypy追加予定）
- **依存性注入**: dependency-injector
- **ドメインモデル**: Pydantic

### 基本コマンド
```bash
# プロジェクト管理
rye run site2 --help
rye run python
rye run ipython

# テスト
rye run python -m pytest tests
rye run pytest tests/integration/test_pipeline_integration.py -v
rye run pytest tests/unit/test_fetch_domain.py::test_fetch_result_creation -v
rye run pytest tests/features/pipeline.feature -v

# 開発ツール
rye run pre-commit run --all-files
```

### 開発フロー
```bash
# 1. テスト実行（現在は失敗する）
rye run python -m pytest tests

# 2. 実装（契約に基づいて実装を作成）

# 3. テスト再実行（成功を確認）
rye run python -m pytest tests

# 4. BDDテスト実行
rye run python -m pytest tests/features

# 5. カバレッジ確認
rye run python -m pytest --cov=src
```

## 🎯 開発方針と原則

### 1. 採用している開発手法
- **DDD (Domain-Driven Design)**: ドメインモデルを中心とした設計
- **TDD (Test-Driven Development)**: テストファーストで開発
- **BDD (Behavior-Driven Development)**: pytest-bddを使用
- **Contract-First Development**: インターフェース定義を先行
- **Clean Architecture**: 依存関係の方向を内側に向ける

### 2. 重要な原則
- **設計先行**: 実装前に設計・契約・テストを完成させる
- **段階的実装**: MVP → 機能追加 → 最適化の順で進める
- **AI協調開発**: 明確な契約に基づいてAIに実装を委託
- **品質保証**: 契約準拠・テストカバレッジ・コードレビュー

### 3. 言語使用ルール

#### 🎯 言語使用の原則

**Commander / Worker 共通:**

##### 日本語を使用する場面
- ユーザーへのコミュニケーション
  - プログレスレポート
  - エラー報告
  - 完了通知
  - 質問や確認
  - 進捗状況の説明
- ユーザーもよむドキュメント
  - 技術仕様書・ドキュメント作成
  - コード・コメント・関数名
  - システム設計・技術解析

##### 英語を使用する場面
- Agent 間のやり取り
  - Agent内部の思考プロセス
  - Agent間のタスクファイル・通信
  - API通信・プロンプトエンジニアリング

#### 📝 実装ガイドライン

##### ファイル作成時の言語選択
```
ai-agents/tasks/        → Japanese
ai-agents/reports/      → English (Agent間通信) + Japanese summary for user
ai-agents/roles/        → Mixed (Description in Japanese, technical rules in English)
src/                    → Japanese (Code)
tests/                  → Japanese (Code)
examples/               → Japanese (Code)
docs/                   → Context-dependent (user-facing: Japanese, technical: English)
```

## 📁 プロジェクト構造

### ディレクトリ構造
```
site2/
├── src/site2/
│   ├── core/              # ビジネスロジック（外部依存なし）
│   │   ├── domain/        # ドメインモデル
│   │   │   ├── fetch_domain.py      # Fetch機能のドメインモデル
│   │   │   ├── detect_domain.py     # Detect機能のドメインモデル
│   │   │   └── build_domain.py      # Build機能のドメインモデル
│   │   ├── ports/         # インターフェース定義（契約）
│   │   │   ├── fetch_contracts.py   # Fetch契約定義
│   │   │   ├── detect_contracts.py  # Detect契約定義
│   │   │   ├── build_contracts.py   # Build契約定義
│   │   │   ├── pipeline_contracts.py # Pipeline契約定義
│   │   │   └── services.py          # 統合サービスインターフェース
│   │   ├── use_cases/     # ユースケース
│   │   └── containers.py  # 依存性注入コンテナ
│   ├── adapters/          # 外部システムとの接続
│   │   ├── cli/           # CLIアダプター
│   │   ├── crawlers/      # Webクローラー実装
│   │   └── storage/       # ストレージ実装
│   └── cli.py             # CLIエントリーポイント
├── tests/
│   ├── features/          # BDDテスト（pytest-bdd）
│   ├── unit/              # 単体テスト
│   ├── integration/       # 統合テスト
│   ├── mocks/             # モックサービス
│   └── fixtures/          # テストデータ
├── ai-agents/             # AIエージェント関連
│   ├── tasks/             # タスク定義
│   ├── reports/           # 実行レポート
│   └── prompts/           # プロンプト定義
└── docs/                  # ドキュメント
```

### 主要CLIコマンド仕様
```bash
# 自動変換（fetch + build）
site2 auto [--format <md|pdf>] <uri>

# 個別コマンド
site2 fetch <uri>                    # Webサイトをキャッシュ
site2 fetch:list                     # キャッシュ一覧
site2 detect:main <file_or_uri>      # メインコンテンツのCSSセレクタ検出
site2 detect:nav <file_or_uri>       # ナビゲーションのCSSセレクタ検出
site2 detect:order <path_or_uri>     # ドキュメント順序の検出
site2 build [--format <md|pdf>] <file_or_uri>...  # ビルド
```

### 重要なデータフロー
```
Navigation → DocumentOrder → MarkdownDocument
Fetch → Detect (Navigation) → Detect (Order with Navigation) → Build (with Order)
```

## 🤖 AIエージェント実行指示

### エージェントの役割

#### Commander（統括者）
- タスク全体の進行管理
- Workerへの作業指示
- 成果物のレビューと統合
- 進捗の報告

#### Worker（作業者）
- 具体的な実装作業
- テストの作成と実行
- ドキュメントの作成
- Commanderへの報告

### 基本的な実行フロー
```
1. Commanderがタスクを理解
2. Workerに具体的な作業を指示
3. Workerが実装
4. Commanderがレビュー
5. 必要に応じて修正
6. 完了報告
```

### Workerへの指示方法
```markdown
---
【Worker指示】
作業ID: [例: TASK01-1]
作業内容: [具体的な作業内容]
入力: [必要な情報やファイル]
期待する出力: [成果物の詳細]
制約: [守るべきルールや注意点]
---
```

### 作業完了報告フォーマット
```markdown
---
【作業完了報告】
作業ID: [対応する作業ID]
完了内容:
- [実装した機能]
- [作成したファイル]
- [更新したファイル]

テスト結果: [PASSEDまたは課題あり]
特記事項: [あれば]
---
```

### レポート保存場所
- タスク実行後のレポートは `ai-agents/reports/` に保存
- ファイル名: `task{番号}.md` または `task{番号}_{内容}.md`
- 例: `task20.md`, `task21_dataflow_fix.md`

## ⚡ 実装時重要事項

### 1. 契約準拠
すべての実装は`src/site2/core/ports/`に定義された契約（Protocol）に準拠すること。

重要な原則：
- サービス間のデータ依存関係を正しく理解する（Navigation → DocumentOrder → MarkdownDocument）
- 各Protocolのメソッドシグネチャを厳守する
- 非同期処理（async/await）の一貫性を保つ

### 2. 依存関係の方向
- Core層（domain, use_cases）は外部に依存しない
- Adapters層はCore層のインターフェースに依存
- 依存性注入で具象実装を注入

### 3. テストファースト
1. まずテストを書く（現在は既に用意済み）
2. テストが失敗することを確認
3. 実装を書く
4. テストが成功することを確認

### 4. エラーハンドリング
契約で定義されたエラーを適切に処理すること：
- `NetworkError` - ネットワーク関連のエラー
- `InvalidURLError` - URL検証エラー
- `CachePermissionError` - ファイルシステム権限エラー
- `DetectError` - コンテンツ検出関連のエラー
- `BuildError` - ドキュメント生成関連のエラー

各エラーは適切にハンドリングし、ユーザーに分かりやすいメッセージを表示すること。

### 5. コーディング規約
- **命名規則**: PEP 8準拠
- **型ヒント**: すべての関数に型ヒントを付ける
- **docstring**: Googleスタイル
- **最大行長**: 88文字（Black準拠）
- **インポート**: isortで整理

### 6. コミットメッセージ規約
- `feat:` 新機能
- `fix:` バグ修正
- `docs:` ドキュメント
- `test:` テスト
- `refactor:` リファクタリング

### 7. 最適化注意事項
- API使用時は以下に注意：
  - 大きなファイルは分割して処理
  - バッチ処理でAPI呼び出し回数を削減
  - レート制限を考慮した適切な待機時間の設定
- 各Agentは必ず `ai-agents/AGENT_CONTEXT.md` を最初に読み込んでルールを確認する

## 🔄 実装の進め方

実装の優先順位と現在のフェーズは以下を参照：
- `ai-agents/todos.md` - 優先順位付きタスクリスト
- `ai-agents/PROJECT_STATUS.md` - 現在の実装フェーズと状態

基本的な実装順序：
1. Core層の実装（ドメインモデル、ユースケース）
2. Adapters層の実装（外部システム接続）
3. CLI統合
4. テストとドキュメントの整備

## 📋 プロジェクト進捗の確認

現在の進捗状況は以下のファイルを参照：
- `ai-agents/todos.md` - タスク一覧と完了状況
- `ai-agents/PROJECT_STATUS.md` - 現在のフェーズとサマリー
- `ai-agents/reports/` - 各タスクの詳細な実行レポート

## 📚 参考情報

- [プロジェクト概要設計書](docs/design/project_overview.md)
- [BDD開発ガイド](docs/testing/bdd-guide.md)
- [前身プロジェクト site2pdf](https://github.com/boarnasia/site2pdf)

---

**重要**: このプロジェクトは設計駆動で進めています。実装を始める前に、必ず対応する契約定義とテストが存在することを確認してください。
