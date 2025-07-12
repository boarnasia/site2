"""
site2 fetch機能の契約定義（Contract-First Development）
"""

from typing import Protocol, List, Optional, Dict, Any
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, ConfigDict, HttpUrl

from ..domain.fetch_domain import WebsiteURL, WebsiteCache, CrawlDepth, CachedPage


# DTOs (Data Transfer Objects) - 外部とのやり取り用
class FetchRequest(BaseModel):
    """Fetch要求の契約"""

    model_config = ConfigDict(str_strip_whitespace=True)

    url: HttpUrl = Field(..., description="Fetch対象のURL")
    depth: CrawlDepth = Field(
        default_factory=lambda: CrawlDepth(value=3), description="クロール深度"
    )
    force_refresh: bool = Field(default=False, description="強制更新フラグ")
    cache_dir: Optional[str] = Field(default=None, description="キャッシュディレクトリ")


class FetchResult(BaseModel):
    """Fetch結果の契約"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    cache_id: str = Field(..., min_length=1, description="キャッシュID")
    root_url: HttpUrl = Field(..., description="ルートURL")
    pages_fetched: int = Field(..., ge=0, description="フェッチしたページ数")
    pages_updated: int = Field(..., ge=0, description="更新したページ数")
    total_size: int = Field(..., ge=0, description="合計サイズ")
    cache_directory: str = Field(
        ..., min_length=1, description="キャッシュディレクトリ"
    )
    errors: List[Dict[str, str]] = Field(default_factory=list, description="エラー一覧")

    @field_validator("cache_directory")
    @classmethod
    def validate_cache_directory_exists(cls, v: str) -> str:
        """キャッシュディレクトリの存在検証"""
        if not Path(v).exists():
            raise ValueError(f"Cache directory must exist: {v}")
        return v


class CacheListResult(BaseModel):
    """キャッシュ一覧の契約"""

    caches: List[Dict[str, Any]] = Field(
        default_factory=list, description="キャッシュ一覧"
    )

    @field_validator("caches")
    @classmethod
    def validate_cache_structure(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """キャッシュ構造の検証"""
        required_keys = {"id", "url", "page_count", "total_size", "last_updated"}
        for cache in v:
            missing_keys = required_keys - set(cache.keys())
            if missing_keys:
                raise ValueError(f"Each cache must have keys: {missing_keys}")
        return v


# サービスインターフェース（ポート）
class FetchServiceProtocol(Protocol):
    """Fetchサービスの契約"""

    def fetch(self, request: FetchRequest) -> FetchResult:
        """
        WebサイトをFetchしてキャッシュする

        事前条件:
        - request.url は有効なHTTP(S) URL
        - request.depth は 0-10 の範囲
        - cache_dir が指定されている場合は書き込み可能

        事後条件:
        - FetchResultが返される
        - cache_directoryが存在する
        - 少なくとも1ページ（ルートページ）がフェッチされる（エラーがない限り）

        例外:
        - NetworkError: ネットワーク接続に失敗
        - PermissionError: キャッシュディレクトリへの書き込み権限がない
        """
        ...

    def list_caches(self) -> CacheListResult:
        """
        キャッシュ済みサイトの一覧を取得

        事前条件:
        - なし

        事後条件:
        - CacheListResultが返される
        - 各キャッシュ情報が完全である
        """
        ...


# リポジトリインターフェース（ポート）
class WebsiteCacheRepositoryProtocol(Protocol):
    """キャッシュリポジトリの契約"""

    def save(self, cache: WebsiteCache) -> None:
        """
        キャッシュを保存

        事前条件:
        - cache は有効なWebsiteCacheインスタンス

        事後条件:
        - キャッシュがファイルシステムに保存される
        - メタデータが更新される
        """
        ...

    def find_by_url(self, url: WebsiteURL) -> Optional[WebsiteCache]:
        """
        URLでキャッシュを検索

        事前条件:
        - url は有効なWebsiteURL

        事後条件:
        - 存在する場合はWebsiteCacheを返す
        - 存在しない場合はNoneを返す
        """
        ...

    def find_all(self) -> List[WebsiteCache]:
        """
        すべてのキャッシュを取得

        事前条件:
        - なし

        事後条件:
        - すべてのキャッシュのリストを返す（空の可能性あり）
        """
        ...


# クローラーインターフェース（ポート）
class WebCrawlerProtocol(Protocol):
    """Webクローラーの契約"""

    def crawl(
        self,
        url: WebsiteURL,
        depth: CrawlDepth,
        existing_cache: Optional[WebsiteCache] = None,
    ) -> List[CachedPage]:
        """
        Webサイトをクロール

        事前条件:
        - url は有効なWebsiteURL
        - depth は有効なCrawlDepth

        事後条件:
        - クロールされたページのリストを返す
        - 各ページは local_path にダウンロードされている

        例外:
        - NetworkError: ネットワーク接続に失敗
        - TooManyRequestsError: レート制限に達した
        """
        ...


# エラー定義
class FetchError(Exception):
    """Fetch機能の基底エラー"""

    code: str = "FETCH_ERROR"


class NetworkError(FetchError):
    """ネットワークエラー"""

    code: str = "NETWORK_ERROR"


class InvalidURLError(FetchError):
    """無効なURLエラー"""

    code: str = "INVALID_URL"


class CachePermissionError(FetchError):
    """キャッシュ権限エラー"""

    code: str = "CACHE_PERMISSION_ERROR"
