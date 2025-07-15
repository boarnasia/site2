# Task 25: HTMLパーサーアダプターの実装

## 目的

Task 04で定義された`parser_contracts.py`のインターフェース（プロトコル）に基づき、HTML解析機能の具体的な実装を**アダプター層**に作成する。`BeautifulSoup`や`chardet`といった外部ライブラリへの依存をこの層に閉じ込める。

## 背景

クリーンアーキテクチャの原則に従い、`core`層で定義された契約と、外部ライブラリを利用する実装を分離する。このタスクは後者の「実装」部分を担当する。

## 成果物

1.  **`src/site2/adapters/parsers/`** ディレクトリの作成
2.  **`src/site2/adapters/parsers/beautifulsoup_parser.py`**
    -   `HTMLParserProtocol`を実装した`BeautifulSoupParser`クラスを作成。
    -   `HTMLAnalyzerProtocol`を実装した`BeautifulSoupAnalyzer`クラスを作成。
    -   `HTMLPreprocessorProtocol`を実装した`LLMPreprocessor`クラスを作成。
3.  **`src/site2/adapters/parsers/chardet_detector.py`**
    -   `EncodingDetectorProtocol`を実装した`ChardetDetector`クラスを作成。
4.  **DIコンテナへの登録**
    -   `src/site2/core/containers.py`に、定義した契約と実装を結びつける設定を追加する。

## 実装詳細

### 1. `ChardetDetector`
-   `chardet`ライブラリを使用して、ファイルまたはバイト列からエンコーディングを検出するロジックを実装する。

### 2. `BeautifulSoupParser`
-   `BeautifulSoup`ライブラリを内部で使用し、HTMLのパース、テキスト抽出、セレクタ検索を行う。
-   エンコーディング検出には`ChardetDetector`を利用する。

### 3. `BeautifulSoupAnalyzer`
-   パース済みの`BeautifulSoup`オブジェクトを受け取り、構造分析やメタデータ抽出を行う。

### 4. `LLMPreprocessor`
-   `examples/think_page_gemini/`の実装を参考に、LLMへの入力に適した形にHTMLを前処理する。

### 5. DIコンテナ (`containers.py`)
-   `parser_service = providers.Factory(BeautifulSoupParser, ...)` のように、プロトコルと実装クラスを紐付ける。

## 受け入れ基準

-   [ ] `parser_contracts.py`で定義された全てのプロトコルが、アダプター層のクラスによって実装されていること。
-   [ ] `chardet`と`BeautifulSoup4`への依存が`src/site2/adapters/parsers/`配下に限定されていること。
-   [ ] DIコンテナを通じて、`core`層のサービスが具体的な実装を知ることなくパーサー機能を利用できること。
-   [ ] 元のTask 04で計画されていた実装要件（エラーハンドリング、パフォーマンスなど）が満たされていること。

## 依存関係

-   Task 04: HTML解析契約の定義
-   BeautifulSoup4
-   chardet
-   loguru

## 次のタスク

→ **Task 26: HTMLパーサーの単体テスト実装**
