# Todo 08: Markdownコンバーターの実装

## 目的

HTMLコンテンツを適切なMarkdown形式に変換する。

## 背景

BeautifulSoupで抽出したHTMLコンテンツを、読みやすいMarkdownに変換する必要がある。
画像、リンク、コードブロック、テーブルなどの要素を適切に処理する。

## 成果物

1. **MarkdownConverter実装**
   - `src/site2/adapters/converters/markdown_converter.py`
   - HTML→Markdown変換ロジック

## 実装詳細

### 基本的な変換ルール

```python
class MarkdownConverter:
    """HTML to Markdown コンバーター"""

    def __init__(self):
        self.converters = {
            'h1': self._convert_heading,
            'h2': self._convert_heading,
            'h3': self._convert_heading,
            'h4': self._convert_heading,
            'h5': self._convert_heading,
            'h6': self._convert_heading,
            'p': self._convert_paragraph,
            'a': self._convert_link,
            'img': self._convert_image,
            'strong': self._convert_strong,
            'b': self._convert_strong,
            'em': self._convert_emphasis,
            'i': self._convert_emphasis,
            'code': self._convert_code,
            'pre': self._convert_pre,
            'ul': self._convert_list,
            'ol': self._convert_list,
            'li': self._convert_list_item,
            'blockquote': self._convert_blockquote,
            'table': self._convert_table,
            'hr': self._convert_hr,
        }

    def convert(self, element: Tag) -> str:
        """HTML要素をMarkdownに変換"""
        if isinstance(element, str):
            return element

        # テキストノード
        if element.name is None:
            return str(element)

        # 特定のタグの変換
        if element.name in self.converters:
            return self.converters[element.name](element)

        # デフォルト：子要素を再帰的に変換
        return self._convert_children(element)
```

### 各要素の変換実装

```python
def _convert_heading(self, element: Tag) -> str:
    """見出しの変換"""
    level = int(element.name[1])  # h1 -> 1
    text = self._convert_children(element).strip()
    return f"{'#' * level} {text}\n\n"

def _convert_paragraph(self, element: Tag) -> str:
    """段落の変換"""
    text = self._convert_children(element).strip()
    return f"{text}\n\n" if text else ""

def _convert_link(self, element: Tag) -> str:
    """リンクの変換"""
    text = self._convert_children(element).strip()
    href = element.get('href', '')

    if not text:
        text = href

    # 画像リンクの場合
    if element.find('img'):
        return self._convert_children(element)

    return f"[{text}]({href})"

def _convert_image(self, element: Tag) -> str:
    """画像の変換"""
    alt = element.get('alt', '')
    src = element.get('src', '')
    title = element.get('title', '')

    if title:
        return f'![{alt}]({src} "{title}")'
    else:
        return f'![{alt}]({src})'

def _convert_code(self, element: Tag) -> str:
    """インラインコードの変換"""
    code = element.get_text()
    return f"`{code}`"

def _convert_pre(self, element: Tag) -> str:
    """コードブロックの変換"""
    code_elem = element.find('code')

    if code_elem:
        # 言語の検出
        classes = code_elem.get('class', [])
        language = ''
        for cls in classes:
            if cls.startswith('language-'):
                language = cls.replace('language-', '')
                break

        code = code_elem.get_text()
        return f"```{language}\n{code}\n```\n\n"
    else:
        # <pre>のみの場合
        code = element.get_text()
        return f"```\n{code}\n```\n\n"
```

### リストの変換

```python
def _convert_list(self, element: Tag) -> str:
    """リストの変換"""
    items = []
    list_type = element.name  # 'ul' or 'ol'

    for i, li in enumerate(element.find_all('li', recursive=False)):
        marker = f"{i + 1}." if list_type == 'ol' else "-"
        item_text = self._convert_list_item(li, marker)
        items.append(item_text)

    return '\n'.join(items) + '\n\n'

def _convert_list_item(self, element: Tag, marker: str = '-') -> str:
    """リストアイテムの変換"""
    # ネストされたリストを処理
    nested_lists = []
    for child in element.find_all(['ul', 'ol'], recursive=False):
        nested_lists.append(child)
        child.extract()  # 一時的に削除

    # テキストコンテンツを取得
    text = self._convert_children(element).strip()
    result = f"{marker} {text}"

    # ネストされたリストを追加
    if nested_lists:
        for nested in nested_lists:
            nested_text = self._convert_list(nested)
            # インデントを追加
            indented = '\n'.join(f"  {line}" for line in nested_text.split('\n') if line)
            result += f"\n{indented}"

    return result
```

### テーブルの変換

```python
def _convert_table(self, element: Tag) -> str:
    """テーブルの変換"""
    rows = []

    # ヘッダー行を探す
    thead = element.find('thead')
    if thead:
        header_row = thead.find('tr')
        if header_row:
            headers = [self._convert_children(th).strip()
                      for th in header_row.find_all(['th', 'td'])]
            rows.append('| ' + ' | '.join(headers) + ' |')
            rows.append('|' + '---|' * len(headers))

    # ボディ行
    tbody = element.find('tbody') or element
    for tr in tbody.find_all('tr'):
        # theadの行はスキップ
        if tr.parent.name == 'thead':
            continue

        cells = [self._convert_children(td).strip()
                for td in tr.find_all(['td', 'th'])]
        rows.append('| ' + ' | '.join(cells) + ' |')

    return '\n'.join(rows) + '\n\n' if rows else ''
```

### 特殊な処理

```python
def _handle_nested_formatting(self, element: Tag) -> str:
    """ネストされた書式設定を処理"""
    # 例: <strong><em>text</em></strong> -> ***text***
    result = self._convert_children(element)

    # 連続する書式記号を整理
    result = re.sub(r'\*{4,}', '***', result)  # ****text**** -> ***text***
    result = re.sub(r'_{3,}', '__', result)    # ___text___ -> __text__

    return result

def _escape_markdown_chars(self, text: str) -> str:
    """Markdown特殊文字をエスケープ"""
    # ただし、すでにMarkdown記法の一部である場合は除く
    chars_to_escape = ['\\', '`', '*', '_', '{', '}', '[', ']',
                      '(', ')', '#', '+', '-', '.', '!']

    for char in chars_to_escape:
        # 簡易的なエスケープ（より洗練された実装が必要）
        text = text.replace(char, f'\\{char}')

    return text
```

### 高度な機能

```python
class AdvancedMarkdownConverter(MarkdownConverter):
    """拡張Markdown機能"""

    def __init__(self, options: dict = None):
        super().__init__()
        self.options = options or {}
        self.footnotes = []
        self.heading_ids = {}

    def convert_with_toc(self, element: Tag) -> str:
        """目次付きで変換"""
        # まず通常の変換
        content = self.convert(element)

        # 見出しを収集
        toc = self._generate_toc(element)

        # 目次を先頭に追加
        return f"{toc}\n\n{content}"

    def _generate_toc(self, element: Tag) -> str:
        """目次を生成"""
        headings = element.find_all(['h1', 'h2', 'h3', 'h4'])
        toc_lines = ["## Table of Contents\n"]

        for heading in headings:
            level = int(heading.name[1])
            text = heading.get_text(strip=True)
            # アンカーリンクを生成
            anchor = self._slugify(text)
            indent = "  " * (level - 1)
            toc_lines.append(f"{indent}- [{text}](#{anchor})")

        return '\n'.join(toc_lines)

    def _slugify(self, text: str) -> str:
        """テキストをURLフレンドリーなスラッグに変換"""
        # 簡易実装
        slug = text.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
```

## テスト要件

### テストケース

```python
def test_convert_basic_html():
    """基本的なHTML要素の変換"""
    html = """
    <h1>Title</h1>
    <p>This is a <strong>paragraph</strong> with <em>emphasis</em>.</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
    </ul>
    """

    expected = """# Title

This is a **paragraph** with *emphasis*.

- Item 1
- Item 2

"""

    converter = MarkdownConverter()
    result = converter.convert(BeautifulSoup(html, 'html.parser'))
    assert result.strip() == expected.strip()

def test_convert_nested_lists():
    """ネストされたリストの変換"""
    html = """
    <ul>
        <li>Parent 1
            <ul>
                <li>Child 1.1</li>
                <li>Child 1.2</li>
            </ul>
        </li>
        <li>Parent 2</li>
    </ul>
    """

    converter = MarkdownConverter()
    result = converter.convert(BeautifulSoup(html, 'html.parser'))

    assert "- Parent 1" in result
    assert "  - Child 1.1" in result
    assert "  - Child 1.2" in result
```

## 実装のポイント

1. **空白の処理**
   - HTMLの改行・空白とMarkdownの改行の違い
   - 適切な段落区切り

2. **ネストされた要素**
   - リストの入れ子
   - 書式の入れ子（**_text_**）

3. **特殊なケース**
   - 画像のみのリンク
   - 空の要素
   - 壊れたHTML

4. **拡張性**
   - カスタム変換ルールの追加
   - プラグイン機構

## 受け入れ基準

- [ ] 基本的なHTML要素を正しく変換
- [ ] ネストされた構造を保持
- [ ] 特殊文字を適切にエスケープ
- [ ] 生成されたMarkdownが有効

## 推定工数

4-5時間

## 依存関係

- [04. HTMLパーサーの実装](20250706-04-implement-html-parser.md)

## 次のタスク

→ [09. PDFコンバーターの実装](20250706-09-implement-pdf-converter.md)
