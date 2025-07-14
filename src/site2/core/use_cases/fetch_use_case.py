"""
Fetchサービスの実装

Webサイトを取得してキャッシュするサービス
"""

import hashlib
import json
from pathlib import Path
from datetime import datetime

from loguru import logger

from ..domain.fetch_domain import WebsiteURL, WebsiteCache, CachedPage
from ..ports.fetch_contracts import (
    FetchRequest,
    FetchResult,
    CacheListResult,
    FetchServiceProtocol,
    WebsiteCacheRepositoryProtocol,
    WebCrawlerProtocol,
    NetworkError,
    InvalidURLError,
    CachePermissionError,
)


class FetchService(FetchServiceProtocol):
    """Fetchサービスの実装"""

    def __init__(
        self,
        crawler: WebCrawlerProtocol,
        repository: WebsiteCacheRepositoryProtocol,
        cache_dir: Path = None,
    ):
        """
        Args:
            crawler: Webクローラー
            repository: キャッシュリポジトリ（読み取り専用）
            cache_dir: キャッシュディレクトリ（デフォルト: ~/.cache/site2）
        """
        self.crawler = crawler
        self.repository = repository
        self.cache_dir = cache_dir or (Path.home() / ".cache" / "site2")

    def fetch(self, request: FetchRequest) -> FetchResult:
        """
        WebサイトをFetchしてキャッシュする

        Args:
            request: Fetch要求

        Returns:
            FetchResult: Fetch結果

        Raises:
            NetworkError: ネットワーク接続エラー
            InvalidURLError: 無効なURL
            CachePermissionError: キャッシュディレクトリへの権限エラー
        """
        logger.info(f"Fetching website: {request.url}")

        # カスタムキャッシュディレクトリの処理
        cache_base_dir = (
            Path(request.cache_dir) if request.cache_dir else self.cache_dir
        )

        try:
            # URLの検証と正規化
            website_url = WebsiteURL(value=str(request.url))
        except Exception as e:
            raise InvalidURLError(f"Invalid URL format: {request.url}") from e

        # キャッシュIDの生成
        cache_id = self._generate_cache_id(website_url)
        cache_directory = cache_base_dir / f"{website_url.domain}_{cache_id}"

        # 既存キャッシュの確認
        existing_cache = None
        if not request.force_refresh:
            try:
                existing_cache = self.repository.find_by_url(website_url)
                if existing_cache:
                    logger.info(f"Using existing cache for {website_url}")
                    return self._create_result_from_cache(existing_cache)
            except Exception as e:
                logger.warning(f"Failed to check existing cache: {e}")

        # キャッシュディレクトリの作成
        try:
            cache_directory.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise CachePermissionError(
                f"Permission denied creating cache directory: {cache_directory}"
            ) from e

        # クローリングの実行
        try:
            logger.info(f"Crawling {website_url} with depth {request.depth.value}")
            cached_pages = self.crawler.crawl(
                url=website_url,
                depth=request.depth,
                existing_cache=existing_cache,
            )
        except NetworkError:
            raise
        except Exception as e:
            raise NetworkError(f"Failed to crawl website: {e}") from e

        # ファイルを正式なキャッシュディレクトリに移動
        moved_pages = []
        for page in cached_pages:
            # 新しいパスを計算
            relative_path = page.local_path.name
            new_path = cache_directory / relative_path

            # ファイルを移動（またはコピー）
            if page.local_path != new_path:
                try:
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    if page.local_path.exists():
                        import shutil

                        shutil.move(str(page.local_path), str(new_path))
                except Exception as e:
                    logger.warning(
                        f"Failed to move file {page.local_path} to {new_path}: {e}"
                    )
                    new_path = page.local_path  # 移動に失敗した場合は元のパスを使用
            else:
                new_path = page.local_path

            # 新しいCachedPageを作成
            moved_page = CachedPage(
                page_url=page.page_url,
                local_path=new_path,
                content_type=page.content_type,
                size_bytes=page.size_bytes,
                fetched_at=page.fetched_at,
            )

            moved_pages.append(moved_page)

        # WebsiteCacheの作成と保存
        website_cache = WebsiteCache(
            root_url=website_url,
            cache_directory=cache_directory,
            pages=moved_pages,
            created_at=datetime.now(),
        )

        # キャッシュメタデータの保存
        self._save_cache_metadata(website_cache)

        # 結果の作成
        total_size = sum(page.size_bytes for page in cached_pages)
        pages_updated = len(cached_pages) if request.force_refresh else 0

        result = FetchResult(
            cache_id=cache_id,
            root_url=str(website_url.value),
            pages_fetched=len(cached_pages),
            pages_updated=pages_updated,
            total_size=total_size,
            cache_directory=str(cache_directory),
            errors=[],
        )

        logger.info(
            f"Fetch completed: {result.pages_fetched} pages, {result.total_size} bytes"
        )

        return result

    def list_caches(self) -> CacheListResult:
        """
        キャッシュ済みサイトの一覧を取得

        Returns:
            CacheListResult: キャッシュ一覧
        """
        logger.info("Listing cached websites")

        all_caches = self.repository.find_all()

        cache_list = []
        for cache in all_caches:
            total_size = sum(page.size_bytes for page in cache.pages)
            cache_info = {
                "id": self._generate_cache_id(cache.root_url),
                "url": str(cache.root_url.value),
                "page_count": len(cache.pages),
                "total_size": total_size,
                "last_updated": cache.created_at.isoformat(),
            }
            cache_list.append(cache_info)

        logger.info(f"Found {len(cache_list)} cached websites")

        return CacheListResult(caches=cache_list)

    def _generate_cache_id(self, url: WebsiteURL) -> str:
        """キャッシュIDの生成"""
        url_str = str(url.value)
        hash_obj = hashlib.md5(url_str.encode())
        return hash_obj.hexdigest()[:8]

    def _create_result_from_cache(self, cache: WebsiteCache) -> FetchResult:
        """既存キャッシュからFetchResultを作成"""
        total_size = sum(page.size_bytes for page in cache.pages)
        cache_id = self._generate_cache_id(cache.root_url)

        # キャッシュディレクトリが存在しない場合は作成
        if not cache.cache_directory.exists():
            cache.cache_directory.mkdir(parents=True, exist_ok=True)

        return FetchResult(
            cache_id=cache_id,
            root_url=str(cache.root_url.value),
            pages_fetched=len(cache.pages),
            pages_updated=0,
            total_size=total_size,
            cache_directory=str(cache.cache_directory),
            errors=[],
        )

    def _save_cache_metadata(self, cache: WebsiteCache) -> None:
        """キャッシュメタデータをファイルに保存"""
        metadata_file = cache.cache_directory / "cache.json"

        metadata = {
            "root_url": str(cache.root_url.value),
            "created_at": cache.created_at.isoformat(),
            "pages": [
                {
                    "url": str(page.page_url.value),
                    "local_path": str(
                        page.local_path.relative_to(cache.cache_directory)
                    ),
                    "content_type": page.content_type,
                    "size_bytes": page.size_bytes,
                    "fetched_at": page.fetched_at.isoformat(),
                }
                for page in cache.pages
            ],
        }

        try:
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")
            raise CachePermissionError(f"Failed to save cache metadata: {e}") from e
