"""
site2 build機能のドメインモデル（Domain-Driven Design）
"""

from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from enum import Enum
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field, ConfigDict


# エニュメーション
class OutputFormat(Enum):
    """出力フォーマット"""

    MARKDOWN = "md"
    PDF = "pdf"

    def get_extension(self) -> str:
        """ファイル拡張子を取得"""
        return f".{self.value}"

    def get_mime_type(self) -> str:
        """MIMEタイプを取得"""
        if self == OutputFormat.MARKDOWN:
            return "text/markdown"
        elif self == OutputFormat.PDF:
            return "application/pdf"
        else:
            raise ValueError(f"Unknown format: {self}")


class ContentType(Enum):
    """コンテンツタイプ"""

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    CODE = "code"
    TABLE = "table"
    IMAGE = "image"
    LINK = "link"
    QUOTE = "quote"


# 値オブジェクト
class ContentFragment(BaseModel):
    """
    コンテンツの断片

    HTML要素から抽出された意味のある単位
    """

    content_type: ContentType = Field(..., description="Type of content")
    raw_content: str = Field(..., min_length=1, description="Raw content text")
    formatted_content: str = Field(..., min_length=1, description="Formatted content")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    model_config = ConfigDict(frozen=True)

    def get_text_length(self) -> int:
        """テキスト長を取得"""
        return len(self.raw_content)

    def is_heading(self) -> bool:
        """見出しかどうか"""
        return self.content_type == ContentType.HEADING

    def get_heading_level(self) -> Optional[int]:
        """見出しレベルを取得（見出しの場合）"""
        if not self.is_heading():
            return None
        return self.metadata.get("level", 1)


class DocumentMetadata(BaseModel):
    """
    ドキュメントのメタデータ
    """

    title: str = Field(..., min_length=1, description="Document title")
    source_url: Optional[str] = Field(default=None, description="Source URL")
    author: Optional[str] = Field(default=None, description="Author name")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[str] = Field(default=None, description="Update timestamp")
    description: Optional[str] = Field(default=None, description="Document description")
    keywords: List[str] = Field(default_factory=list, description="Keywords")

    model_config = ConfigDict(frozen=True)


class ExtractedContent(BaseModel):
    """
    抽出されたコンテンツのエンティティ

    1つのHTMLファイルから抽出されたコンテンツ
    """

    file_path: Path = Field(..., description="Source file path")
    title: str = Field(..., min_length=1, description="Content title")
    fragments: List[ContentFragment] = Field(
        default_factory=list, description="Content fragments"
    )
    metadata: DocumentMetadata = Field(
        default_factory=lambda: DocumentMetadata(title=""),
        description="Document metadata",
    )
    extraction_warnings: List[str] = Field(
        default_factory=list, description="Extraction warnings"
    )

    model_config = ConfigDict(frozen=False)  # mutable entity

    def add_fragment(self, fragment: ContentFragment) -> None:
        """コンテンツ断片を追加"""
        self.fragments.append(fragment)

    def get_total_text_length(self) -> int:
        """総テキスト長を計算"""
        return sum(fragment.get_text_length() for fragment in self.fragments)

    def get_fragments_by_type(self, content_type: ContentType) -> List[ContentFragment]:
        """指定タイプの断片を取得"""
        return [f for f in self.fragments if f.content_type == content_type]

    def get_headings(self) -> List[ContentFragment]:
        """見出しの断片を取得"""
        return self.get_fragments_by_type(ContentType.HEADING)

    def adjust_heading_levels(self, offset: int) -> None:
        """見出しレベルを調整"""
        for i, fragment in enumerate(self.get_headings()):
            current_level = fragment.get_heading_level() or 1
            new_level = max(1, min(6, current_level + offset))
            # Pydanticの不変オブジェクトを更新
            new_metadata = fragment.metadata.copy()
            new_metadata["level"] = new_level
            new_fragment = fragment.model_copy(update={"metadata": new_metadata})
            # リスト内の該当する断片を置き換え
            fragment_index = self.fragments.index(fragment)
            self.fragments[fragment_index] = new_fragment


class CombinedDocument(BaseModel):
    """
    結合されたドキュメントのエンティティ

    複数のExtractedContentを結合した最終的なドキュメント
    """

    title: str = Field(..., min_length=1, description="Document title")
    format: OutputFormat = Field(..., description="Output format")
    contents: List[ExtractedContent] = Field(
        default_factory=list, description="Document contents"
    )
    toc_enabled: bool = Field(default=True, description="Table of contents enabled")
    metadata: DocumentMetadata = Field(
        default_factory=lambda: DocumentMetadata(title=""),
        description="Document metadata",
    )
    build_options: Dict[str, Any] = Field(
        default_factory=dict, description="Build options"
    )

    model_config = ConfigDict(frozen=False)  # mutable entity

    def add_content(self, content: ExtractedContent) -> None:
        """コンテンツを追加"""
        self.contents.append(content)

    def get_total_pages(self) -> int:
        """総ページ数を取得"""
        return len(self.contents)

    def get_total_text_length(self) -> int:
        """総テキスト長を計算"""
        return sum(content.get_total_text_length() for content in self.contents)

    def generate_toc(self) -> List[Dict[str, Any]]:
        """目次を生成"""
        toc_items = []

        for i, content in enumerate(self.contents):
            toc_item = {
                "title": content.title,
                "page": i + 1,
                "file_path": str(content.file_path),
                "headings": [],
            }

            # 見出しを収集
            for fragment in content.get_headings():
                heading_item = {
                    "text": fragment.raw_content,
                    "level": fragment.get_heading_level() or 1,
                }
                toc_item["headings"].append(heading_item)

            toc_items.append(toc_item)

        return toc_items

    def adjust_heading_hierarchy(self) -> None:
        """見出し階層を調整して重複を避ける"""
        for content in self.contents:
            # 各ドキュメントの見出しレベルを1つずつ下げる
            content.adjust_heading_levels(1)


class ConvertRequest(BaseModel):
    """変換要求の基底クラス"""

    file_path: Path = Field(..., description="File path to convert")
    main_selector: str = Field(
        ..., min_length=1, description="CSS selector for main content"
    )
    options: Dict[str, Any] = Field(
        default_factory=dict, description="Conversion options"
    )

    model_config = ConfigDict(frozen=True)


class MarkdownConvertRequest(ConvertRequest):
    """Markdown変換要求"""

    include_toc: bool = Field(default=True, description="Include table of contents")
    heading_offset: int = Field(
        default=0, ge=0, le=5, description="Heading level offset"
    )


class PDFConvertRequest(ConvertRequest):
    """PDF変換要求"""

    pdf_options: Dict[str, Any] = Field(
        default_factory=dict, description="PDF-specific options"
    )


class ConvertResult(BaseModel):
    """変換結果"""

    original_file: Path = Field(..., description="Original file path")
    content: Union[str, bytes] = Field(..., description="Converted content")
    format: OutputFormat = Field(..., description="Output format")
    title: str = Field(..., min_length=1, description="Document title")
    extracted_text_length: int = Field(
        ..., ge=0, description="Length of extracted text"
    )
    warnings: List[str] = Field(default_factory=list, description="Conversion warnings")

    model_config = ConfigDict(frozen=True)


# ドメインサービス
class ContentExtractor(ABC):
    """
    コンテンツ抽出の抽象ベースクラス
    """

    @abstractmethod
    def extract(self, file_path: Path, selector: str) -> ExtractedContent:
        """ファイルからコンテンツを抽出"""
        pass


class DocumentBuilder:
    """
    ドキュメント構築のドメインサービス

    複数のコンテンツを結合して最終的なドキュメントを作成
    """

    def __init__(self, format: OutputFormat):
        self.format = format

    def build_document(
        self,
        title: str,
        contents: List[ExtractedContent],
        options: Optional[Dict[str, Any]] = None,
    ) -> CombinedDocument:
        """複数のコンテンツからドキュメントを構築"""
        options = options or {}

        document = CombinedDocument(
            title=title,
            format=self.format,
            toc_enabled=options.get("include_toc", True),
            build_options=options,
        )

        # コンテンツを追加
        for content in contents:
            document.add_content(content)

        # 見出し階層を調整
        if options.get("adjust_headings", True):
            document.adjust_heading_hierarchy()

        return document

    def create_metadata(
        self, title: str, source_url: Optional[str] = None, **kwargs
    ) -> DocumentMetadata:
        """ドキュメントメタデータを作成"""
        return DocumentMetadata(title=title, source_url=source_url, **kwargs)


class FormatConverter(ABC):
    """
    フォーマット変換の抽象ベースクラス
    """

    @abstractmethod
    def convert(self, document: CombinedDocument) -> Union[str, bytes]:
        """ドキュメントを指定フォーマットに変換"""
        pass

    @abstractmethod
    def get_supported_format(self) -> OutputFormat:
        """サポートするフォーマットを取得"""
        pass


class MarkdownConverter(FormatConverter):
    """Markdown変換器の抽象クラス"""

    def get_supported_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN


class PDFConverter(FormatConverter):
    """PDF変換器の抽象クラス"""

    def get_supported_format(self) -> OutputFormat:
        return OutputFormat.PDF


# ファクトリー
class ContentExtractorFactory:
    """コンテンツ抽出器のファクトリー"""

    _extractors: Dict[str, ContentExtractor] = {}

    @classmethod
    def register(cls, name: str, extractor: ContentExtractor) -> None:
        """抽出器を登録"""
        cls._extractors[name] = extractor

    @classmethod
    def create(cls, name: str = "default") -> ContentExtractor:
        """抽出器を作成"""
        if name not in cls._extractors:
            raise ValueError(f"Unknown extractor: {name}")
        return cls._extractors[name]


class FormatConverterFactory:
    """フォーマット変換器のファクトリー"""

    _converters: Dict[OutputFormat, FormatConverter] = {}

    @classmethod
    def register(cls, format: OutputFormat, converter: FormatConverter) -> None:
        """変換器を登録"""
        cls._converters[format] = converter

    @classmethod
    def create(cls, format: OutputFormat) -> FormatConverter:
        """変換器を作成"""
        if format not in cls._converters:
            raise ValueError(f"Unsupported format: {format}")
        return cls._converters[format]


# バリューオブジェクトのビルダー
class DocumentMetadataBuilder:
    """ドキュメントメタデータのビルダー"""

    def __init__(self, title: str):
        self._title = title
        self._source_url: Optional[str] = None
        self._author: Optional[str] = None
        self._created_at: Optional[str] = None
        self._updated_at: Optional[str] = None
        self._description: Optional[str] = None
        self._keywords: List[str] = []

    def source_url(self, url: str) -> "DocumentMetadataBuilder":
        self._source_url = url
        return self

    def author(self, author: str) -> "DocumentMetadataBuilder":
        self._author = author
        return self

    def created_at(self, timestamp: str) -> "DocumentMetadataBuilder":
        self._created_at = timestamp
        return self

    def updated_at(self, timestamp: str) -> "DocumentMetadataBuilder":
        self._updated_at = timestamp
        return self

    def description(self, desc: str) -> "DocumentMetadataBuilder":
        self._description = desc
        return self

    def keywords(self, keywords: List[str]) -> "DocumentMetadataBuilder":
        self._keywords = keywords
        return self

    def build(self) -> DocumentMetadata:
        """メタデータを構築"""
        return DocumentMetadata(
            title=self._title,
            source_url=self._source_url,
            author=self._author,
            created_at=self._created_at,
            updated_at=self._updated_at,
            description=self._description,
            keywords=self._keywords,
        )
