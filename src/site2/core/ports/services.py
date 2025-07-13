from typing import Protocol, List
from pathlib import Path

from ..domain.fetch_domain import FetchResult
from ..domain.detect_domain import MainContent, Navigation, DocumentOrder
from ..domain.build_domain import MarkdownDocument, PdfDocument


class IFetchService(Protocol):
    """Webサイト取得サービスのインターフェース"""

    async def execute(self, url: str) -> FetchResult:
        """指定されたURLからWebサイトを取得する"""
        ...


class IDetectService(Protocol):
    """コンテンツ検出サービスのインターフェース"""

    async def detect_main_content(self, html: str) -> MainContent:
        """HTMLからメインコンテンツを検出する"""
        ...

    async def detect_navigation(self, html: str) -> Navigation:
        """HTMLからナビゲーション構造を検出する"""
        ...

    async def detect_order(
        self,
        cache_dir: Path,
        navigation: Navigation,  # 重要：ナビゲーション構造から順序を決定
    ) -> DocumentOrder:
        """ナビゲーション構造を基にドキュメントの順序を決定する"""
        ...


class IBuildService(Protocol):
    """ドキュメント生成サービスのインターフェース"""

    async def build_markdown(
        self,
        contents: List[MainContent],
        doc_order: DocumentOrder,  # 重要：順序に従ってコンテンツを組み立て
    ) -> MarkdownDocument:
        """コンテンツリストを順序に従ってMarkdownドキュメントに変換する"""
        ...

    async def build_pdf(
        self, contents: List[MainContent], doc_order: DocumentOrder
    ) -> PdfDocument:
        """コンテンツリストを順序に従ってPDFドキュメントに変換する"""
        ...
