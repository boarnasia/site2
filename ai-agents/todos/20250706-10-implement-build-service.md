# Todo 10: Buildサービスの実装

## 目的

検出された情報を使用して、複数のHTMLファイルを1つのMarkdown/PDFにビルドする。

## 背景

パイプラインの最終ステップとして、以下の情報を統合する：
- メインコンテンツのセレクタ
- ドキュメントの順序
- 出力フォーマット

## 成果物

1. **BuildService実装**
   - 複数ファイルの結合
   - フォーマット変換の調整
   - メタデータの埋め込み

## 実装詳細

### BuildService

```python
class BuildService:
    def __init__(
        self,
        parser: HTMLParserProtocol,
        markdown_converter: MarkdownConverterProtocol,
        pdf_converter: PDFConverterProtocol,
    ):
        self.parser = parser
        self.converters = {
            OutputFormat.MARKDOWN: markdown_converter,
            OutputFormat.PDF: pdf_converter,
        }

    def build(self, request: BuildRequest) -> BuildResult:
        """
        ビルドプロセス：
        1. 各ファイルからコンテンツ抽出
        2. 順序通りに結合
        3. フォーマット変換
        4. 後処理（目次、ページ番号など）
        """
```

### コンテンツ抽出

```python
def extract_content(
    self,
    file_path: Path,
    selector: str
) -> ExtractedContent:
    """
    HTMLファイルからコンテンツを抽出

    1. HTMLをパース
    2. セレクタで要素を選択
    3. 不要な要素を除去
    4. 相対リンクを調整
    """
    soup = self.parser.parse(file_path)

    # メインコンテンツを選択
    main_element = soup.select_one(selector)
    if not main_element:
        # フォールバック：bodyタグ全体
        main_element = soup.body

    # クリーンアップ
    self._remove_unwanted_elements(main_element)
    self._fix_relative_links(main_element, file_path)

    return ExtractedContent(
        title=self._extract_title(soup),
        content=main_element,
        metadata=self._extract_metadata(soup)
    )
```

### 結合ロジック

```python
def combine_contents(
    self,
    contents: List[ExtractedContent],
    ordered_files: List[OrderedFile]
) -> CombinedDocument:
    """
    コンテンツを順序通りに結合

    1. 階層に応じて見出しレベルを調整
    2. ページ区切りを挿入
    3. 内部リンクを更新
    """
    document = CombinedDocument()

    for i, (content, order_info) in enumerate(
        zip(contents, ordered_files)
    ):
        # 見出しレベルを調整
        adjusted_content = self._adjust_heading_levels(
            content,
            order_info.level
        )

        # ページ区切り（PDFの場合）
        if i > 0 and self.format == OutputFormat.PDF:
            document.add_page_break()

        # コンテンツを追加
        document.add_section(
            title=order_info.title,
            content=adjusted_content,
            level=order_info.level
        )

    return document
```

### 後処理

```python
def post_process(
    self,
    document: CombinedDocument,
    format: OutputFormat
) -> Union[str, bytes]:
    """
    フォーマット固有の後処理

    Markdown:
    - 目次の生成
    - リンクの検証
    - コードブロックの整形

    PDF:
    - ページ番号
    - ヘッダー/フッター
    - ブックマーク
    """
```

## テスト要件

### 統合テスト

```python
def test_build_complete_document():
    """完全なドキュメントのビルド"""
    request = BuildRequest(
        main_selector="main.content",
        ordered_files=[
            OrderedFile(1, Path("index.html"), "Introduction", 0),
            OrderedFile(2, Path("guide.html"), "User Guide", 0),
            OrderedFile(3, Path("api.html"), "API Reference", 0),
        ],
        format=OutputFormat.MARKDOWN
    )

    result = service.build(request)

    assert result.format == OutputFormat.MARKDOWN
    assert result.page_count == 3
    assert "# Introduction" in result.content
    assert "# User Guide" in result.content
    assert "# API Reference" in result.content
```

## 実装のポイント

1. **エラー処理**
   - ファイルが見つからない場合
   - セレクタがマッチしない場合
   - 変換エラー

2. **パフォーマンス**
   - 大きなドキュメントでのメモリ使用
   - ストリーミング処理の検討

3. **品質保証**
   - 画像の処理（Base64埋め込み or 外部参照）
   - コードブロックの構文ハイライト
   - テーブルの適切な変換

## 受け入れ基準

- [ ] 順序通りにドキュメントが結合される
- [ ] 階層構造が保持される
- [ ] 内部リンクが正しく更新される
- [ ] 両フォーマット（MD/PDF）で出力可能

## 推定工数

5-6時間

## 依存関係

- [08. Markdownコンバーターの実装](20250706-08-implement-markdown-converter.md)
- [09. PDFコンバーターの実装](20250706-09-implement-pdf-converter.md)

## 次のタスク

→ [11. Autoコマンドの実装](20250706-11-implement-auto-command.md)

## AIへの実装依頼例

```
BuildServiceを実装してください。

要件：
1. 複数のHTMLファイルからコンテンツを抽出
2. 指定された順序で結合
3. Markdown/PDF形式で出力

重要な処理：
- 見出しレベルの調整（階層に応じて）
- 相対リンクの解決
- 不要な要素（nav, aside等）の除去

テストケースを参考に実装してください。
```
