"""
site2 fetch機能のドメインモデル定義
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set
from urllib.parse import urlparse
import hashlib


# 値オブジェクト（Value Objects）
@dataclass(frozen=True)
class WebsiteURL:
    """WebサイトのURL（値オブジェクト）"""

    value: str

    def __post_init__(self):
        parsed = urlparse(self.value)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Invalid URL scheme: {parsed.scheme}")
        if not parsed.netloc:
            raise ValueError(f"Invalid URL: {self.value}")

    @property
    def domain(self) -> str:
        """ドメイン名を取得"""
        return urlparse(self.value).netloc

    @property
    def slug(self) -> str:
        """URL からキャッシュ用のスラッグを生成"""
        # シンプルな実装: ドメイン名 + パスのハッシュ
        parsed = urlparse(self.value)
        path_hash = hashlib.md5(parsed.path.encode()).hexdigest()[:8]
        return f"{parsed.netloc}_{path_hash}"


@dataclass(frozen=True)
class CrawlDepth:
    """クロールの深さ（値オブジェクト）"""

    value: int

    def __post_init__(self):
        if not 0 <= self.value <= 10:
            raise ValueError(f"Depth must be between 0 and 10, got {self.value}")


# エンティティ（Entities）
@dataclass
class CachedPage:
    """キャッシュされたページ（エンティティ）"""

    page_url: WebsiteURL
    local_path: Path
    content_type: str
    size_bytes: int
    fetched_at: datetime
    last_modified: Optional[datetime] = None
    etag: Optional[str] = None

    @property
    def id(self) -> str:
        """エンティティの識別子"""
        return str(self.page_url.value)

    def is_stale(self, cache_duration_hours: int = 24) -> bool:
        """キャッシュが古いかどうか判定"""
        age = datetime.now() - self.fetched_at
        return age.total_seconds() > cache_duration_hours * 3600


@dataclass
class WebsiteCache:
    """Webサイトのキャッシュ（集約ルート）"""

    root_url: WebsiteURL
    cache_directory: Path
    pages: List[CachedPage] = field(default_factory=list)
    crawl_depth: CrawlDepth = CrawlDepth(3)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    @property
    def id(self) -> str:
        """集約の識別子"""
        return self.root_url.slug

    @property
    def total_size(self) -> int:
        """キャッシュの合計サイズ"""
        return sum(page.size_bytes for page in self.pages)

    @property
    def page_count(self) -> int:
        """キャッシュされたページ数"""
        return len(self.pages)

    def add_page(self, page: CachedPage) -> None:
        """ページを追加（ビジネスルール）"""
        # 同じURLのページは上書き
        self.pages = [p for p in self.pages if p.id != page.id]
        self.pages.append(page)
        self.last_updated = datetime.now()

    def get_stale_pages(self, cache_duration_hours: int = 24) -> List[CachedPage]:
        """古いページを取得"""
        return [p for p in self.pages if p.is_stale(cache_duration_hours)]

    def get_page_urls(self) -> Set[str]:
        """キャッシュ済みページのURL一覧"""
        return {page.page_url.value for page in self.pages}


# ドメインイベント（Domain Events）
@dataclass
class PageFetched:
    """ページ取得完了イベント"""

    website_cache_id: str
    page_url: str
    size_bytes: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CacheCreated:
    """キャッシュ作成イベント"""

    website_cache_id: str
    root_url: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CacheUpdated:
    """キャッシュ更新イベント"""

    website_cache_id: str
    updated_pages: int
    timestamp: datetime = field(default_factory=datetime.now)
