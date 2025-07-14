"""
モックサービス実装

パイプライン統合テスト用のモックサービス
"""

from typing import List, Optional
from pathlib import Path
from datetime import datetime

from site2.core.domain.fetch_domain import WebsiteCache, WebsiteURL, CachedPage
from site2.core.domain.detect_domain import (
    MainContent,
    Navigation,
    DocumentOrder,
    NavigationStructure,
    NavLink,
    OrderedFile,
    DetectionScore,
)
from site2.core.domain.build_domain import MarkdownDocument, DocumentMetadata
from site2.core.ports.fetch_contracts import (
    FetchResult,
    FetchServiceProtocol,
    WebsiteCacheRepositoryProtocol,
)
from site2.core.ports.detect_contracts import DetectServiceProtocol
from site2.core.ports.build_contracts import BuildServiceProtocol


class MockRepository(WebsiteCacheRepositoryProtocol):
    """メモリ内でキャッシュを管理するモックリポジトリ"""

    def __init__(self):
        self._cache = {}
        self._setup_test_data()

    def _setup_test_data(self):
        """テスト用のWebsiteCacheデータを準備"""
        # テストフィクスチャのパス
        fixture_dir = (
            Path(__file__).parent.parent / "fixtures" / "websites" / "simple-site"
        )
        index_file = fixture_dir / "index.html"

        # WebsiteURLを作成
        test_url = WebsiteURL(value="http://test-site/")

        # CachedPageを作成
        cached_page = CachedPage(
            page_url=test_url,
            local_path=index_file,
            content_type="text/html",
            size_bytes=1024,
            fetched_at=datetime.now(),
        )

        # WebsiteCacheを作成
        test_cache = WebsiteCache(
            root_url=test_url,
            cache_directory=fixture_dir,
            pages=[cached_page],
            created_at=datetime.now(),
        )

        # キャッシュに追加
        self._cache["http://test-site/"] = test_cache

    def find_by_url(self, url: WebsiteURL) -> Optional[WebsiteCache]:
        return self._cache.get(str(url.value))

    def find_all(self) -> List[WebsiteCache]:
        return list(self._cache.values())


class MockFetchService(FetchServiceProtocol):
    """simple-siteのデータを返すモックサービス"""

    def __init__(self, repository: WebsiteCacheRepositoryProtocol):
        self.repository = repository

    async def execute(self, url: str) -> FetchResult:
        """リポジトリと連携したFetch結果を返す"""
        # テストフィクスチャのパス
        fixture_dir = (
            Path(__file__).parent.parent / "fixtures" / "websites" / "simple-site"
        )

        # 正しいFetchResultを返す（repositoryにキャッシュが存在することを前提）
        return FetchResult(
            cache_id="test-cache-001",
            root_url=url + "/" if not url.endswith("/") else url,
            pages_fetched=1,
            pages_updated=0,
            total_size=1024,
            cache_directory=str(fixture_dir),
            errors=[],
        )


class MockDetectService(DetectServiceProtocol):
    """固定の検出結果を返すモックサービス"""

    async def detect_main_content(self, html: str) -> MainContent:
        """main.content セレクタを返す"""
        # HTMLから簡単なテキスト抽出
        text_content = (
            "Welcome to Test Site. This is a simple test site for site2 testing."
        )

        return MainContent(
            selector="main.content",
            html_content='<main class="content"><h1>Welcome to Test Site</h1><p>This is a simple test site for site2 testing.</p></main>',
            text_content=text_content,
            title="Welcome to Test Site",
            confidence=DetectionScore.high(),
        )

    async def detect_navigation(self, html: str) -> Navigation:
        """nav.navigation セレクタを返す"""
        # モックのナビゲーション構造を作成
        nav_links = [
            NavLink(text="Home", href="index.html", level=0),
            NavLink(text="About", href="about.html", level=0),
            NavLink(text="Guide", href="docs/guide.html", level=0),
        ]

        nav_structure = NavigationStructure(
            root_selector="nav.navigation", links=nav_links
        )

        return Navigation(
            selector="nav.navigation",
            structure=nav_structure,
            confidence=DetectionScore.high(),
        )

    async def detect_order(
        self,
        cache_dir: Path,
        navigation: Navigation,  # 追加
    ) -> DocumentOrder:
        """ナビゲーション構造から順序を決定する"""
        # ナビゲーションのリンク順序に基づいて順序を作成
        files = []
        for i, link in enumerate(navigation.structure.links):
            files.append(
                OrderedFile(
                    file_path=Path(link.href),
                    order=i,
                    level=0,  # シンプルなフラット構造
                    title=link.text,
                )
            )

        return DocumentOrder(
            files=files, method="navigation", confidence=DetectionScore(value=0.95)
        )


class MockBuildService(BuildServiceProtocol):
    """簡単なMarkdownを生成するモックサービス"""

    async def build_markdown(
        self,
        contents: List[MainContent],
        doc_order: DocumentOrder,  # 追加
    ) -> MarkdownDocument:
        """順序に従ってMarkdownを生成する"""
        if not contents:
            raise ValueError("No content provided")

        # doc_orderに従ってコンテンツを並べ替え
        # （モックでは簡略化：最初のコンテンツのみ使用）
        main_content = contents[0]

        # doc_orderの情報を含めたMarkdownを生成
        content = f"# {main_content.title}\n\n"
        content += f"{main_content.text_content}\n\n"
        content += f"---\n\nDocument Order: {len(doc_order.files)} files\n"
        content += "Generated by MockBuildService\n"

        metadata = DocumentMetadata(
            title=main_content.title or "Untitled",
            source_url="http://test-site",
            description="Generated from mock service",
        )

        return MarkdownDocument(
            title=main_content.title or "Untitled",
            content=content,
            metadata=metadata,
        )
