"""
site2 HTMLパーサー機能の契約定義（Contract-First Development）
"""

from typing import Protocol, List, Optional, Dict
from pathlib import Path
from dataclasses import dataclass, field
from bs4 import BeautifulSoup, Tag


# DTOs (Data Transfer Objects) - 外部とのやり取り用
@dataclass
class ParseRequest:
    """HTML解析要求の契約"""

    file_path: Path
    encoding: Optional[str] = None

    def validate(self) -> None:
        """契約の事前条件を検証"""
        assert self.file_path.exists(), f"File must exist: {self.file_path}"
        assert self.file_path.suffix.lower() in [".html", ".htm"], (
            f"File must be HTML: {self.file_path}"
        )


@dataclass
class ParseResult:
    """HTML解析結果の契約"""

    file_path: Path
    soup: BeautifulSoup
    encoding: str
    parse_time_seconds: float
    warnings: List[str] = field(default_factory=list)

    def validate(self) -> None:
        """契約の事後条件を検証"""
        assert self.soup is not None, "BeautifulSoup object must not be None"
        assert self.encoding.strip(), "Encoding must not be empty"
        assert self.parse_time_seconds >= 0, "Parse time must be non-negative"


@dataclass
class TextExtractionRequest:
    """テキスト抽出要求の契約"""

    element: Tag
    clean_whitespace: bool = True
    remove_scripts: bool = True
    remove_styles: bool = True

    def validate(self) -> None:
        """契約の事前条件を検証"""
        assert self.element is not None, "Element must not be None"


@dataclass
class TextExtractionResult:
    """テキスト抽出結果の契約"""

    original_element: Tag
    extracted_text: str
    text_length: int
    cleaned: bool

    def validate(self) -> None:
        """契約の事後条件を検証"""
        assert self.text_length >= 0, "Text length must be non-negative"
        assert self.text_length == len(self.extracted_text), (
            "Text length must match actual text length"
        )


@dataclass
class SelectorSearchRequest:
    """セレクタ検索要求の契約"""

    soup: BeautifulSoup
    selectors: List[str]
    find_all: bool = False

    def validate(self) -> None:
        """契約の事前条件を検証"""
        assert self.soup is not None, "BeautifulSoup object must not be None"
        assert len(self.selectors) > 0, "Must provide at least one selector"
        for selector in self.selectors:
            assert selector.strip(), "Selectors cannot be empty"


@dataclass
class SelectorSearchResult:
    """セレクタ検索結果の契約"""

    matched_selector: Optional[str]
    elements: List[Tag]
    search_method: str  # 'first_match', 'all_matches'

    def validate(self) -> None:
        """契約の事後条件を検証"""
        if self.matched_selector:
            assert len(self.elements) > 0, "Must have elements if selector matched"
        else:
            assert len(self.elements) == 0, (
                "Must not have elements if no selector matched"
            )


@dataclass
class HTMLMetadata:
    """HTMLメタデータ"""

    title: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[str] = None
    author: Optional[str] = None
    language: Optional[str] = None
    meta_tags: Dict[str, str] = field(default_factory=dict)
    og_tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class HTMLStructureAnalysis:
    """HTML構造解析結果"""

    has_main: bool
    has_article: bool
    has_nav: bool
    has_header: bool
    has_footer: bool
    heading_count: Dict[str, int] = field(default_factory=dict)  # h1: 3, h2: 5, etc.
    paragraph_count: int = 0
    link_count: int = 0
    image_count: int = 0
    table_count: int = 0
    list_count: int = 0


# サービスインターフェース（ポート）
class HTMLParserProtocol(Protocol):
    """HTMLパーサーの契約"""

    def parse(self, request: ParseRequest) -> ParseResult:
        """
        HTMLファイルをパース

        事前条件:
        - request.file_path は存在するHTMLファイル

        事後条件:
        - ParseResultが返される
        - BeautifulSoupオブジェクトが利用可能

        例外:
        - FileNotFoundError: ファイルが存在しない
        - UnicodeDecodeError: エンコーディングの問題
        - ParseError: HTML解析に失敗
        """
        ...

    def parse_string(self, html: str) -> BeautifulSoup:
        """
        HTML文字列をパース

        事前条件:
        - html は空でない文字列

        事後条件:
        - BeautifulSoupオブジェクトが返される

        例外:
        - ValueError: 空の文字列
        - ParseError: HTML解析に失敗
        """
        ...

    def extract_text(self, request: TextExtractionRequest) -> TextExtractionResult:
        """
        HTML要素からテキストを抽出

        事前条件:
        - request.element は有効なTag

        事後条件:
        - TextExtractionResultが返される
        - extracted_text にクリーンなテキストが含まれる

        例外:
        - ValueError: 無効な要素
        - ExtractError: テキスト抽出に失敗
        """
        ...

    def find_by_selectors(self, request: SelectorSearchRequest) -> SelectorSearchResult:
        """
        複数のセレクタから要素を検索

        事前条件:
        - request.soup は有効なBeautifulSoup
        - request.selectors は空でないリスト

        事後条件:
        - SelectorSearchResultが返される
        - 最初にマッチしたセレクタと要素が返される

        例外:
        - ValueError: 無効なセレクタ
        - SearchError: 検索に失敗
        """
        ...


class HTMLAnalyzerProtocol(Protocol):
    """HTML構造解析の契約"""

    def analyze_structure(self, soup: BeautifulSoup) -> HTMLStructureAnalysis:
        """
        HTML構造を解析

        事前条件:
        - soup は有効なBeautifulSoup

        事後条件:
        - HTMLStructureAnalysisが返される
        - 各セマンティック要素の存在が確認される

        例外:
        - ValueError: 無効なBeautifulSoup
        - AnalysisError: 解析に失敗
        """
        ...

    def extract_metadata(self, soup: BeautifulSoup) -> HTMLMetadata:
        """
        HTMLメタデータを抽出

        事前条件:
        - soup は有効なBeautifulSoup

        事後条件:
        - HTMLMetadataが返される
        - 利用可能なメタデータが抽出される

        例外:
        - ValueError: 無効なBeautifulSoup
        - ExtractionError: メタデータ抽出に失敗
        """
        ...

    def calculate_text_density(self, element: Tag) -> float:
        """
        要素のテキスト密度を計算（テキスト長/HTML長）

        事前条件:
        - element は有効なTag

        事後条件:
        - 0.0-1.0 の範囲の値が返される

        例外:
        - ValueError: 無効な要素
        """
        ...


class EncodingDetectorProtocol(Protocol):
    """エンコーディング検出の契約"""

    def detect_encoding(self, file_path: Path) -> str:
        """
        ファイルのエンコーディングを検出

        事前条件:
        - file_path は存在するファイル

        事後条件:
        - エンコーディング名が返される（例: 'utf-8', 'shift_jis'）

        例外:
        - FileNotFoundError: ファイルが存在しない
        - DetectionError: エンコーディング検出に失敗
        """
        ...

    def detect_encoding_from_bytes(self, data: bytes) -> str:
        """
        バイト列からエンコーディングを検出

        事前条件:
        - data は空でないバイト列

        事後条件:
        - エンコーディング名が返される

        例外:
        - ValueError: 空のデータ
        - DetectionError: エンコーディング検出に失敗
        """
        ...


# エラー定義
class ParseError(Exception):
    """HTML解析の基底エラー"""

    code: str = "PARSE_ERROR"


class EncodingError(ParseError):
    """エンコーディングエラー"""

    code: str = "ENCODING_ERROR"


class SelectorError(ParseError):
    """セレクタエラー"""

    code: str = "SELECTOR_ERROR"


class ExtractError(ParseError):
    """テキスト抽出エラー"""

    code: str = "EXTRACT_ERROR"


class AnalysisError(ParseError):
    """構造解析エラー"""

    code: str = "ANALYSIS_ERROR"


class DetectionError(ParseError):
    """エンコーディング検出エラー"""

    code: str = "DETECTION_ERROR"
