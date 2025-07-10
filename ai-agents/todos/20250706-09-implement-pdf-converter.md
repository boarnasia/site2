# Todo 09: PDFコンバーターの実装

## 目的

HTMLコンテンツをPDF形式に変換する。

## 背景

前プロジェクト（site2pdf）ではPlaywrightを使用してPDF生成を行っていた。
この実績を活かしつつ、より洗練された実装を行う。

## 成果物

1. **PDFConverter実装**
   - `src/site2/adapters/converters/pdf_converter.py`
   - HTML→PDF変換ロジック

## 実装詳細

### 基本的なPDFコンバーター

```python
from playwright.sync_api import sync_playwright
import tempfile
from pathlib import Path
from typing import Union, List, Optional
import base64

class PDFConverter:
    """HTML to PDF コンバーター"""

    def __init__(self, options: dict = None):
        self.options = options or {}
        self.default_options = {
            'format': 'A4',
            'margin': {
                'top': '20mm',
                'right': '20mm',
                'bottom': '20mm',
                'left': '20mm'
            },
            'print_background': True,
            'display_header_footer': True,
            'header_template': self._default_header_template(),
            'footer_template': self._default_footer_template(),
        }

    def _default_header_template(self) -> str:
        """デフォルトのヘッダーテンプレート"""
        return '''
        <div style="font-size: 10px; text-align: center; width: 100%;">
            <span class="title"></span>
        </div>
        '''

    def _default_footer_template(self) -> str:
        """デフォルトのフッターテンプレート"""
        return '''
        <div style="font-size: 10px; text-align: center; width: 100%;">
            <span class="pageNumber"></span> / <span class="totalPages"></span>
        </div>
        '''

    def convert(self, html_content: str) -> bytes:
        """HTMLをPDFに変換"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            try:
                # 新しいページを作成
                page = browser.new_page()

                # HTMLをロード
                page.set_content(html_content, wait_until='networkidle')

                # PDFオプションをマージ
                pdf_options = {**self.default_options, **self.options}

                # PDFを生成
                pdf_bytes = page.pdf(**pdf_options)

                return pdf_bytes

            finally:
                browser.close()
```

### 複数ページの結合

```python
class MultiPagePDFConverter(PDFConverter):
    """複数のHTMLページをPDFに変換"""

    def convert_multiple(
        self,
        html_pages: List[str],
        merge: bool = True
    ) -> Union[bytes, List[bytes]]:
        """
        複数のHTMLページをPDFに変換

        Args:
            html_pages: HTMLコンテンツのリスト
            merge: Trueの場合、1つのPDFに結合
        """
        if merge:
            # 1つのHTMLに結合してから変換
            combined_html = self._combine_html(html_pages)
            return self.convert(combined_html)
        else:
            # 個別に変換
            pdf_list = []
            for html in html_pages:
                pdf_list.append(self.convert(html))
            return pdf_list

    def _combine_html(self, html_pages: List[str]) -> str:
        """複数のHTMLを1つに結合"""
        combined_parts = [
            '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    @media print {
                        .page-break {
                            page-break-after: always;
                        }
                    }
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                                     Roboto, "Helvetica Neue", Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                    }
                    pre {
                        background-color: #f4f4f4;
                        padding: 10px;
                        border-radius: 4px;
                        overflow-x: auto;
                    }
                    code {
                        background-color: #f4f4f4;
                        padding: 2px 4px;
                        border-radius: 2px;
                    }
                    table {
                        border-collapse: collapse;
                        width: 100%;
                        margin: 15px 0;
                    }
                    th, td {
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                    }
                    th {
                        background-color: #f8f8f8;
                    }
                </style>
            </head>
            <body>
            '''
        ]

        for i, html in enumerate(html_pages):
            if i > 0:
                combined_parts.append('<div class="page-break"></div>')

            # bodyタグの中身だけを抽出
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            body_content = soup.body

            if body_content:
                combined_parts.append(str(body_content))
            else:
                combined_parts.append(html)

        combined_parts.append('</body></html>')

        return '\n'.join(combined_parts)
```

### 高度な機能

```python
class AdvancedPDFConverter(MultiPagePDFConverter):
    """高度なPDF変換機能"""

    def __init__(self, options: dict = None):
        super().__init__(options)
        self.toc_enabled = True
        self.bookmarks_enabled = True

    def convert_with_features(
        self,
        html_pages: List[str],
        titles: List[str],
        metadata: dict = None
    ) -> bytes:
        """
        目次とブックマーク付きでPDFを生成

        Args:
            html_pages: HTMLコンテンツのリスト
            titles: 各ページのタイトル
            metadata: PDFメタデータ
        """
        # 目次ページを生成
        if self.toc_enabled:
            toc_html = self._generate_toc(titles)
            html_pages = [toc_html] + html_pages
            titles = ["Table of Contents"] + titles

        # HTMLにアンカーを追加
        html_pages = self._add_anchors(html_pages, titles)

        # PDFを生成
        combined_html = self._combine_html(html_pages)

        # メタデータを設定
        if metadata:
            combined_html = self._add_metadata(combined_html, metadata)

        return self.convert(combined_html)

    def _generate_toc(self, titles: List[str]) -> str:
        """目次ページを生成"""
        toc_items = []
        for i, title in enumerate(titles):
            # ページ番号は1から開始（目次自体が0ページ目）
            page_num = i + 2
            toc_items.append(
                f'<li><a href="#page-{i+1}">{title}</a>'
                f'<span style="float: right;">{page_num}</span></li>'
            )

        return f'''
        <h1>Table of Contents</h1>
        <ul style="list-style: none; padding: 0;">
            {''.join(toc_items)}
        </ul>
        '''

    def _add_anchors(
        self,
        html_pages: List[str],
        titles: List[str]
    ) -> List[str]:
        """各ページにアンカーを追加"""
        anchored_pages = []

        for i, (html, title) in enumerate(zip(html_pages, titles)):
            # ページの先頭にアンカーを追加
            anchor = f'<a id="page-{i}"></a>'
            anchored_html = f'{anchor}\n{html}'
            anchored_pages.append(anchored_html)

        return anchored_pages
```

### 画像の処理

```python
def _process_images(self, html: str, base_path: Path) -> str:
    """画像をBase64エンコードして埋め込み"""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, 'html.parser')

    for img in soup.find_all('img'):
        src = img.get('src', '')

        if src.startswith('data:'):
            # すでにBase64エンコード済み
            continue

        if src.startswith(('http://', 'https://')):
            # 外部画像はそのまま（または取得して埋め込み）
            continue

        # ローカル画像をBase64に変換
        img_path = base_path / src
        if img_path.exists():
            with open(img_path, 'rb') as f:
                img_data = f.read()

            # MIMEタイプを推定
            import mimetypes
            mime_type = mimetypes.guess_type(str(img_path))[0] or 'image/png'

            # Base64エンコード
            b64_data = base64.b64encode(img_data).decode('utf-8')
            img['src'] = f'data:{mime_type};base64,{b64_data}'

    return str(soup)
```

## テスト要件

### テストケース

```python
def test_convert_simple_html():
    """シンプルなHTMLのPDF変換"""
    converter = PDFConverter()
    html = "<h1>Test</h1><p>Content</p>"

    pdf_bytes = converter.convert(html)

    assert pdf_bytes.startswith(b'%PDF')
    assert len(pdf_bytes) > 1000  # 最小サイズ

def test_convert_with_custom_options():
    """カスタムオプションでのPDF変換"""
    options = {
        'format': 'Letter',
        'landscape': True
    }
    converter = PDFConverter(options)

    pdf_bytes = converter.convert("<p>Test</p>")
    assert pdf_bytes is not None

def test_multiple_pages_with_toc():
    """目次付き複数ページのPDF生成"""
    converter = AdvancedPDFConverter()

    pages = [
        "<h1>Chapter 1</h1><p>Content 1</p>",
        "<h1>Chapter 2</h1><p>Content 2</p>"
    ]
    titles = ["Chapter 1", "Chapter 2"]

    pdf_bytes = converter.convert_with_features(pages, titles)
    assert pdf_bytes is not None
```

## 実装のポイント

1. **Playwrightの設定**
   - ヘッドレスモード
   - タイムアウト設定
   - エラーハンドリング

2. **CSSの考慮**
   - 印刷用CSS（@media print）
   - ページ区切り
   - 余白設定

3. **パフォーマンス**
   - ブラウザの再利用
   - 並列処理の検討

4. **品質**
   - フォントの埋め込み
   - 画像の解像度
   - リンクの処理

## 受け入れ基準

- [ ] 基本的なHTML→PDF変換が動作
- [ ] 複数ページの結合が可能
- [ ] 目次とページ番号が正しく表示
- [ ] 画像が適切に埋め込まれる

## 推定工数

4-5時間

## 依存関係

- Playwright のインストールが必要
- [04. HTMLパーサーの実装](20250706-04-implement-html-parser.md)

## 次のタスク

→ [10. Buildサービスの実装](20250706-10-implement-build-service.md)
