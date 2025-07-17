"""
site2 build機能の契約定義（Contract-First Development）
"""

from typing import Protocol, List, Optional, Dict, Any, Union, runtime_checkable
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, ConfigDict

# ドメインモデルをインポート
from ..domain.build_domain import (
    OutputFormat,
    ExtractedContent,
    ConvertResult,
    MarkdownConvertRequest,
    PDFConvertRequest,
)
from ..domain.detect_domain import OrderedFile, DocumentOrder


# DTOs (Data Transfer Objects) - 外部とのやり取り用
class BuildRequest(BaseModel):
    """ビルド要求の契約"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    cache_directory: Path = Field(..., description="キャッシュディレクトリ")
    main_selector: str = Field(
        ..., min_length=1, description="メインコンテンツセレクタ"
    )
    ordered_files: List[OrderedFile] = Field(
        ..., min_length=1, description="順序付きファイル一覧"
    )
    doc_order: DocumentOrder = Field(
        ..., description="ドキュメント順序（Task 21で追加）"
    )
    format: OutputFormat = Field(..., description="出力フォーマット")
    output_path: Optional[Path] = Field(default=None, description="出力パス")
    options: Dict[str, Any] = Field(default_factory=dict, description="オプション")

    @field_validator("cache_directory")
    @classmethod
    def validate_cache_directory(cls, v: Path) -> Path:
        """キャッシュディレクトリの検証"""
        if not v.exists():
            raise ValueError(f"Cache directory must exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Cache directory must be a directory: {v}")
        return v

    @field_validator("main_selector")
    @classmethod
    def validate_main_selector(cls, v: str) -> str:
        """メインセレクタの検証"""
        if not v.strip():
            raise ValueError("Main selector cannot be empty")
        return v

    @field_validator("ordered_files")
    @classmethod
    def validate_ordered_files(cls, v: List[OrderedFile]) -> List[OrderedFile]:
        """順序付きファイルの検証"""
        for file in v:
            if not file.file_path.exists():
                raise ValueError(f"File must exist: {file.file_path}")
        return v


class BuildResult(BaseModel):
    """ビルド結果の契約"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    content: Union[str, bytes] = Field(..., description="生成コンテンツ")
    format: OutputFormat = Field(..., description="出力フォーマット")
    output_path: Optional[Path] = Field(default=None, description="出力パス")
    page_count: int = Field(..., gt=0, description="ページ数")
    extracted_files: List[ExtractedContent] = Field(
        default_factory=list, min_length=1, description="抽出ファイル一覧"
    )
    warnings: List[str] = Field(default_factory=list, description="警告一覧")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="統計情報")

    @field_validator("content")
    @classmethod
    def validate_content_format(cls, v: Union[str, bytes], info) -> Union[str, bytes]:
        """コンテンツフォーマットの検証"""
        format_val = info.data.get("format")
        if format_val == OutputFormat.MARKDOWN and not isinstance(v, str):
            raise ValueError("Markdown content must be string")
        elif format_val == OutputFormat.PDF and not isinstance(v, bytes):
            raise ValueError("PDF content must be bytes")
        return v

    @field_validator("output_path")
    @classmethod
    def validate_output_path(cls, v: Optional[Path]) -> Optional[Path]:
        """出力パスの検証"""
        if v and not v.parent.exists():
            raise ValueError(f"Output directory must exist: {v.parent}")
        return v


# サービスインターフェース（ポート）
@runtime_checkable
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


@runtime_checkable
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


@runtime_checkable
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
