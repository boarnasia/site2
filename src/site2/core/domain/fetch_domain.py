"""
site2 fetch機能のドメインモデル定義
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set
import hashlib

from pydantic import BaseModel, Field, HttpUrl, ConfigDict


# 値オブジェクト（Value Objects）
class WebsiteURL(BaseModel):
    """WebサイトのURL（値オブジェクト）"""

    value: HttpUrl
    _slug: Optional[str] = None  # MD5ハッシュを使ったスラグ

    model_config = ConfigDict(
        frozen=True,
    )

    def model_post_init(self, __context):
        path_hash = hashlib.md5(self.value.path.encode()).hexdigest()[:8]
        object.__setattr__(self, "_slug", f"{self.value.host}_{path_hash}")

    @property
    def domain(self) -> str:
        return self.value.host

    @property
    def slug(self) -> str:
        return self._slug


class CrawlDepth(BaseModel):
    """クロールの深さ（値オブジェクト）"""

    value: int = Field(..., ge=0, le=10, description="0〜10の範囲")

    model_config = ConfigDict(
        frozen=True,
    )


# エンティティ（Entities）
class CachedPage(BaseModel):
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

    def read_text(self, encoding: str = "utf-8") -> str:
        """キャッシュされたHTMLコンテンツを読み込む

        Args:
            encoding: 文字エンコーディング（デフォルト: utf-8）

        Returns:
            HTMLコンテンツ

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            UnicodeDecodeError: エンコーディングエラー
        """
        return self.local_path.read_text(encoding=encoding)


# is_root_page メソッドは削除 - FetchResult.root_urlを直接使用する方がシンプル


class WebsiteCache(BaseModel):
    """Webサイトのキャッシュ（集約ルート）"""

    root_url: WebsiteURL
    cache_directory: Path
    pages: List[CachedPage] = Field(default_factory=list)
    crawl_depth: CrawlDepth = Field(default_factory=lambda: CrawlDepth(value=3))
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)

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

    # get_root_page メソッドは削除 - FetchResult.root_urlを直接使用する方がシンプル

    def add_page(self, page: CachedPage) -> None:
        """ページを追加（ビジネスルール）"""
        self.pages = [p for p in self.pages if p.id != page.id]
        self.pages.append(page)
        self.last_updated = datetime.now()

    def get_stale_pages(self, cache_duration_hours: int = 24) -> List[CachedPage]:
        """古いページを取得"""
        return [p for p in self.pages if p.is_stale(cache_duration_hours)]

    def get_page_urls(self) -> Set[str]:
        """キャッシュ済みページのURL一覧"""
        return {str(page.page_url.value) for page in self.pages}


# ドメインイベント（Domain Events）
class PageFetched(BaseModel):
    """ページ取得完了イベント"""

    website_cache_id: str = Field(..., min_length=1, description="キャッシュ ID")
    page_url: HttpUrl = Field(..., min_length=1, description="ページ URL")
    size_bytes: int = Field(..., ge=0, description="サイズ/bytes")
    timestamp: datetime = Field(default_factory=datetime.now)


class CacheCreated(BaseModel):
    """キャッシュ作成イベント"""

    website_cache_id: str = Field(..., min_length=1, description="キャッシュ ID")
    root_url: HttpUrl = Field(..., min_length=1, description="ルート URL")
    timestamp: datetime = Field(default_factory=datetime.now)


class CacheUpdated(BaseModel):
    """キャッシュ更新イベント"""

    website_cache_id: str = Field(..., min_length=1, description="Website cache ID")
    updated_pages: int = Field(..., ge=0, description="Number of updated pages")
    timestamp: datetime = Field(default_factory=datetime.now)
