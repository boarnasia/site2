# Task 8-10 実行プロンプト: Build機能の実装

## 実行者への指示

あなたはsite2プロジェクトのSonnet実装者です。これからTask 8-10（Build機能）を実装します。

### 重要な前提条件

1. **これまでの経験から学んだこと**：
   - Protocol準拠を最優先する（Task 20-23の教訓）
   - クリーンアーキテクチャの原則を厳守する（Task 27-31の教訓）
   - Adapterは必ずProtocolを明示的に継承する
   - Use Case層はAdapter実装に直接依存しない

2. **ライブラリの選択**：
   - Markdown変換には**Markdownify**を使用（車輪の再発明を避ける）
   - PDF生成にはPlaywrightを使用（既存の設計通り）

3. **実装の順序**：
   - 各タスクで必ずテストを先に作成（TDD）
   - Protocol準拠の確認を最優先
   - DIコンテナへの登録まで完了させる

## Task 8: Markdownコンバーターの実装

### 1. 実装ファイル

```
src/site2/adapters/converters/
├── __init__.py
├── markdown_converter.py
└── markdownify_config.py
```

### 2. 実装要件

```python
# markdown_converter.py
from markdownify import markdownify as md
from ...core.ports.build_contracts import MarkdownConverterProtocol
from ...core.domain.build_domain import MarkdownConvertRequest, ConvertResult

class MarkdownifyConverter(MarkdownConverterProtocol):
    """Markdownifyを使用したMarkdownコンバーター"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()

    def convert(self, request: MarkdownConvertRequest) -> ConvertResult:
        """Protocol準拠のconvertメソッド"""
        # 1. HTMLファイルを読み込む
        # 2. BeautifulSoupでメインコンテンツを抽出
        # 3. Markdownifyで変換
        # 4. ConvertResultを返す
```

### 3. Markdownify設定

```python
# markdownify_config.py
DEFAULT_MARKDOWNIFY_CONFIG = {
    'strip': ['script', 'style'],  # 除去するタグ
    'convert': ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'span'],
    'autolinks': True,
    'heading_style': 'ATX',  # # スタイルの見出し
    'code_language': 'python',  # デフォルト言語
    'escape_misc': False,
    'wrap': True,
    'wrap_width': 80,
}
```

### 4. テストの実装

```python
# tests/unit/adapters/converters/test_markdown_converter.py
def test_markdown_converter_implements_protocol():
    """MarkdownifyConverterがProtocolを実装していることを確認"""
    assert isinstance(MarkdownifyConverter(), MarkdownConverterProtocol)

def test_convert_simple_html():
    """シンプルなHTMLの変換テスト"""
    # テストデータの準備
    # 変換実行
    # アサーション
```

## Task 9: PDFコンバーターの実装

### 1. 実装ファイル

```
src/site2/adapters/converters/
├── pdf_converter.py
└── playwright_config.py
```

### 2. 実装要件

```python
# pdf_converter.py
from playwright.sync_api import sync_playwright
from ...core.ports.build_contracts import PDFConverterProtocol
from ...core.domain.build_domain import PDFConvertRequest, ConvertResult

class PlaywrightPDFConverter(PDFConverterProtocol):
    """PlaywrightによるPDFコンバーター"""

    def convert(self, request: PDFConvertRequest) -> ConvertResult:
        """単一ファイルのPDF変換"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # ページ生成とPDF出力

    def convert_multiple(
        self, requests: List[PDFConvertRequest], merge: bool = True
    ) -> Union[ConvertResult, List[ConvertResult]]:
        """複数ファイルのPDF変換"""
        # PyPDF2などを使用してマージ
```

### 3. テストの実装

```python
# tests/unit/adapters/converters/test_pdf_converter.py
def test_pdf_converter_implements_protocol():
    """PlaywrightPDFConverterがProtocolを実装していることを確認"""
    assert isinstance(PlaywrightPDFConverter(), PDFConverterProtocol)
```

## Task 10: Buildサービスの実装

### 1. 実装ファイル

```
src/site2/core/use_cases/
└── build_service.py
```

### 2. 実装要件

```python
# build_service.py
from ..ports.build_contracts import (
    BuildServiceProtocol,
    BuildRequest,
    BuildResult,
    MarkdownConverterProtocol,
    PDFConverterProtocol
)

class BuildService(BuildServiceProtocol):
    """ビルドサービスの実装"""

    def __init__(
        self,
        markdown_converter: MarkdownConverterProtocol,
        pdf_converter: PDFConverterProtocol,
        html_parser: HtmlParserProtocol
    ):
        # Protocolを通じた依存性注入
        self._markdown_converter = markdown_converter
        self._pdf_converter = pdf_converter
        self._html_parser = html_parser

    def build(self, request: BuildRequest) -> BuildResult:
        """ドキュメントのビルド"""
        # 1. ordered_filesを順番に処理
        # 2. 各ファイルからコンテンツを抽出
        # 3. 指定されたフォーマットで変換
        # 4. 結果を結合してBuildResultを返す
```

### 3. DIコンテナへの登録

```python
# src/site2/infrastructure/containers.py
def _configure_converters(self) -> None:
    """コンバーターの設定"""
    # MarkdownifyConverter
    self.markdown_converter = providers.Factory(
        MarkdownifyConverter,
        config=providers.Dict(DEFAULT_MARKDOWNIFY_CONFIG)
    )

    # PlaywrightPDFConverter
    self.pdf_converter = providers.Factory(
        PlaywrightPDFConverter,
        options=providers.Dict(...)
    )

def _configure_build_services(self) -> None:
    """ビルドサービスの設定"""
    self.build_service = providers.Factory(
        BuildService,
        markdown_converter=self.markdown_converter,
        pdf_converter=self.pdf_converter,
        html_parser=self.html_parser
    )
```

### 4. 統合テスト

```python
# tests/integration/test_build_pipeline.py
def test_build_markdown_pipeline():
    """Markdownビルドのエンドツーエンドテスト"""
    container = Container()
    build_service = container.build_service()

    request = BuildRequest(
        cache_directory=test_cache_dir,
        main_selector="main",
        ordered_files=[...],
        doc_order=DocumentOrder(...),
        format=OutputFormat.MARKDOWN
    )

    result = build_service.build(request)
    assert isinstance(result.content, str)
    assert result.format == OutputFormat.MARKDOWN
```

## 実装時の注意事項

### 1. Protocol準拠の徹底
- 全てのAdapterクラスは対応するProtocolを明示的に継承
- メソッドシグネチャは完全に一致させる
- 戻り値の型も厳密に守る

### 2. エラーハンドリング
- Protocol定義にある例外を適切に発生させる
- カスタムエラークラスを使用（BuildError, ConvertError）
- 詳細なエラーメッセージを提供

### 3. テストの充実
- 単体テスト：各コンポーネントの動作確認
- 統合テスト：パイプライン全体の動作確認
- Protocolへの準拠テスト：必須

### 4. 依存関係の管理
```toml
# pyproject.tomlに追加
markdownify = "^0.11.6"
pypdf2 = "^3.0.1"  # PDF結合用
```

## 成功基準

1. [ ] 全てのテストがPASS（単体・統合）
2. [ ] Protocol準拠の確認（型チェック通過）
3. [ ] DIコンテナでの正常な依存性注入
4. [ ] Markdownify使用による効率的な実装
5. [ ] クリーンアーキテクチャの原則遵守

## 実行コマンド例

```bash
# テスト実行
make test-unit
make test-integration

# 型チェック
mypy src/site2/adapters/converters/
mypy src/site2/core/use_cases/build_service.py

# カバレッジ確認
make coverage
```

## 参考資料

- [Markdownifyドキュメント](https://github.com/matthewwithanm/python-markdownify)
- Task 20-23のレポート（インターフェース違反の教訓）
- Task 27-31のレポート（アーキテクチャ改善の教訓）

---

このプロンプトに従って実装を進めてください。問題が発生した場合は、これまでの教訓を思い出し、Protocol準拠とクリーンアーキテクチャを最優先に解決してください。
