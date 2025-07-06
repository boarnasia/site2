"""
site2 detect機能の契約定義（Contract-First Development）
"""

from typing import Protocol, List, Optional
from pathlib import Path
from dataclasses import dataclass, field


# DTOs (Data Transfer Objects) - 外部とのやり取り用
@dataclass
class DetectMainRequest:
    """メインコンテンツ検出要求の契約"""

    file_path: Path

    def validate(self) -> None:
        """契約の事前条件を検証"""
        assert self.file_path.exists(), f"File must exist: {self.file_path}"
        assert self.file_path.suffix.lower() in [".html", ".htm"], (
            f"File must be HTML: {self.file_path}"
        )


@dataclass
class SelectorCandidate:
    """セレクタ候補"""

    selector: str
    score: float
    reasoning: str
    element_count: int


@dataclass
class DetectMainResult:
    """メインコンテンツ検出結果の契約"""

    file_path: Path
    selectors: List[str]
    confidence: float
    primary_selector: str
    candidates: List[SelectorCandidate] = field(default_factory=list)

    def validate(self) -> None:
        """契約の事後条件を検証"""
        assert 0.0 <= self.confidence <= 1.0, "Confidence must be between 0.0 and 1.0"
        assert len(self.selectors) > 0 or self.confidence == 0.0, (
            "Must have selectors if confidence > 0"
        )
        if self.selectors:
            assert self.primary_selector in self.selectors, (
                "Primary selector must be in selectors list"
            )


@dataclass
class DetectNavRequest:
    """ナビゲーション検出要求の契約"""

    file_path: Path

    def validate(self) -> None:
        """契約の事前条件を検証"""
        assert self.file_path.exists(), f"File must exist: {self.file_path}"
        assert self.file_path.suffix.lower() in [".html", ".htm"], (
            f"File must be HTML: {self.file_path}"
        )


@dataclass
class NavLink:
    """ナビゲーションリンク"""

    text: str
    href: str
    level: int = 0
    is_external: bool = False


@dataclass
class DetectNavResult:
    """ナビゲーション検出結果の契約"""

    file_path: Path
    selectors: List[str]
    confidence: float
    primary_selector: str
    nav_links: List[NavLink] = field(default_factory=list)

    def validate(self) -> None:
        """契約の事後条件を検証"""
        assert 0.0 <= self.confidence <= 1.0, "Confidence must be between 0.0 and 1.0"
        assert len(self.selectors) > 0 or self.confidence == 0.0, (
            "Must have selectors if confidence > 0"
        )
        if self.selectors:
            assert self.primary_selector in self.selectors, (
                "Primary selector must be in selectors list"
            )


@dataclass
class DetectOrderRequest:
    """順序検出要求の契約"""

    cache_directory: Path
    nav_selector: Optional[str] = None

    def validate(self) -> None:
        """契約の事前条件を検証"""
        assert self.cache_directory.exists(), (
            f"Cache directory must exist: {self.cache_directory}"
        )
        assert self.cache_directory.is_dir(), (
            f"Cache directory must be a directory: {self.cache_directory}"
        )


@dataclass
class OrderedFile:
    """順序付きファイル"""

    file_path: Path
    title: str
    order: int
    level: int = 0
    parent_path: Optional[Path] = None


@dataclass
class DetectOrderResult:
    """順序検出結果の契約"""

    cache_directory: Path
    ordered_files: List[OrderedFile]
    confidence: float
    method: str  # 'navigation', 'alphabetical', 'numeric'

    def validate(self) -> None:
        """契約の事後条件を検証"""
        assert 0.0 <= self.confidence <= 1.0, "Confidence must be between 0.0 and 1.0"
        assert self.method in ["navigation", "alphabetical", "numeric"], (
            f"Invalid method: {self.method}"
        )

        # 順序の重複チェック
        orders = [f.order for f in self.ordered_files]
        assert len(orders) == len(set(orders)), "Orders must be unique"

        # ファイル存在チェック
        for file in self.ordered_files:
            assert file.file_path.exists(), f"File must exist: {file.file_path}"


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
