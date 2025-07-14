"""
FileRepositoryの実装

ファイルシステムからWebsiteCacheを読み込む（読み取り専用）
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from loguru import logger

from ...core.domain.fetch_domain import WebsiteURL, WebsiteCache, CachedPage
from ...core.ports.fetch_contracts import WebsiteCacheRepositoryProtocol


class FileRepository(WebsiteCacheRepositoryProtocol):
    """ファイルシステムベースのキャッシュリポジトリ（読み取り専用）"""

    def __init__(self, cache_dir: Path = None):
        """
        Args:
            cache_dir: キャッシュディレクトリ（デフォルト: ~/.cache/site2）
        """
        self.cache_dir = cache_dir or (Path.home() / ".cache" / "site2")

    def find_by_url(self, url: WebsiteURL) -> Optional[WebsiteCache]:
        """
        URLでキャッシュを検索

        Args:
            url: 検索対象のURL

        Returns:
            Optional[WebsiteCache]: 見つかった場合はWebsiteCache、なければNone
        """
        logger.debug(f"Searching cache for URL: {url}")

        if not self.cache_dir.exists():
            logger.debug(f"Cache directory does not exist: {self.cache_dir}")
            return None

        # すべてのキャッシュディレクトリを検索
        for cache_dir in self.cache_dir.iterdir():
            if not cache_dir.is_dir():
                continue

            if cache_dir.name.startswith("."):
                continue

            cache = self._load_cache_from_directory(cache_dir)
            if cache and str(cache.root_url.value) == str(url.value):
                logger.info(f"Found cache for {url} in {cache_dir}")
                return cache

        logger.debug(f"No cache found for URL: {url}")
        return None

    def find_all(self) -> List[WebsiteCache]:
        """
        すべてのキャッシュを取得

        Returns:
            List[WebsiteCache]: すべてのキャッシュのリスト
        """
        logger.debug("Loading all caches")

        if not self.cache_dir.exists():
            logger.debug(f"Cache directory does not exist: {self.cache_dir}")
            return []

        caches = []

        # すべてのキャッシュディレクトリを読み込み
        for cache_dir in self.cache_dir.iterdir():
            if not cache_dir.is_dir():
                continue

            if cache_dir.name.startswith("."):
                continue

            cache = self._load_cache_from_directory(cache_dir)
            if cache:
                caches.append(cache)

        logger.info(f"Found {len(caches)} cached websites")
        return caches

    def _load_cache_from_directory(self, cache_dir: Path) -> Optional[WebsiteCache]:
        """
        キャッシュディレクトリからWebsiteCacheを読み込む

        Args:
            cache_dir: キャッシュディレクトリ

        Returns:
            Optional[WebsiteCache]: 読み込んだキャッシュ、失敗時はNone
        """
        metadata_file = cache_dir / "cache.json"

        if not metadata_file.exists():
            logger.warning(f"cache.json not found in {cache_dir}")
            return None

        try:
            # メタデータを読み込み
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # 必須フィールドの確認
            if "root_url" not in metadata or "pages" not in metadata:
                logger.error(
                    f"Invalid cache metadata in {cache_dir}: missing required fields"
                )
                return None

            # WebsiteURLの作成
            root_url = WebsiteURL(value=metadata["root_url"])

            # CachedPageリストの作成
            pages = []
            for page_data in metadata["pages"]:
                try:
                    page_url = WebsiteURL(value=page_data["url"])
                    local_path = cache_dir / page_data["local_path"]

                    # CachedPageを作成
                    cached_page = CachedPage(
                        page_url=page_url,
                        local_path=local_path,
                        content_type=page_data.get("content_type", "text/html"),
                        size_bytes=page_data.get("size_bytes", 0),
                        fetched_at=datetime.fromisoformat(page_data["fetched_at"]),
                    )

                    pages.append(cached_page)

                except Exception as e:
                    logger.warning(
                        f"Failed to load page {page_data.get('url', 'unknown')}: {e}"
                    )
                    continue

            # WebsiteCacheの作成
            cache = WebsiteCache(
                root_url=root_url,
                cache_directory=cache_dir,
                pages=pages,
                created_at=datetime.fromisoformat(metadata["created_at"]),
            )

            return cache

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {metadata_file}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load cache from {cache_dir}: {e}")
            return None
