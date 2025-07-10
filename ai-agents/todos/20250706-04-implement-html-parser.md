# Todo 04: HTMLパーサーの実装

## 目的

HTMLファイルを解析して、構造化されたデータとして扱えるようにする。

## 背景

BeautifulSoup4を使用してHTMLを解析し、各サービスが必要とする機能を提供する共通パーサーを実装する。

## 成果物

1. **HTMLParserサービス**
   - `src/site2/core/services/html_parser.py`
   - BeautifulSoupのラッパー

2. **パーサープロトコル**
   - `src/site2/core/ports/parser_contracts.py`
   - パーサーインターフェース

## 実装詳細

### 1. パーサー契約

```python
# src/site2/core/ports/parser_contracts.py
from typing import Protocol, Optional, List
from bs4 import BeautifulSoup, Tag

class HTMLParserProtocol(Protocol):
    """HTMLパーサーの契約"""

    def parse(self, file_path: Path) -> BeautifulSoup:
        """HTMLファイルをパース"""
        ...

    def parse_string(self, html: str) -> BeautifulSoup:
        """HTML文字列をパース"""
        ...

    def extract_text(self, element: Tag) -> str:
        """要素からテキストを抽出"""
        ...

    def find_by_selectors(
        self,
        soup: BeautifulSoup,
        selectors: List[str]
    ) -> Optional[Tag]:
        """複数のセレクタから最初にマッチする要素を取得"""
        ...
```

### 2. HTMLParser実装

```python
# src/site2/core/services/html_parser.py
import chardet
from bs4 import BeautifulSoup, Tag
from pathlib import Path
from typing import Optional, List

class HTMLParser:
    """HTML解析サービス"""

    def __init__(self, parser: str = "html.parser"):
        self.parser = parser

    def parse(self, file_path: Path) -> BeautifulSoup:
        """
        HTMLファイルをパース

        1. エンコーディング検出
        2. ファイル読み込み
        3. BeautifulSoupでパース
        """
        # エンコーディング検出
        encoding = self._detect_encoding(file_path)

        # ファイル読み込み
        with open(file_path, 'r', encoding=encoding) as f:
            html_content = f.read()

        return self.parse_string(html_content)

    def parse_string(self, html: str) -> BeautifulSoup:
        """HTML文字列をパース"""
        return BeautifulSoup(html, self.parser)

    def _detect_encoding(self, file_path: Path) -> str:
        """ファイルのエンコーディングを検出"""
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # 最初の10KB

        # chardetで検出
        result = chardet.detect(raw_data)
        encoding = result['encoding'] or 'utf-8'

        # 一般的なエイリアスを正規化
        encoding_map = {
            'ascii': 'utf-8',
            'ISO-8859-1': 'latin-1',
        }

        return encoding_map.get(encoding, encoding)

    def extract_text(self, element: Tag) -> str:
        """
        要素からテキストを抽出

        - 改行を適切に処理
        - 余分な空白を除去
        - スクリプト/スタイルを除外
        """
        if not element:
            return ""

        # スクリプトとスタイルを除去
        for tag in element.find_all(['script', 'style']):
            tag.decompose()

        # テキスト抽出
        text = element.get_text(separator='\n', strip=True)

        # 余分な空白を正規化
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]

        return '\n'.join(lines)

    def find_by_selectors(
        self,
        soup: BeautifulSoup,
        selectors: List[str]
    ) -> Optional[Tag]:
        """複数のセレクタから最初にマッチする要素を取得"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element
        return None
```

### 3. 拡張機能

```python
class HTMLAnalyzer:
    """HTML構造解析ヘルパー"""

    def __init__(self, parser: HTMLParserProtocol):
        self.parser = parser

    def analyze_structure(self, soup: BeautifulSoup) -> dict:
        """HTML構造を解析"""
        return {
            'has_main': bool(soup.find('main')),
            'has_article': bool(soup.find('article')),
            'has_nav': bool(soup.find('nav')),
            'heading_count': len(soup.find_all(['h1', 'h2', 'h3'])),
            'paragraph_count': len(soup.find_all('p')),
            'link_count': len(soup.find_all('a')),
        }

    def extract_metadata(self, soup: BeautifulSoup) -> dict:
        """メタデータを抽出"""
        metadata = {}

        # タイトル
        title_tag = soup.find('title')
        metadata['title'] = title_tag.string if title_tag else None

        # メタタグ
        for meta in soup.find_all('meta'):
            if meta.get('name'):
                metadata[meta['name']] = meta.get('content', '')
            elif meta.get('property'):
                metadata[meta['property']] = meta.get('content', '')

        return metadata

    def calculate_text_density(self, element: Tag) -> float:
        """テキスト密度を計算（テキスト/HTML比）"""
        if not element:
            return 0.0

        text_length = len(self.parser.extract_text(element))
        html_length = len(str(element))

        return text_length / html_length if html_length > 0 else 0.0
```

## テスト要件

### 単体テスト

- [ ] 各種エンコーディングのHTML
- [ ] 壊れたHTML
- [ ] 大きなHTMLファイル
- [ ] 特殊文字を含むHTML

### テストケース例

```python
def test_parse_utf8_html():
    """UTF-8エンコーディングのHTML"""
    parser = HTMLParser()
    soup = parser.parse(Path("test_utf8.html"))
    assert soup.title.string == "テストページ"

def test_extract_text_removes_scripts():
    """スクリプトタグを除外してテキスト抽出"""
    html = """
    <div>
        <p>Visible text</p>
        <script>console.log('invisible')</script>
        <style>p { color: red; }</style>
    </div>
    """
    parser = HTMLParser()
    soup = parser.parse_string(html)
    text = parser.extract_text(soup.div)
    assert text == "Visible text"
    assert "console.log" not in text
```

## 受け入れ基準

- [ ] 主要なエンコーディングに対応
- [ ] 壊れたHTMLでもクラッシュしない
- [ ] テキスト抽出が適切
- [ ] パフォーマンスが実用的

## 推定工数

2-3時間

## 依存関係

なし（基盤コンポーネント）

## 次のタスク

→ [05. Detect:Mainサービスの実装](20250706-05-implement-detect-main.md)
