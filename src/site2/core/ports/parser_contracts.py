"""
site2 HTMLパーサー機能の契約定義（Contract-First Development）
"""

from typing import Protocol, List, Optional, Dict
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, ConfigDict
from bs4 import BeautifulSoup, Tag


# DTOs (Data Transfer Objects) - 外部とのやり取り用
class ParseRequest(BaseModel):
    """HTML解析要求の契約"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: Path = Field(..., description="解析対象HTMLファイル")
    encoding: Optional[str] = Field(default=None, description="文字エンコーディング")

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: Path) -> Path:
        """ファイルパスの検証"""
        if not v.exists():
            raise ValueError(f"File must exist: {v}")
        if v.suffix.lower() not in [".html", ".htm"]:
            raise ValueError(f"File must be HTML: {v}")
        return v


class ParseResult(BaseModel):
    """HTML解析結果の契約"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: Path = Field(..., description="解析したHTMLファイル")
    soup: BeautifulSoup = Field(..., description="BeautifulSoupオブジェクト")
    encoding: str = Field(..., min_length=1, description="文字エンコーディング")
    parse_time_seconds: float = Field(..., ge=0, description="解析時間(秒)")
    warnings: List[str] = Field(default_factory=list, description="警告一覧")

    @field_validator("soup")
    @classmethod
    def validate_soup(cls, v: BeautifulSoup) -> BeautifulSoup:
        """BeautifulSoupオブジェクトの検証"""
        if v is None:
            raise ValueError("BeautifulSoup object must not be None")
        return v


class TextExtractionRequest(BaseModel):
    """テキスト抽出要求の契約"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    element: Tag = Field(..., description="抽出対象の要素")
    clean_whitespace: bool = Field(default=True, description="空白文字クリーンアップ")
    remove_scripts: bool = Field(default=True, description="スクリプト除去")
    remove_styles: bool = Field(default=True, description="スタイル除去")

    @field_validator("element")
    @classmethod
    def validate_element(cls, v: Tag) -> Tag:
        """Tag要素の検証"""
        if v is None:
            raise ValueError("Element must not be None")
        return v


class TextExtractionResult(BaseModel):
    """テキスト抽出結果の契約"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    original_element: Tag = Field(..., description="元の要素")
    extracted_text: str = Field(..., description="抽出したテキスト")
    text_length: int = Field(..., ge=0, description="テキスト長")
    cleaned: bool = Field(..., description="クリーンアップ済みフラグ")

    @field_validator("text_length")
    @classmethod
    def validate_text_length(cls, v: int, info) -> int:
        """テキスト長の検証"""
        extracted_text = info.data.get("extracted_text", "")
        if v != len(extracted_text):
            raise ValueError("Text length must match actual text length")
        return v


class SelectorSearchRequest(BaseModel):
    """セレクタ検索要求の契約"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    soup: BeautifulSoup = Field(..., description="BeautifulSoupオブジェクト")
    selectors: List[str] = Field(..., min_length=1, description="検索セレクタ一覧")
    find_all: bool = Field(default=False, description="全件検索フラグ")

    @field_validator("soup")
    @classmethod
    def validate_soup(cls, v: BeautifulSoup) -> BeautifulSoup:
        """BeautifulSoupオブジェクトの検証"""
        if v is None:
            raise ValueError("BeautifulSoup object must not be None")
        return v

    @field_validator("selectors")
    @classmethod
    def validate_selectors(cls, v: List[str]) -> List[str]:
        """セレクタ一覧の検証"""
        for selector in v:
            if not selector.strip():
                raise ValueError("Selectors cannot be empty")
        return v


class SelectorSearchResult(BaseModel):
    """セレクタ検索結果の契約"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    matched_selector: Optional[str] = Field(
        default=None, description="マッチしたセレクタ"
    )
    elements: List[Tag] = Field(default_factory=list, description="見つかった要素一覧")
    search_method: str = Field(..., description="検索手法")

    @field_validator("search_method")
    @classmethod
    def validate_search_method(cls, v: str) -> str:
        """検索手法の検証"""
        valid_methods = {"first_match", "all_matches"}
        if v not in valid_methods:
            raise ValueError(
                f"Invalid search method: {v}. Must be one of {valid_methods}"
            )
        return v

    @field_validator("elements")
    @classmethod
    def validate_elements(cls, v: List[Tag], info) -> List[Tag]:
        """要素一覧の検証"""
        matched_selector = info.data.get("matched_selector")
        if matched_selector and len(v) == 0:
            raise ValueError("Must have elements if selector matched")
        if not matched_selector and len(v) > 0:
            raise ValueError("Must not have elements if no selector matched")
        return v


class HTMLMetadata(BaseModel):
    """HTMLメタデータ"""

    title: Optional[str] = Field(default=None, description="ページタイトル")
    description: Optional[str] = Field(default=None, description="ページ説明")
    keywords: Optional[str] = Field(default=None, description="キーワード")
    author: Optional[str] = Field(default=None, description="作者")
    language: Optional[str] = Field(default=None, description="言語")
    meta_tags: Dict[str, str] = Field(default_factory=dict, description="メタタグ")
    og_tags: Dict[str, str] = Field(default_factory=dict, description="OGタグ")


class HTMLStructureAnalysis(BaseModel):
    """HTML構造解析結果"""

    has_main: bool = Field(..., description="main要素の有無")
    has_article: bool = Field(..., description="article要素の有無")
    has_nav: bool = Field(..., description="nav要素の有無")
    has_header: bool = Field(..., description="header要素の有無")
    has_footer: bool = Field(..., description="footer要素の有無")
    heading_count: Dict[str, int] = Field(
        default_factory=dict, description="見出しカウント(h1: 3, h2: 5, etc.)"
    )
    paragraph_count: int = Field(default=0, ge=0, description="段落数")
    link_count: int = Field(default=0, ge=0, description="リンク数")
    image_count: int = Field(default=0, ge=0, description="画像数")
    table_count: int = Field(default=0, ge=0, description="テーブル数")
    list_count: int = Field(default=0, ge=0, description="リスト数")


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
