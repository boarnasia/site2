# Task 04: HTML解析契約の定義 (再定義)

## 目的

クリーンアーキテクチャの原則に基づき、HTML解析機能の**インターフェース（契約）**と**データ転送オブジェクト（DTO）**を`core`層に定義する。これにより、ビジネスロジック（use cases）が具体的なパーサー実装（e.g., BeautifulSoup）から完全に独立することを保証する。

## 背景

当初の計画では契約と実装が混在していたが、クリーンアーキテクチャを徹底するため、責務を明確に分離する。このタスクでは、システムの中心である`core`層に、HTML解析機能が満たすべき仕様（プロトコル）を定義することに集中する。

## 成果物

1.  **`src/site2/core/ports/parser_contracts.py`**
    - HTML解析に関連する全てのプロトコルとDTOをこのファイルに定義する。

## 実装詳細

### 1. データ転送オブジェクト (DTOs)

`pydantic.BaseModel`を使用して、以下のデータ構造を定義する。

-   `ParseRequest`: パース対象のファイルパスやエンコーディングを指定。
-   `ParseResult`: パース結果の`BeautifulSoup`オブジェクトや処理時間を格納。
-   `TextExtractionRequest`: テキスト抽出のオプションを指定。
-   `TextExtractionResult`: 抽出したテキストとメタデータを格納。
-   `SelectorSearchRequest`: CSSセレクタ検索の条件を指定。
-   `SelectorSearchResult`: セレクタ検索結果の要素を格納。
-   `HTMLStructureAnalysis`: `main`タグの有無、見出しの数など、HTMLの構造分析結果。
-   `HTMLMetadata`: `title`, `description`などのメタデータ。

### 2. プロトコル (Ports)

`typing.Protocol`を使用して、以下のインターフェースを定義する。

-   **`EncodingDetectorProtocol`**:
    -   `detect_encoding(file_path: Path) -> str`
    -   `detect_encoding_from_bytes(data: bytes) -> str`

-   **`HTMLParserProtocol`**:
    -   `parse(request: ParseRequest) -> ParseResult`
    -   `parse_string(html: str) -> Any` (戻り値はBeautifulSoupオブジェクトを想定するが、型ヒントは`Any`としておく)
    -   `extract_text(request: TextExtractionRequest) -> TextExtractionResult`
    -   `find_by_selectors(request: SelectorSearchRequest) -> SelectorSearchResult`

-   **`HTMLAnalyzerProtocol`**:
    -   `analyze_structure(soup: Any) -> HTMLStructureAnalysis`
    -   `extract_metadata(soup: Any) -> HTMLMetadata`
    -   `calculate_text_density(element: Any) -> float`

-   **`HTMLPreprocessorProtocol`**:
    -   `preprocess_for_llm(soup: Any, max_length: int) -> str`

### 3. カスタム例外

-   `ParseError`
-   `SelectorError`
-   `AnalysisError`
-   `DetectionError`

## 受け入れ基準

-   [ ] `src/site2/core/ports/parser_contracts.py`が作成され、上記仕様が定義されていること。
-   [ ] 定義されたDTOとプロトコルが、後続の`detect`系サービスの要求を満たしていること。
-   [ ] `core`層の他のモジュールから、この契約ファイル以外に依存しない設計となっていること。

## 依存関係

-   pydantic
-   loguru (ログ出力用)

## 次のタスク

→ **Task 25: HTMLパーサーアダプターの実装**
→ **Task 26: HTMLパーサーの単体テスト実装**
