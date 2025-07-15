# Execute Task 04: HTMLパーサーの実装

## Commander Role: タスク分析と設計

### 目的
HTMLファイルを解析する基盤サービスを実装します。これは後続のDetectサービスやGemini連携の基礎となります。

### 設計方針
1. **契約準拠**: `parser_contracts.py`に定義されたProtocolを厳密に実装
2. **Gemini連携考慮**: LLM用の前処理機能を含む
3. **モジュール分割**: 責務ごとにサービスを分離
4. **エラーハンドリング**: 適切な例外処理

## Worker Role: 実装手順

### Step 1: HTMLParserサービスの実装

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
    ExtractError,
)
from .encoding_detector import EncodingDetector


class HTMLParser:
    """HTML解析サービス

    BeautifulSoup4をラップし、契約に基づいたHTML解析機能を提供
    """

    def __init__(self, parser: str = "html.parser"):
        """
        Args:
            parser: BeautifulSoupのパーサー名（html.parser, lxml等）
        """
        self.parser = parser
        self.encoding_detector = EncodingDetector()

    def parse(self, request: ParseRequest) -> ParseResult:
        """HTMLファイルをパース

        Args:
            request: 解析要求

        Returns:
            ParseResult: 解析結果

        Raises:
            ParseError: 解析に失敗した場合
        """
        start_time = time.time()
        warnings = []

        try:
            # エンコーディング検出または指定されたものを使用
            encoding = request.encoding
            if not encoding:
                encoding = self.encoding_detector.detect_encoding(request.file_path)
                logger.info(f"Detected encoding: {encoding} for {request.file_path}")

            # ファイル読み込み
            try:
                with open(request.file_path, 'r', encoding=encoding) as f:
                    html_content = f.read()
            except UnicodeDecodeError:
                # フォールバック: バイナリで読み込んで別のエンコーディングを試す
                warnings.append(f"Failed to decode with {encoding}, trying fallback")
                with open(request.file_path, 'rb') as f:
                    raw_data = f.read()
                encoding = self.encoding_detector.detect_encoding_from_bytes(raw_data)
                html_content = raw_data.decode(encoding, errors='replace')
                warnings.append(f"Used fallback encoding: {encoding}")

            # BeautifulSoupでパース
            soup = self.parse_string(html_content)

            # 解析時間
            parse_time = time.time() - start_time

            logger.debug(f"Parsed {request.file_path} in {parse_time:.3f} seconds")

            return ParseResult(
                file_path=request.file_path,
                soup=soup,
                encoding=encoding,
                parse_time_seconds=parse_time,
                warnings=warnings
            )

        except FileNotFoundError:
            raise ParseError(f"File not found: {request.file_path}")
        except Exception as e:
            logger.error(f"Failed to parse {request.file_path}: {str(e)}")
            raise ParseError(f"Failed to parse HTML: {str(e)}")

    def parse_string(self, html: str) -> BeautifulSoup:
        """HTML文字列をパース

        Args:
            html: HTML文字列

        Returns:
            BeautifulSoup: パース結果

        Raises:
            ValueError: 空の文字列の場合
            ParseError: パースに失敗した場合
        """
        if not html:
            raise ValueError("HTML string cannot be empty")

        try:
            return BeautifulSoup(html, self.parser)
        except Exception as e:
            raise ParseError(f"Failed to parse HTML string: {str(e)}")

    def extract_text(self, request: TextExtractionRequest) -> TextExtractionResult:
        """要素からテキストを抽出

        Gemini実装を参考に、スクリプトやスタイルを除去してクリーンなテキストを抽出

        Args:
            request: テキスト抽出要求

        Returns:
            TextExtractionResult: 抽出結果

        Raises:
            ExtractError: 抽出に失敗した場合
        """
        try:
            element = request.element

            # 作業用のコピーを作成（元の要素を変更しない）
            element_copy = BeautifulSoup(str(element), self.parser)

            # スクリプトとスタイルを除去
            if request.remove_scripts:
                for tag in element_copy.find_all(['script', 'noscript']):
                    tag.decompose()

            if request.remove_styles:
                for tag in element_copy.find_all(['style']):
                    tag.decompose()
                # style属性も削除
                for tag in element_copy.find_all():
                    if 'style' in tag.attrs:
                        del tag.attrs['style']

            # テキスト抽出
            text = element_copy.get_text(separator='\n', strip=request.clean_whitespace)

            # 空白文字のクリーンアップ
            if request.clean_whitespace:
                # 連続する空白を単一スペースに
                import re
                text = re.sub(r'[ \t]+', ' ', text)
                # 連続する改行を最大2つに制限
                text = re.sub(r'\n{3,}', '\n\n', text)
                # 各行の前後の空白を削除
                lines = [line.strip() for line in text.split('\n')]
                # 空行を除去（ただし段落区切りは維持）
                result_lines = []
                prev_empty = False
                for line in lines:
                    if line:
                        result_lines.append(line)
                        prev_empty = False
                    elif not prev_empty:
                        result_lines.append('')
                        prev_empty = True
                text = '\n'.join(result_lines).strip()

            return TextExtractionResult(
                original_element=request.element,
                extracted_text=text,
                text_length=len(text),
                cleaned=request.clean_whitespace
            )

        except Exception as e:
            raise ExtractError(f"Failed to extract text: {str(e)}")

    def find_by_selectors(self, request: SelectorSearchRequest) -> SelectorSearchResult:
        """複数のセレクタから要素を検索

        Args:
            request: セレクタ検索要求

        Returns:
            SelectorSearchResult: 検索結果

        Raises:
            SelectorError: セレクタエラーの場合
        """
        soup = request.soup
        elements = []
        matched_selector = None

        try:
            if request.find_all:
                # 全件検索モード
                for selector in request.selectors:
                    try:
                        found = soup.select(selector)
                        if found:
                            elements.extend(found)
                            if not matched_selector:
                                matched_selector = selector
                    except Exception as e:
                        logger.warning(f"Invalid selector '{selector}': {str(e)}")
                        continue

                return SelectorSearchResult(
                    matched_selector=matched_selector,
                    elements=elements,
                    search_method="all_matches"
                )
            else:
                # 最初にマッチしたものを返す
                for selector in request.selectors:
                    try:
                        element = soup.select_one(selector)
                        if element:
                            return SelectorSearchResult(
                                matched_selector=selector,
                                elements=[element],
                                search_method="first_match"
                            )
                    except Exception as e:
                        logger.warning(f"Invalid selector '{selector}': {str(e)}")
                        continue

                # マッチしなかった場合
                return SelectorSearchResult(
                    matched_selector=None,
                    elements=[],
                    search_method="first_match"
                )

        except Exception as e:
            raise SelectorError(f"Selector search failed: {str(e)}")
```

### Step 2: HTMLAnalyzerサービスの実装

```python
# src/site2/core/services/html_analyzer.py

from bs4 import BeautifulSoup, Tag
from typing import Dict
from loguru import logger

from ..ports.parser_contracts import (
    HTMLAnalyzerProtocol,
    HTMLStructureAnalysis,
    HTMLMetadata,
    AnalysisError,
)


class HTMLAnalyzer:
    """HTML構造解析サービス

    HTMLの構造やメタデータを解析する機能を提供
    """

    def analyze_structure(self, soup: BeautifulSoup) -> HTMLStructureAnalysis:
        """HTML構造を解析

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            HTMLStructureAnalysis: 構造解析結果

        Raises:
            AnalysisError: 解析に失敗した場合
        """
        try:
            # 見出しカウント
            heading_count = {}
            for level in range(1, 7):
                h_tags = soup.find_all(f'h{level}')
                if h_tags:
                    heading_count[f'h{level}'] = len(h_tags)

            # 各要素のカウント
            analysis = HTMLStructureAnalysis(
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

            logger.debug(f"Structure analysis: {heading_count.get('h1', 0)} h1, "
                        f"{analysis.paragraph_count} paragraphs, "
                        f"{analysis.link_count} links")

            return analysis

        except Exception as e:
            raise AnalysisError(f"Structure analysis failed: {str(e)}")

    def extract_metadata(self, soup: BeautifulSoup) -> HTMLMetadata:
        """HTMLメタデータを抽出

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            HTMLMetadata: メタデータ

        Raises:
            AnalysisError: 抽出に失敗した場合
        """
        try:
            meta_tags = {}
            og_tags = {}

            # タイトル
            title_tag = soup.find('title')
            title = title_tag.string.strip() if title_tag and title_tag.string else None

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

            metadata = HTMLMetadata(
                title=title,
                description=description,
                keywords=keywords,
                author=author,
                language=language,
                meta_tags=meta_tags,
                og_tags=og_tags
            )

            logger.debug(f"Extracted metadata: title='{title}', lang='{language}'")

            return metadata

        except Exception as e:
            raise AnalysisError(f"Metadata extraction failed: {str(e)}")

    def calculate_text_density(self, element: Tag) -> float:
        """テキスト密度を計算（テキスト/HTML比）

        Args:
            element: 計算対象の要素

        Returns:
            float: テキスト密度（0.0-1.0）

        Raises:
            ValueError: 無効な要素の場合
        """
        if not element:
            return 0.0

        try:
            # テキスト長（空白を正規化）
            text = element.get_text(strip=True)
            text_length = len(text)

            # HTML長
            html = str(element)
            html_length = len(html)

            if html_length == 0:
                return 0.0

            density = text_length / html_length

            logger.debug(f"Text density: {density:.3f} (text: {text_length}, html: {html_length})")

            return density

        except Exception as e:
            raise ValueError(f"Failed to calculate text density: {str(e)}")
```

### Step 3: EncodingDetectorサービスの実装

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
    """エンコーディング検出サービス

    chardetを使用してファイルやバイト列のエンコーディングを検出
    """

    # エンコーディングのエイリアス
    ENCODING_ALIASES = {
        'ascii': 'utf-8',
        'ISO-8859-1': 'latin-1',
        'Windows-1252': 'cp1252',
        'shift-jis': 'shift_jis',
        'shift_jis': 'shift_jis',
        'sjis': 'shift_jis',
        'cp932': 'cp932',
        'euc-jp': 'euc_jp',
        'eucjp': 'euc_jp',
    }

    # 信頼度の閾値
    CONFIDENCE_THRESHOLD = 0.7

    def detect_encoding(self, file_path: Path) -> str:
        """ファイルのエンコーディングを検出

        Args:
            file_path: 検出対象のファイルパス

        Returns:
            str: 検出されたエンコーディング名

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            DetectionError: 検出に失敗した場合
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # ファイルサイズをチェック
            file_size = file_path.stat().st_size
            read_size = min(file_size, 10240)  # 最大10KB

            # 最初の部分を読み込み
            with open(file_path, 'rb') as f:
                raw_data = f.read(read_size)

            encoding = self.detect_encoding_from_bytes(raw_data)

            logger.info(f"Detected encoding for {file_path.name}: {encoding}")

            return encoding

        except Exception as e:
            logger.error(f"Encoding detection failed for {file_path}: {str(e)}")
            raise DetectionError(f"Failed to detect encoding: {str(e)}")

    def detect_encoding_from_bytes(self, data: bytes) -> str:
        """バイト列からエンコーディングを検出

        Args:
            data: 検出対象のバイト列

        Returns:
            str: 検出されたエンコーディング名

        Raises:
            ValueError: 空のデータの場合
            DetectionError: 検出に失敗した場合
        """
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

            logger.debug(f"Detected encoding: {encoding} (confidence: {confidence:.3f})")

            # エイリアスを正規化
            normalized = self.ENCODING_ALIASES.get(encoding.lower(), encoding)

            # 信頼度が低い場合
            if confidence < self.CONFIDENCE_THRESHOLD:
                logger.warning(f"Low confidence encoding detection: {encoding} ({confidence:.3f})")

                # 日本語エンコーディングの場合は追加チェック
                if normalized in ['shift_jis', 'euc_jp', 'cp932']:
                    # UTF-8として読めるか試す
                    try:
                        data.decode('utf-8')
                        logger.info("Successfully decoded as UTF-8, using UTF-8 instead")
                        return 'utf-8'
                    except UnicodeDecodeError:
                        pass

            return normalized.lower()

        except Exception as e:
            raise DetectionError(f"Encoding detection failed: {str(e)}")
```

### Step 4: HTMLPreprocessorの実装（Gemini連携用）

```python
# src/site2/core/services/html_preprocessor.py

from bs4 import BeautifulSoup, Comment
import re
from typing import Set, Optional
from loguru import logger


class HTMLPreprocessor:
    """Gemini API用のHTML前処理

    think_page_geminiの実装を参考に、LLM処理用にHTMLを最適化
    """

    # 保持する属性
    KEEP_ATTRIBUTES = {'id', 'class', 'href', 'src', 'alt'}

    # 削除する要素
    REMOVE_TAGS = {
        'script', 'style', 'noscript', 'iframe', 'embed', 'object',
        'video', 'audio', 'canvas', 'svg', 'map'
    }

    @classmethod
    def preprocess_for_llm(
        cls,
        soup: BeautifulSoup,
        max_length: int = 50000,
        keep_links: bool = True
    ) -> str:
        """LLM用にHTMLを前処理

        Args:
            soup: BeautifulSoupオブジェクト
            max_length: 最大文字数
            keep_links: リンクを保持するか

        Returns:
            str: 前処理されたHTML文字列
        """
        # クローンを作成（元のsoupを変更しない）
        soup_copy = BeautifulSoup(str(soup), 'html.parser')

        # 不要な要素を削除
        for tag_name in cls.REMOVE_TAGS:
            for tag in soup_copy.find_all(tag_name):
                tag.decompose()

        # コメントを削除
        for comment in soup_copy.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # 空のタグを削除
        cls._remove_empty_tags(soup_copy)

        # 属性を簡略化
        cls._simplify_attributes(soup_copy, keep_links)

        # HTMLを文字列化
        html_str = str(soup_copy.prettify())

        # 連続する空白行を削除
        html_str = re.sub(r'\n\s*\n\s*\n', '\n\n', html_str)

        # インデントを簡略化（2スペースに統一）
        lines = []
        for line in html_str.split('\n'):
            # インデントレベルを計算
            stripped = line.lstrip()
            if stripped:
                indent_level = (len(line) - len(stripped)) // 2
                lines.append('  ' * indent_level + stripped)

        html_str = '\n'.join(lines)

        # 最大長を超える場合は切り詰め
        if len(html_str) > max_length:
            # タグの途中で切れないように調整
            truncated = html_str[:max_length]
            last_tag_start = truncated.rfind('<')
            if last_tag_start > max_length * 0.9:  # 最後の10%以内にタグがある場合
                truncated = truncated[:last_tag_start]
            html_str = truncated + "\n<!-- truncated -->"
            logger.warning(f"HTML truncated from {len(html_str)} to {max_length} characters")

        return html_str

    @staticmethod
    def _remove_empty_tags(soup: BeautifulSoup) -> None:
        """空のタグを再帰的に削除"""
        while True:
            empty_tags = []
            for tag in soup.find_all():
                # テキストも子要素もない場合
                if not tag.get_text(strip=True) and not tag.find_all():
                    # ただし、img, br, hr, input等の自己完結型タグは除外
                    if tag.name not in ['img', 'br', 'hr', 'input', 'meta', 'link']:
                        empty_tags.append(tag)

            if not empty_tags:
                break

            for tag in empty_tags:
                tag.decompose()

    @classmethod
    def _simplify_attributes(cls, soup: BeautifulSoup, keep_links: bool) -> None:
        """属性を簡略化"""
        for tag in soup.find_all():
            # 保持する属性を決定
            keep_attrs = set(cls.KEEP_ATTRIBUTES)
            if not keep_links and tag.name == 'a':
                keep_attrs.discard('href')

            # 属性をフィルタリング
            attrs_to_keep = {}
            for attr, value in tag.attrs.items():
                if attr in keep_attrs:
                    # class属性は文字列に変換
                    if attr == 'class' and isinstance(value, list):
                        attrs_to_keep[attr] = ' '.join(value)
                    else:
                        attrs_to_keep[attr] = value

            tag.attrs = attrs_to_keep

    @staticmethod
    def extract_main_block(html: str, url: Optional[str] = None) -> str:
        """メインブロックのHTMLを抽出（think_page_geminiの extract_main_block を参考）

        Args:
            html: 元のHTML
            url: ページのURL（オプション）

        Returns:
            str: メインブロックのHTML
        """
        soup = BeautifulSoup(html, 'html.parser')

        # bodyタグを探す
        body = soup.find('body')
        if not body:
            logger.warning("No body tag found, using entire HTML")
            return html

        # メインコンテンツの候補を探す
        main_candidates = [
            body.find('main'),
            body.find('article'),
            body.find('div', {'id': 'main'}),
            body.find('div', {'id': 'content'}),
            body.find('div', {'class': 'main'}),
            body.find('div', {'class': 'content'}),
        ]

        # 最初に見つかった候補を使用
        for candidate in main_candidates:
            if candidate:
                logger.debug(f"Found main block: {candidate.name}")
                return str(candidate)

        # 見つからない場合はbody全体
        logger.debug("No specific main block found, using entire body")
        return str(body)
```

### Step 5: DIコンテナへの登録

```python
# src/site2/core/containers.py に追加

from ..core.services.html_parser import HTMLParser
from ..core.services.html_analyzer import HTMLAnalyzer
from ..core.services.encoding_detector import EncodingDetector
from ..core.services.html_preprocessor import HTMLPreprocessor

class Container(containers.DeclarativeContainer):
    # ... 既存のコード ...

    # HTMLパーサー関連
    encoding_detector = providers.Singleton(
        EncodingDetector,
    )

    html_parser = providers.Singleton(
        HTMLParser,
        parser="html.parser",
    )

    html_analyzer = providers.Singleton(
        HTMLAnalyzer,
    )

    html_preprocessor = providers.Singleton(
        HTMLPreprocessor,
    )
```

## テスト実装のポイント

1. **エンコーディングテスト**
   - 各種エンコーディング（UTF-8, Shift_JIS, EUC-JP）のテストファイル
   - エンコーディング検出の精度確認

2. **パースエラーテスト**
   - 壊れたHTML
   - 不正なエンコーディング
   - 巨大ファイル

3. **テキスト抽出テスト**
   - スクリプト・スタイル除去の確認
   - 空白正規化の確認

4. **前処理テスト**
   - Gemini用の前処理が適切か
   - 最大長での切り詰めが正しく動作するか

これで、HTMLパーサーの基盤が整い、後続のDetectサービスやGemini連携の準備が完了します。
