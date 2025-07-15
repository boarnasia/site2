# Task 26: HTMLパーサーの単体テスト実装

## 目的

Task 25で実装されたHTMLパーサー関連のアダプター（`BeautifulSoupParser`, `ChardetDetector`など）の品質を保証するため、網羅的な単体テストを作成する。

## 背景

TDD（テスト駆動開発）のプラクティスに従い、実装された機能が仕様通りに動作することを検証し、将来のリファクタリングに対する安全網を構築する。

## 成果物

1.  **`tests/unit/adapters/parsers/`** ディレクトリの作成
2.  **テストフィクスチャの準備**
    -   `tests/fixtures/html/` ディレクトリに、テスト用のHTMLファイル（正常系、異常系、各種エンコーディング）を配置する。
3.  **テストモジュールの作成**
    -   `tests/unit/adapters/parsers/test_beautifulsoup_parser.py`
    -   `tests/unit/adapters/parsers/test_beautifulsoup_analyzer.py`
    -   `tests/unit/adapters/parsers/test_chardet_detector.py`
    -   `tests/unit/adapters/parsers/test_llm_preprocessor.py`

## テスト要件

### 1. `ChardetDetector`のテスト
-   [ ] **正常系**: UTF-8, Shift_JIS, EUC-JPなどの主要なエンコーディングが正しく検出できること。
-   [ ] **エイリアス**: `shift-jis`が`shift_jis`に正規化されるなど、エイリアスが正しく処理されること。
-   [ ] **異常系**: 存在しないファイル、空のファイル、判定不能なバイト列などを扱った際に、適切にデフォルト値（utf-8）を返すか、または定義された例外を送出すること。

### 2. `BeautifulSoupParser`のテスト
-   [ ] **パース処理**: 正常なHTML、壊れたHTML、巨大なHTMLを処理してもクラッシュしないこと。
-   [ ] **テキスト抽出**: `script`タグや`style`タグが正しく除去され、テキストが抽出されること。
-   [ ] **セレクタ検索**: 単一および複数のCSSセレクタで、要素が正しく検索できること。見つからない場合に空の結果を返すこと。

### 3. `BeautifulSoupAnalyzer`のテスト
-   [ ] **構造分析**: 見出しの数や`main`タグの有無などが正しくカウント・判定されること。
-   [ ] **メタデータ抽出**: `title`, `description`, `lang`属性などが正しく抽出されること。
-   [ ] **テキスト密度**: テキスト密度が正しく計算されること。

### 4. `LLMPreprocessor`のテス��
-   [ ] **前処理**: 不要なタグ（`script`, `style`）や属性が除去され、LLMに適した形式に変換されること。
-   [ ] **最大長**: 指定した最大長でテキストが切り詰められること。

## 受け入れ基準

-   [ ] 上記のテスト要件を全て満たす単体テストが実装されていること。
-   [ ] テストカバレッジが目標値（例: 90%以上）に達していること。
-   [ ] 全てのテストが`pytest`で正常にパスすること。

## 依存関係

-   Task 25: HTMLパーサーアダプターの実装
-   pytest

## 次のタスク

→ **Task 05: Detect:Mainサービスの実装**
