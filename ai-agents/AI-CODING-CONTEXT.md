# site2プロジェクト - AIコーディングエージェント向けコンテキスト

## プロジェクト概要

**site2**は、Webサイトを単一のMarkdownまたはPDFファイルに変換するCLIツールです。

- **GitHub**: https://github.com/boarnasia/site2/tree/20250706-01-initial-work
- **前身プロジェクト**: site2pdf（PDF出力のみ）
- **主要改善点**: Markdown出力対応、Clean Architecture採用、開発プロセスの明確化

## 開発方針と原則

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

## プロジェクト構造

```
site2/
├── src/site2/
│   ├── core/              # ビジネスロジック（外部依存なし）
│   │   ├── domain/        # ドメインモデル
│   │   ├── ports/         # インターフェース定義（契約）
│   │   └── use_cases/     # ユースケース
│   ├── adapters/          # 外部システムとの接続
│   │   ├── cli/           # CLIアダプター
│   │   ├── crawlers/      # Webクローラー実装
│   │   └── storage/       # ストレージ実装
│   └── cli.py             # CLIエントリーポイント
├── tests/
│   ├── features/          # BDDテスト（pytest-bdd）
│   ├── unit/              # 単体テスト
│   ├── integration/       # 統合テスト
│   └── fixtures/          # テストデータ
├── contracts/             # 契約定義
└── docs/                  # ドキュメント
```

## 主要コマンドとその仕様

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

## 現在の実装状況

### ✅ 実装済み

1. **基本構造**
   - Clean Architectureに基づくディレクトリ構造
   - CLI基本実装（Typer使用）

2. **ドメインモデル** (`src/site2/core/domain/fetch_domain.py`)
   - 値オブジェクト: `WebsiteURL`, `CrawlDepth`
   - エンティティ: `CachedPage`, `WebsiteCache`
   - ドメインイベント: `PageFetched`, `CacheCreated`, `CacheUpdated`

3. **契約定義** (`src/site2/core/ports/fetch_contracts.py`)
   - DTOs: `FetchRequest`, `FetchResult`, `CacheListResult`
   - プロトコル: `FetchServiceProtocol`, `WebsiteCacheRepositoryProtocol`, `WebCrawlerProtocol`

4. **テスト基盤**
   - pytest-bdd導入済み
   - テスト用Webサーバー実装
   - BDDシナリオ作成済み

### ❌ 未実装（これから実装）

1. **ユースケース実装**
   - `FetchService` - Webサイト取得のビジネスロジック
   - `DetectService` - コンテンツ検出のビジネスロジック
   - `BuildService` - ドキュメント生成のビジネスロジック

2. **アダプター実装**
   - `WgetCrawler` - wgetを使用したクローラー
   - `FileRepository` - ファイルシステムへの保存
   - `MarkdownConverter` - Markdown変換
   - `PDFConverter` - PDF変換

3. **CLI統合**
   - CLIコマンドとユースケースの接続
   - 依存性注入の設定

## 実装時の重要事項

### 1. 契約準拠

すべての実装は`src/site2/core/ports/`に定義された契約（Protocol）に準拠すること：

```python
class FetchServiceProtocol(Protocol):
    def fetch(self, request: FetchRequest) -> FetchResult:
        """契約に定義された事前条件・事後条件を満たす"""
```

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

契約で定義されたエラーを適切に処理：
- `NetworkError` - ネットワーク関連
- `InvalidURLError` - URL検証
- `CachePermissionError` - ファイルシステム権限

## 開発フロー

```bash
# 1. テスト実行（現在は失敗する）
make test-unit

# 2. 実装
# 契約に基づいて実装を作成

# 3. テスト再実行（成功を確認）
make test-unit

# 4. BDDテスト実行
make test-bdd

# 5. カバレッジ確認
make coverage
```

## 技術スタック

- **言語**: Python 3.10+
- **プロジェクト管理**: Rye
- **CLI**: Typer
- **テスト**: pytest, pytest-bdd, pytest-cov
- **Webクローリング**: wget (subprocess経由)
- **HTML解析**: BeautifulSoup4
- **PDF生成**: pypdf, Playwright
- **型チェック**: 型ヒント使用（将来的にmypy追加予定）

## コーディング規約

- **命名規則**: PEP 8準拠
- **型ヒント**: すべての関数に型ヒントを付ける
- **docstring**: Googleスタイル
- **最大行長**: 88文字（Black準拠）
- **インポート**: isortで整理

## 次の実装優先順位

1. **FetchService実装** (`src/site2/core/use_cases/fetch_use_case.py`)
   - `FetchServiceProtocol`を実装
   - リポジトリとクローラーを依存性注入

2. **WgetCrawler実装** (`src/site2/adapters/crawlers/wget_crawler.py`)
   - `WebCrawlerProtocol`を実装
   - subprocessでwgetを呼び出し

3. **FileRepository実装** (`src/site2/adapters/storage/file_repository.py`)
   - `WebsiteCacheRepositoryProtocol`を実装
   - キャッシュの保存・読み込み

4. **CLI統合** (`src/site2/adapters/cli/fetch_command.py`)
   - CLIとユースケースを接続
   - 依存性注入の設定

## 参考情報

- [プロジェクト概要設計書](docs/design/project_overview.md)
- [BDD開発ガイド](docs/testing/bdd-guide.md)
- [前身プロジェクト site2pdf](https://github.com/boarnasia/site2pdf)

---

**重要**: このプロジェクトは設計駆動で進めています。実装を始める前に、必ず対応する契約定義とテストが存在することを確認してください。
