"""
site2 detect機能のドメインモデル（Domain-Driven Design）
"""

from typing import List, Optional
from pathlib import Path
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SelectorCandidate:
    """
    セレクタ候補の値オブジェクト

    検出されたCSSセレクタとその評価スコア
    """

    selector: str
    score: float
    reasoning: str
    element_count: int

    def __post_init__(self):
        if not self.selector.strip():
            raise ValueError("Selector cannot be empty")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0: {self.score}")
        if self.element_count < 0:
            raise ValueError(
                f"Element count must be non-negative: {self.element_count}"
            )


@dataclass(frozen=True)
class DetectionScore:
    """
    検出スコアの値オブジェクト

    0.0から1.0の範囲で、検出の信頼度を表す
    """

    value: float

    def __post_init__(self):
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0: {self.value}")

    @classmethod
    def high(cls) -> "DetectionScore":
        """高い信頼度（0.8以上）"""
        return cls(0.8)

    @classmethod
    def medium(cls) -> "DetectionScore":
        """中程度の信頼度（0.5-0.8）"""
        return cls(0.6)

    @classmethod
    def low(cls) -> "DetectionScore":
        """低い信頼度（0.5未満）"""
        return cls(0.3)

    @classmethod
    def none(cls) -> "DetectionScore":
        """検出なし"""
        return cls(0.0)

    def is_reliable(self) -> bool:
        """信頼できるスコアかどうか（0.5以上）"""
        return self.value >= 0.5


@dataclass(frozen=True)
class NavLink:
    """
    ナビゲーションリンクの値オブジェクト

    階層構造を持つナビゲーションリンク
    """

    text: str
    href: str
    level: int = 0
    is_external: bool = False

    def __post_init__(self):
        if not self.text.strip():
            raise ValueError("Link text cannot be empty")
        if self.level < 0:
            raise ValueError(f"Level must be non-negative: {self.level}")

    def is_internal_link(self) -> bool:
        """内部リンクかどうか"""
        return not self.is_external and not self.href.startswith(
            ("http://", "https://")
        )

    def get_file_path(self, base_path: Path) -> Optional[Path]:
        """リンクが指すファイルパスを取得"""
        if self.is_external:
            return None

        # アンカーリンクやクエリパラメータを除去
        clean_href = self.href.split("#")[0].split("?")[0]

        if not clean_href:
            return None

        return base_path / clean_href


@dataclass
class NavigationStructure:
    """
    ナビゲーション構造のエンティティ

    検出されたナビゲーションの階層構造を表現
    """

    root_selector: str
    links: List[NavLink] = field(default_factory=list)
    max_depth: int = 0

    def __post_init__(self):
        if not self.root_selector.strip():
            raise ValueError("Root selector cannot be empty")

        # 最大深度を計算
        if self.links:
            self.max_depth = max(link.level for link in self.links)

    def get_links_by_level(self, level: int) -> List[NavLink]:
        """指定レベルのリンクを取得"""
        return [link for link in self.links if link.level == level]

    def get_file_order(self, base_path: Path) -> List[Path]:
        """ナビゲーション順序でファイルパスのリストを取得"""
        file_paths = []
        for link in self.links:
            file_path = link.get_file_path(base_path)
            if file_path and file_path not in file_paths:
                file_paths.append(file_path)
        return file_paths

    def add_link(self, link: NavLink) -> None:
        """リンクを追加"""
        self.links.append(link)
        self.max_depth = max(self.max_depth, link.level)


@dataclass(frozen=True)
class OrderedFile:
    """
    順序付きファイルの値オブジェクト

    文書の順序と階層を表現
    """

    file_path: Path
    title: str
    order: int
    level: int = 0
    parent_path: Optional[Path] = None

    def __post_init__(self):
        if not self.title.strip():
            raise ValueError("Title cannot be empty")
        if self.order < 0:
            raise ValueError(f"Order must be non-negative: {self.order}")
        if self.level < 0:
            raise ValueError(f"Level must be non-negative: {self.level}")

    def is_child_of(self, other: "OrderedFile") -> bool:
        """他のファイルの子ファイルかどうか"""
        return self.parent_path == other.file_path or (
            self.level > other.level and self.order > other.order
        )

    def get_display_title(self, include_order: bool = False) -> str:
        """表示用タイトルを取得"""
        indent = "  " * self.level
        prefix = f"{self.order}. " if include_order else ""
        return f"{indent}{prefix}{self.title}"


@dataclass
class DocumentOrder:
    """
    文書順序のエンティティ

    複数の文書ファイルの順序を管理
    """

    files: List[OrderedFile] = field(default_factory=list)
    method: str = "unknown"  # 'navigation', 'alphabetical', 'numeric'
    confidence: DetectionScore = field(default_factory=DetectionScore.none)

    def __post_init__(self):
        if self.method not in ["navigation", "alphabetical", "numeric", "unknown"]:
            raise ValueError(f"Invalid method: {self.method}")

        # 順序でソート
        self.files.sort(key=lambda f: f.order)

    def add_file(self, file: OrderedFile) -> None:
        """ファイルを追加して順序を維持"""
        self.files.append(file)
        self.files.sort(key=lambda f: f.order)

    def get_files_by_level(self, level: int) -> List[OrderedFile]:
        """指定レベルのファイルを取得"""
        return [f for f in self.files if f.level == level]

    def get_top_level_files(self) -> List[OrderedFile]:
        """トップレベル（level=0）のファイルを取得"""
        return self.get_files_by_level(0)

    def validate_order(self) -> bool:
        """順序が重複していないかチェック"""
        orders = [f.order for f in self.files]
        return len(orders) == len(set(orders))

    def reorder(self) -> None:
        """連続した順序番号に振り直し"""
        for i, file in enumerate(self.files):
            object.__setattr__(file, "order", i)


# ドメインサービス
class ContentDetectionService:
    """
    コンテンツ検出のドメインサービス

    複数の検出ロジックを組み合わせてコンテンツを特定
    """

    @staticmethod
    def merge_candidates(
        candidates: List[SelectorCandidate],
    ) -> List[SelectorCandidate]:
        """
        複数の候補をマージして重複を排除

        同じセレクタがある場合は最高スコアを採用
        """
        unique_candidates = {}

        for candidate in candidates:
            if candidate.selector not in unique_candidates:
                unique_candidates[candidate.selector] = candidate
            else:
                existing = unique_candidates[candidate.selector]
                if candidate.score > existing.score:
                    unique_candidates[candidate.selector] = candidate

        # スコア順でソート
        return sorted(unique_candidates.values(), key=lambda c: c.score, reverse=True)

    @staticmethod
    def calculate_confidence(candidates: List[SelectorCandidate]) -> DetectionScore:
        """候補リストから全体の信頼度を計算"""
        if not candidates:
            return DetectionScore.none()

        # 最高スコアを基準に信頼度を決定
        best_score = candidates[0].score

        if best_score >= 0.8:
            return DetectionScore.high()
        elif best_score >= 0.6:
            return DetectionScore.medium()
        elif best_score >= 0.3:
            return DetectionScore.low()
        else:
            return DetectionScore.none()


class NavigationOrderService:
    """
    ナビゲーション順序のドメインサービス

    ナビゲーション構造から文書順序を決定
    """

    @staticmethod
    def extract_order_from_navigation(
        nav_structure: NavigationStructure, base_path: Path
    ) -> DocumentOrder:
        """ナビゲーション構造から文書順序を抽出"""
        ordered_files = []

        for i, link in enumerate(nav_structure.links):
            file_path = link.get_file_path(base_path)
            if file_path and file_path.exists():
                ordered_file = OrderedFile(
                    file_path=file_path, title=link.text, order=i, level=link.level
                )
                ordered_files.append(ordered_file)

        confidence = DetectionScore.high() if ordered_files else DetectionScore.none()

        return DocumentOrder(
            files=ordered_files, method="navigation", confidence=confidence
        )

    @staticmethod
    def create_alphabetical_order(files: List[Path]) -> DocumentOrder:
        """アルファベット順の文書順序を作成"""
        ordered_files = []

        # ファイル名でソート
        sorted_files = sorted(files, key=lambda f: f.name.lower())

        for i, file_path in enumerate(sorted_files):
            # ファイル名からタイトルを生成
            title = file_path.stem.replace("_", " ").replace("-", " ").title()

            ordered_file = OrderedFile(
                file_path=file_path, title=title, order=i, level=0
            )
            ordered_files.append(ordered_file)

        confidence = DetectionScore.medium()

        return DocumentOrder(
            files=ordered_files, method="alphabetical", confidence=confidence
        )
