"""
site2 build機能の契約定義（Contract-First Development）
"""

from typing import Protocol, List, Optional, Dict, Any, Union, TYPE_CHECKING
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from ..domain.detect_domain import OrderedFile


# エニュメーション
class OutputFormat(Enum):
    """出力フォーマット"""

    MARKDOWN = "md"
    PDF = "pdf"


# DTOs (Data Transfer Objects) - 外部とのやり取り用
@dataclass
class BuildRequest:
    """ビルド要求の契約"""

    cache_directory: Path
    main_selector: str
    ordered_files: List["OrderedFile"]  # detect_contracts.pyから参照
    format: OutputFormat
    output_path: Optional[Path] = None
    options: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """契約の事前条件を検証"""
        assert self.cache_directory.exists(), (
            f"Cache directory must exist: {self.cache_directory}"
        )
        assert self.cache_directory.is_dir(), (
            f"Cache directory must be a directory: {self.cache_directory}"
        )
        assert self.main_selector.strip(), "Main selector cannot be empty"
        assert len(self.ordered_files) > 0, "Must have at least one file to build"

        # ファイル存在チェック
        for file in self.ordered_files:
            assert file.file_path.exists(), f"File must exist: {file.file_path}"


@dataclass
class ExtractedContent:
    """抽出されたコンテンツ"""

    file_path: Path
    title: str
    content: str
    heading_level: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildResult:
    """ビルド結果の契約"""

    content: Union[str, bytes]
    format: OutputFormat
    output_path: Optional[Path]
    page_count: int
    extracted_files: List[ExtractedContent] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """契約の事後条件を検証"""
        assert self.page_count > 0, "Page count must be positive"
        assert len(self.extracted_files) > 0, "Must have extracted content"

        # フォーマット特有のチェック
        if self.format == OutputFormat.MARKDOWN:
            assert isinstance(self.content, str), "Markdown content must be string"
        elif self.format == OutputFormat.PDF:
            assert isinstance(self.content, bytes), "PDF content must be bytes"

        # 出力パスが指定されている場合、親ディレクトリが存在することを確認
        if self.output_path:
            assert self.output_path.parent.exists(), (
                f"Output directory must exist: {self.output_path.parent}"
            )


@dataclass
class ConvertRequest:
    """変換要求の基底クラス"""

    file_path: Path
    main_selector: str
    options: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """契約の事前条件を検証"""
        assert self.file_path.exists(), f"File must exist: {self.file_path}"
        assert self.main_selector.strip(), "Main selector cannot be empty"


@dataclass
class MarkdownConvertRequest(ConvertRequest):
    """Markdown変換要求"""

    include_toc: bool = True
    heading_offset: int = 0


@dataclass
class PDFConvertRequest(ConvertRequest):
    """PDF変換要求"""

    pdf_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConvertResult:
    """変換結果"""

    original_file: Path
    content: Union[str, bytes]
    format: OutputFormat
    title: str
    extracted_text_length: int
    warnings: List[str] = field(default_factory=list)

    def validate(self) -> None:
        """契約の事後条件を検証"""
        assert self.extracted_text_length >= 0, "Text length must be non-negative"
        assert self.title.strip(), "Title cannot be empty"


# サービスインターフェース（ポート）
class BuildServiceProtocol(Protocol):
    """Buildサービスの契約"""

    def build(self, request: BuildRequest) -> BuildResult:
        """
        ドキュメントをビルド

        事前条件:
        - request.cache_directory は存在するディレクトリ
        - request.ordered_files にはすべて存在するファイルが含まれる
        - request.main_selector は有効なCSSセレクタ

        事後条件:
        - BuildResultが返される
        - content にビルド結果が含まれる
        - 指定された形式（Markdown/PDF）で出力される

        例外:
        - FileNotFoundError: ファイルが存在しない
        - ValueError: 無効なセレクタまたは設定
        - BuildError: ビルド処理に失敗
        """
        ...


class MarkdownConverterProtocol(Protocol):
    """Markdownコンバーターの契約"""

    def convert(self, request: MarkdownConvertRequest) -> ConvertResult:
        """
        HTMLをMarkdownに変換

        事前条件:
        - request.file_path は存在するHTMLファイル
        - request.main_selector は有効なCSSセレクタ

        事後条件:
        - ConvertResultが返される
        - content はMarkdown形式の文字列

        例外:
        - FileNotFoundError: ファイルが存在しない
        - ValueError: 無効なHTML、またはセレクタでコンテンツが見つからない
        - ConvertError: 変換処理に失敗
        """
        ...


class PDFConverterProtocol(Protocol):
    """PDFコンバーターの契約"""

    def convert(self, request: PDFConvertRequest) -> ConvertResult:
        """
        HTMLをPDFに変換

        事前条件:
        - request.file_path は存在するHTMLファイル
        - request.main_selector は有効なCSSセレクタ

        事後条件:
        - ConvertResultが返される
        - content はPDF形式のバイト列

        例外:
        - FileNotFoundError: ファイルが存在しない
        - ValueError: 無効なHTML、またはセレクタでコンテンツが見つからない
        - ConvertError: 変換処理に失敗
        """
        ...

    def convert_multiple(
        self, requests: List[PDFConvertRequest], merge: bool = True
    ) -> Union[ConvertResult, List[ConvertResult]]:
        """
        複数のHTMLファイルをPDFに変換

        事前条件:
        - すべてのrequestsが有効

        事後条件:
        - mergeがTrueの場合、結合されたPDFのConvertResultを返す
        - mergeがFalseの場合、個別PDFのConvertResultリストを返す

        例外:
        - ConvertError: 変換または結合に失敗
        """
        ...


# エラー定義
class BuildError(Exception):
    """Build機能の基底エラー"""

    code: str = "BUILD_ERROR"


class ConvertError(BuildError):
    """変換エラー"""

    code: str = "CONVERT_ERROR"


class InvalidSelectorError(BuildError):
    """無効なセレクタエラー"""

    code: str = "INVALID_SELECTOR"


class ContentNotFoundError(BuildError):
    """コンテンツが見つからないエラー"""

    code: str = "CONTENT_NOT_FOUND"


class OutputFormatError(BuildError):
    """出力フォーマットエラー"""

    code: str = "OUTPUT_FORMAT_ERROR"
