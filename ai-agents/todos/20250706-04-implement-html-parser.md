# Todo 04: HTMLパーサーの実装

## 目的

HTMLファイルを解析して、構造化されたデータとして扱えるようにする。Geminiを使用したコンテンツ検出機能の基盤となる。

## 背景

BeautifulSoup4を使用してHTMLを解析し、各サービスが必要とする機能を提供する共通パーサーを実装する。`examples/think_page_gemini/`の実装を参考に、Gemini APIとの連携を考慮した設計とする。

## 成果物

1. **HTMLParserサービス**
   - `src/site2/core/services/html_parser.py`
   - BeautifulSoupのラッパー
   - HTMLParserProtocolの実装

2. **HTMLAnalyzerサービス**
   - `src/site2/core/services/html_analyzer.py`
   - HTML構造解析機能
   - HTMLAnalyzerProtocolの実装

3. **EncodingDetectorサービス**
   - `src/site2/core/services/encoding_detector.py`
   - エンコーディング検出機能
   - EncodingDetectorProtocolの実装

## 実装詳細

### 1. HTMLParser実装

```python
# src/site2/core/services/html_parser.py
from pathlib import Path
from typing import Optional, List
import time
from bs4 import BeautifulSoup, Tag
from loguru import logger

from ..ports.parser_contracts import (
    HTMLParserProtocol,
    ParseRequest,
    ParseResult,
    TextExtractionRequest,
    TextExtractionResult,
    SelectorSearchRequest,
    SelectorSearchResult,
    ParseError,
    SelectorError,
)
from .encoding_detector import EncodingDetector

class HTMLParser:
    """HTML解析サービス"""

    def __init__(self, parser: str = "html.parser"):
        self.parser = parser
        self.encoding_detector = EncodingDetector()

    def parse(self, request: ParseRequest) -> ParseResult:
        """HTMLファイルをパース"""
        start_time = time.time()
        warnings = []

        try:
            # エンコーディング検出
            encoding = request.encoding
            if not encoding:
                encoding = self.encoding_detector.detect_encoding(request.file_path)
                logger.info(f"Detected encoding: {encoding} for {request.file_path}")

            # ファイル読み込み
            with open(request.file_path, 'r', encoding=encoding) as f:
                html_content = f.read()

            # BeautifulSoupでパース
            soup = self.parse_string(html_content)

            # 解析時間
            parse_time = time.time() - start_time

            return ParseResult(
                file_path=request.file_path,
                soup=soup,
                encoding=encoding,
                parse_time_seconds=parse_time,
                warnings=warnings
            )

        except Exception as e:
            logger.error(f"Failed to parse {request.file_path}: {str(e)}")
            raise ParseError(f"Failed to parse HTML: {str(e)}")

    def parse_string(self, html: str) -> BeautifulSoup:
        """HTML文字列をパース"""
        if not html:
            raise ValueError("HTML string cannot be empty")

        try:
            return BeautifulSoup(html, self.parser)
        except Exception as e:
            raise ParseError(f"Failed to parse HTML string: {str(e)}")

    def extract_text(self, request: TextExtractionRequest) -> TextExtractionResult:
        """要素からテキストを抽出（Gemini実装参考）"""
        element = request.element

        # スクリプトとスタイルを除去（Geminiの前処理と同様）
        if request.remove_scripts:
            for tag in element.find_all(['script', 'noscript']):
                tag.decompose()

        if request.remove_styles:
            for tag in element.find_all(['style']):
                tag.decompose()
            # style属性も削除
            for tag in element.find_all():
                if 'style' in tag.attrs:
                    del tag.attrs['style']

        # テキスト抽出
        text = element.get_text(separator='\n', strip=True)

        # 空白文字のクリーンアップ
        if request.clean_whitespace:
            lines = [line.strip() for line in text.split('\n')]
            lines = [line for line in lines if line]
            text = '\n'.join(lines)

        return TextExtractionResult(
            original_element=element,
            extracted_text=text,
            text_length=len(text),
            cleaned=request.clean_whitespace
        )

    def find_by_selectors(self, request: SelectorSearchRequest) -> SelectorSearchResult:
        """複数のセレクタから要素を検索"""
        soup = request.soup
        elements = []
        matched_selector = None

        try:
            if request.find_all:
                # 全件検索モード
                for selector in request.selectors:
                    found = soup.select(selector)
                    if found:
                        elements.extend(found)
                        if not matched_selector:
                            matched_selector = selector

                return SelectorSearchResult(
                    matched_selector=matched_selector,
                    elements=elements,
                    search_method="all_matches"
                )
            else:
                # 最初にマッチしたものを返す
                for selector in request.selectors:
                    element = soup.select_one(selector)
                    if element:
                        return SelectorSearchResult(
                            matched_selector=selector,
                            elements=[element],
                            search_method="first_match"
                        )

                return SelectorSearchResult(
                    matched_selector=None,
                    elements=[],
                    search_method="first_match"
                )

        except Exception as e:
            raise SelectorError(f"Selector search failed: {str(e)}")
```

### 2. HTMLAnalyzer実装

```python
# src/site2/core/services/html_analyzer.py
from bs4 import BeautifulSoup, Tag
from typing import Dict

from ..ports.parser_contracts import (
    HTMLAnalyzerProtocol,
    HTMLStructureAnalysis,
    HTMLMetadata,
    AnalysisError,
)

class HTMLAnalyzer:
    """HTML構造解析サービス"""

    def analyze_structure(self, soup: BeautifulSoup) -> HTMLStructureAnalysis:
        """HTML構造を解析"""
        try:
            # 見出しカウント
            heading_count = {}
            for level in range(1, 7):
                h_tags = soup.find_all(f'h{level}')
                if h_tags:
                    heading_count[f'h{level}'] = len(h_tags)

            return HTMLStructureAnalysis(
                has_main=bool(soup.find('main')),
                has_article=bool(soup.find('article')),
                has_nav=bool(soup.find('nav')),
                has_header=bool(soup.find('header')),
                has_footer=bool(soup.find('footer')),
                heading_count=heading_count,
                paragraph_count=len(soup.find_all('p')),
                link_count=len(soup.find_all('a')),
                image_count=len(soup.find_all('img')),
                table_count=len(soup.find_all('table')),
                list_count=len(soup.find_all(['ul', 'ol']))
            )
        except Exception as e:
            raise AnalysisError(f"Structure analysis failed: {str(e)}")

    def extract_metadata(self, soup: BeautifulSoup) -> HTMLMetadata:
        """HTMLメタデータを抽出"""
        meta_tags = {}
        og_tags = {}

        # タイトル
        title_tag = soup.find('title')
        title = title_tag.string if title_tag else None

        # メタタグ
        for meta in soup.find_all('meta'):
            # name属性
            if meta.get('name'):
                name = meta['name'].lower()
                content = meta.get('content', '')
                meta_tags[name] = content

            # property属性（OGタグ）
            if meta.get('property'):
                prop = meta['property']
                if prop.startswith('og:'):
                    og_tags[prop] = meta.get('content', '')

        # 一般的なメタデータを抽出
        description = meta_tags.get('description')
        keywords = meta_tags.get('keywords')
        author = meta_tags.get('author')

        # 言語
        html_tag = soup.find('html')
        language = html_tag.get('lang') if html_tag else None

        return HTMLMetadata(
            title=title,
            description=description,
            keywords=keywords,
            author=author,
            language=language,
            meta_tags=meta_tags,
            og_tags=og_tags
        )

    def calculate_text_density(self, element: Tag) -> float:
        """テキスト密度を計算（テキスト/HTML比）"""
        if not element:
            return 0.0

        # テキスト長
        text = element.get_text(strip=True)
        text_length = len(text)

        # HTML長
        html = str(element)
        html_length = len(html)

        if html_length == 0:
            return 0.0

        return text_length / html_length
```

### 3. EncodingDetector実装

```python
# src/site2/core/services/encoding_detector.py
from pathlib import Path
import chardet
from loguru import logger

from ..ports.parser_contracts import (
    EncodingDetectorProtocol,
    DetectionError,
)

class EncodingDetector:
    """エンコーディング検出サービス"""

    # エンコーディングのエイリアス
    ENCODING_ALIASES = {
        'ascii': 'utf-8',
        'ISO-8859-1': 'latin-1',
        'Windows-1252': 'cp1252',
        'shift-jis': 'shift_jis',
        'euc-jp': 'euc_jp',
    }

    def detect_encoding(self, file_path: Path) -> str:
        """ファイルのエンコーディングを検出"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # 最初の10KBを読み込み
            with open(file_path, 'rb') as f:
                raw_data = f.read(10240)

            return self.detect_encoding_from_bytes(raw_data)

        except Exception as e:
            logger.error(f"Encoding detection failed for {file_path}: {str(e)}")
            raise DetectionError(f"Failed to detect encoding: {str(e)}")

    def detect_encoding_from_bytes(self, data: bytes) -> str:
        """バイト列からエンコーディングを検出"""
        if not data:
            raise ValueError("Data cannot be empty")

        try:
            # chardetで検出
            result = chardet.detect(data)

            if not result or not result.get('encoding'):
                logger.warning("chardet failed to detect encoding, using utf-8")
                return 'utf-8'

            encoding = result['encoding']
            confidence = result.get('confidence', 0)

            logger.debug(f"Detected encoding: {encoding} (confidence: {confidence})")

            # エイリアスを正規化
            normalized = self.ENCODING_ALIASES.get(encoding, encoding)

            # 信頼度が低い場合は警告
            if confidence < 0.7:
                logger.warning(f"Low confidence encoding detection: {encoding} ({confidence})")

            return normalized.lower()

        except Exception as e:
            raise DetectionError(f"Encoding detection failed: {str(e)}")
```

### 4. Gemini連携を考慮した前処理機能

```python
# src/site2/core/services/html_preprocessor.py
from bs4 import BeautifulSoup
import re

class HTMLPreprocessor:
    """Gemini API用のHTML前処理（think_page_gemini参考）"""

    @staticmethod
    def preprocess_for_llm(soup: BeautifulSoup, max_length: int = 50000) -> str:
        """LLM用にHTMLを前処理"""
        # クローンを作成（元のsoupを変更しない）
        soup_copy = BeautifulSoup(str(soup), 'html.parser')

        # 不要な要素を削除
        for tag in soup_copy.find_all(['script', 'style', 'noscript', 'iframe']):
            tag.decompose()

        # コメントを削除
        for comment in soup_copy.find_all(string=lambda text: isinstance(text, str) and '<!--' in text):
            comment.extract()

        # 属性を簡略化（id, class, href以外を削除）
        for tag in soup_copy.find_all():
            attrs_to_keep = {}
            if 'id' in tag.attrs:
                attrs_to_keep['id'] = tag.attrs['id']
            if 'class' in tag.attrs:
                attrs_to_keep['class'] = ' '.join(tag.attrs['class'])
            if tag.name == 'a' and 'href' in tag.attrs:
                attrs_to_keep['href'] = tag.attrs['href']
            tag.attrs = attrs_to_keep

        # HTMLを文字列化
        html_str = str(soup_copy.prettify())

        # 連続する空白行を削除
        html_str = re.sub(r'\n\s*\n', '\n', html_str)

        # 最大長を超える場合は切り詰め
        if len(html_str) > max_length:
            html_str = html_str[:max_length] + "\n<!-- truncated -->"

        return html_str
```

## テスト要件

### 単体テスト

- [ ] HTMLParserのテスト
  - [ ] 各種エンコーディングのHTML（UTF-8, Shift_JIS, EUC-JP）
  - [ ] 壊れたHTML
  - [ ] 大きなHTMLファイル
  - [ ] 空のHTML

- [ ] HTMLAnalyzerのテスト
  - [ ] 構造解析の正確性
  - [ ] メタデータ抽出
  - [ ] テキスト密度計算

- [ ] EncodingDetectorのテスト
  - [ ] 各種エンコーディングの検出
  - [ ] エイリアスの正規化
  - [ ] エラーケース

- [ ] HTMLPreprocessorのテスト
  - [ ] 不要要素の削除
  - [ ] 属性の簡略化
  - [ ] 最大長での切り詰め

### 統合テスト

- [ ] パイプライン全体での動作確認
- [ ] 実際のWebサイトのHTMLでのテスト

## 受け入れ基準

- [ ] 主要なエンコーディングに対応（UTF-8, Shift_JIS, EUC-JP, CP932）
- [ ] 壊れたHTMLでもクラッシュしない
- [ ] テキスト抽出が適切（スクリプト・スタイル除去）
- [ ] Gemini API用の前処理が機能する
- [ ] パフォーマンスが実用的（1MBのHTMLを1秒以内に処理）

## 推定工数

3-4時間

## 依存関係

- BeautifulSoup4
- chardet
- loguru

## 次のタスク

→ [05. Detect:Mainサービスの実装](20250706-05-implement-detect-main.md)

## AIへの実装依頼例

```
以下の契約に基づいてHTMLパーサーを実装してください：

契約定義:
- src/site2/core/ports/parser_contracts.py

参考実装:
- examples/think_page_gemini/think_page_gemini.py（前処理部分）

要件:
1. HTMLParserProtocolを実装
2. HTMLAnalyzerProtocolを実装
3. EncodingDetectorProtocolを実装
4. Gemini用の前処理機能を追加
5. 適切なエラーハンドリング
6. ログ出力（loguru使用）

テストケース:
- tests/unit/core/services/test_html_parser.py
- tests/unit/core/services/test_html_analyzer.py
- tests/unit/core/services/test_encoding_detector.py

制約:
- BeautifulSoup4のhtml.parserを使用
- エンコーディング検出にはchardetを使用
- 大きなHTMLファイル（10MB以上）も処理可能
```
