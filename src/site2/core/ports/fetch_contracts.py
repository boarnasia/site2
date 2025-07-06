"""
site2 fetch機能の契約定義（Contract-First Development）
"""

from typing import Protocol, List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field

from ..domain.fetch_domain import WebsiteURL, WebsiteCache, CrawlDepth, CachedPage


# DTOs (Data Transfer Objects) - 外部とのやり取り用
@dataclass
class FetchRequest:
    """Fetch要求の契約"""

    url: str
    depth: int = 3
    force_refresh: bool = False
    cache_dir: Optional[str] = None

    def validate(self) -> None:
        """契約の事前条件を検証"""
        # URLの検証はWebsiteURLに委譲
        WebsiteURL(value=self.url)
        # 深さの検証はCrawlDepthに委譲
        CrawlDepth(value=self.depth)


@dataclass
class FetchResult:
    """Fetch結果の契約"""

    cache_id: str
    root_url: str
    pages_fetched: int
    pages_updated: int
    total_size: int
    cache_directory: str
    errors: List[Dict[str, str]] = field(default_factory=list)

    def validate(self) -> None:
        """契約の事後条件を検証"""
        assert self.pages_fetched >= 0, "pages_fetched must be non-negative"
        assert self.pages_updated >= 0, "pages_updated must be non-negative"
        assert self.total_size >= 0, "total_size must be non-negative"
        assert Path(self.cache_directory).exists(), (
            f"Cache directory must exist: {self.cache_directory}"
        )


@dataclass
class CacheListResult:
    """キャッシュ一覧の契約"""

    caches: List[Dict[str, Any]]

    def validate(self) -> None:
        """契約の事後条件を検証"""
        for cache in self.caches:
            assert "id" in cache, "Each cache must have an id"
            assert "url" in cache, "Each cache must have a url"
            assert "page_count" in cache, "Each cache must have page_count"
            assert "total_size" in cache, "Each cache must have total_size"
            assert "last_updated" in cache, "Each cache must have last_updated"


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
