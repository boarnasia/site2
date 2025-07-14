"""
site2 detect機能の契約定義（Contract-First Development）
"""

from typing import Protocol, List, Optional, TYPE_CHECKING
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, ConfigDict

if TYPE_CHECKING:
    from ..domain.detect_domain import Navigation


# DTOs (Data Transfer Objects) - 外部とのやり取り用
class DetectMainRequest(BaseModel):
    """メインコンテンツ検出要求の契約"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: Path = Field(..., description="検出対象のHTMLファイルパス")

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: Path) -> Path:
        """ファイルパスの検証"""
        if not v.exists():
            raise ValueError(f"File must exist: {v}")
        if v.suffix.lower() not in [".html", ".htm"]:
            raise ValueError(f"File must be HTML: {v}")
        return v


class SelectorCandidate(BaseModel):
    """セレクタ候補"""

    selector: str = Field(..., min_length=1, description="CSSセレクタ")
    score: float = Field(..., ge=0.0, le=1.0, description="スコア(0.0-1.0)")
    reasoning: str = Field(..., min_length=1, description="選定理由")
    element_count: int = Field(..., ge=0, description="要素数")


class DetectMainResult(BaseModel):
    """メインコンテンツ検出結果の契約"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: Path = Field(..., description="処理したHTMLファイルパス")
    selectors: List[str] = Field(
        default_factory=list, description="検出したセレクタ一覧"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="信頼度(0.0-1.0)")
    primary_selector: str = Field(..., min_length=1, description="メインセレクタ")
    candidates: List[SelectorCandidate] = Field(
        default_factory=list, description="候補セレクタ一覧"
    )

    @field_validator("primary_selector")
    @classmethod
    def validate_primary_selector(cls, v: str, info) -> str:
        """メインセレクタの検証"""
        # info.dataで他のフィールドにアクセス
        selectors = info.data.get("selectors", [])
        confidence = info.data.get("confidence", 0.0)

        if confidence > 0.0 and len(selectors) == 0:
            raise ValueError("Must have selectors if confidence > 0")

        if selectors and v not in selectors:
            raise ValueError("Primary selector must be in selectors list")

        return v


class DetectNavRequest(BaseModel):
    """ナビゲーション検出要求の契約"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: Path = Field(..., description="検出対象のHTMLファイルパス")

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: Path) -> Path:
        """ファイルパスの検証"""
        if not v.exists():
            raise ValueError(f"File must exist: {v}")
        if v.suffix.lower() not in [".html", ".htm"]:
            raise ValueError(f"File must be HTML: {v}")
        return v


class NavLink(BaseModel):
    """ナビゲーションリンク"""

    text: str = Field(..., min_length=1, description="リンクテキスト")
    href: str = Field(..., min_length=1, description="リンク先URL")
    level: int = Field(default=0, ge=0, description="階層レベル")
    is_external: bool = Field(default=False, description="外部リンクフラグ")


class DetectNavResult(BaseModel):
    """ナビゲーション検出結果の契約"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: Path = Field(..., description="処理したHTMLファイルパス")
    selectors: List[str] = Field(
        default_factory=list, description="検出したセレクタ一覧"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="信頼度(0.0-1.0)")
    primary_selector: str = Field(..., min_length=1, description="メインセレクタ")
    nav_links: List[NavLink] = Field(
        default_factory=list, description="ナビゲーションリンク一覧"
    )

    @field_validator("primary_selector")
    @classmethod
    def validate_primary_selector(cls, v: str, info) -> str:
        """メインセレクタの検証"""
        selectors = info.data.get("selectors", [])
        confidence = info.data.get("confidence", 0.0)

        if confidence > 0.0 and len(selectors) == 0:
            raise ValueError("Must have selectors if confidence > 0")

        if selectors and v not in selectors:
            raise ValueError("Primary selector must be in selectors list")

        return v


class DetectOrderRequest(BaseModel):
    """順序検出要求の契約"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    cache_directory: Path = Field(..., description="キャッシュディレクトリ")
    navigation: "Navigation" = Field(..., description="ナビゲーション構造")
    nav_selector: Optional[str] = Field(
        default=None, description="ナビゲーションセレクタ（後方互換性）"
    )

    @field_validator("cache_directory")
    @classmethod
    def validate_cache_directory(cls, v: Path) -> Path:
        """キャッシュディレクトリの検証"""
        if not v.exists():
            raise ValueError(f"Cache directory must exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Cache directory must be a directory: {v}")
        return v


class OrderedFile(BaseModel):
    """順序付きファイル"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: Path = Field(..., description="ファイルパス")
    title: str = Field(..., min_length=1, description="ファイルタイトル")
    order: int = Field(..., ge=0, description="順序番号")
    level: int = Field(default=0, ge=0, description="階層レベル")
    parent_path: Optional[Path] = Field(default=None, description="親ファイルパス")


class DetectOrderResult(BaseModel):
    """順序検出結果の契約"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    cache_directory: Path = Field(..., description="キャッシュディレクトリ")
    ordered_files: List[OrderedFile] = Field(
        default_factory=list, description="順序付きファイル一覧"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="信頼度(0.0-1.0)")
    method: str = Field(..., description="検出手法")

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        """検出手法の検証"""
        valid_methods = {"navigation", "alphabetical", "numeric"}
        if v not in valid_methods:
            raise ValueError(f"Invalid method: {v}. Must be one of {valid_methods}")
        return v

    @field_validator("ordered_files")
    @classmethod
    def validate_ordered_files(cls, v: List[OrderedFile]) -> List[OrderedFile]:
        """順序付きファイルの検証"""
        # 順序の重複チェック
        orders = [f.order for f in v]
        if len(orders) != len(set(orders)):
            raise ValueError("Orders must be unique")

        # ファイル存在チェック
        for file in v:
            if not file.file_path.exists():
                raise ValueError(f"File must exist: {file.file_path}")

        return v


# サービスインターフェース（ポート）
class DetectServiceProtocol(Protocol):
    """Detectサービスの契約"""

    def detect_main(self, request: DetectMainRequest) -> DetectMainResult:
        """
        メインコンテンツのセレクタを検出

        事前条件:
        - request.file_path は存在するHTMLファイル

        事後条件:
        - DetectMainResultが返される
        - confidence 0.0-1.0 の範囲
        - confidence > 0 の場合、少なくとも1つのセレクタが提供される

        例外:
        - FileNotFoundError: ファイルが存在しない
        - ValueError: HTMLではない、または解析できない
        - DetectError: 検出処理に失敗
        """
        ...

    def detect_nav(self, request: DetectNavRequest) -> DetectNavResult:
        """
        ナビゲーションのセレクタを検出

        事前条件:
        - request.file_path は存在するHTMLファイル

        事後条件:
        - DetectNavResultが返される
        - confidence 0.0-1.0 の範囲
        - ナビゲーションリンクが抽出される

        例外:
        - FileNotFoundError: ファイルが存在しない
        - ValueError: HTMLではない、または解析できない
        - DetectError: 検出処理に失敗
        """
        ...

    def detect_order(self, request: DetectOrderRequest) -> DetectOrderResult:
        """
        ドキュメントの順序を検出

        事前条件:
        - request.cache_directory は存在するディレクトリ
        - ディレクトリ内にHTMLファイルが存在

        事後条件:
        - DetectOrderResultが返される
        - ファイルが順序付けされている
        - 各ファイルにタイトルが設定されている

        例外:
        - FileNotFoundError: ディレクトリが存在しない
        - ValueError: HTMLファイルがない
        - DetectError: 順序検出に失敗
        """
        ...


# エラー定義
class DetectError(Exception):
    """Detect機能の基底エラー"""

    code: str = "DETECT_ERROR"


class InvalidHTMLError(DetectError):
    """無効なHTMLエラー"""

    code: str = "INVALID_HTML"


class SelectorNotFoundError(DetectError):
    """セレクタが見つからないエラー"""

    code: str = "SELECTOR_NOT_FOUND"


class NavigationNotFoundError(DetectError):
    """ナビゲーションが見つからないエラー"""

    code: str = "NAVIGATION_NOT_FOUND"
