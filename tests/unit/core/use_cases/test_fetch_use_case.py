"""
FetchServiceの単体テスト
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime

from site2.core.use_cases.fetch_use_case import FetchService
from site2.core.domain.fetch_domain import (
    WebsiteURL,
    WebsiteCache,
    CachedPage,
    CrawlDepth,
)
from site2.core.ports.fetch_contracts import (
    FetchRequest,
    FetchResult,
    NetworkError,
    CachePermissionError,
)


class TestFetchService:
    """FetchServiceのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される"""
        self.mock_crawler = Mock()
        self.mock_repository = Mock()
        self.cache_dir = Path("/tmp/test_cache")

        self.service = FetchService(
            crawler=self.mock_crawler,
            repository=self.mock_repository,
            cache_dir=self.cache_dir,
        )

    def test_fetch_new_site_success(self):
        """新規サイトのフェッチが成功すること"""
        # Arrange
        request = FetchRequest(
            url="https://example.com", depth=CrawlDepth(value=2), force_refresh=False
        )

        # リポジトリは既存キャッシュなしを返す
        self.mock_repository.find_by_url.return_value = None

        # クローラーはページリストを返す
        test_url = WebsiteURL(value="https://example.com/")
        cached_pages = [
            CachedPage(
                page_url=test_url,
                local_path=Path("/tmp/test_cache/example.com_abc123/index.html"),
                content_type="text/html",
                size_bytes=1024,
                fetched_at=datetime.now(),
            )
        ]
        self.mock_crawler.crawl.return_value = cached_pages

        # Act
        result = self.service.fetch(request)

        # Assert
        assert isinstance(result, FetchResult)
        assert str(result.root_url) == "https://example.com/"
        assert result.pages_fetched == 1
        assert result.total_size == 1024
        assert len(result.errors) == 0

        # モックが正しく呼ばれたことを確認
        self.mock_repository.find_by_url.assert_called_once()
        self.mock_crawler.crawl.assert_called_once()

    def test_fetch_cached_site_no_refresh(self):
        """キャッシュ済みサイトをforce_refresh=Falseで取得すること"""
        # Arrange
        request = FetchRequest(url="https://example.com", force_refresh=False)

        # 既存のキャッシュを準備
        test_url = WebsiteURL(value="https://example.com/")
        cached_page = CachedPage(
            page_url=test_url,
            local_path=Path("/tmp/test_cache/example.com_abc123/index.html"),
            content_type="text/html",
            size_bytes=2048,
            fetched_at=datetime.now(),
        )
        existing_cache = WebsiteCache(
            root_url=test_url,
            cache_directory=Path("/tmp/test_cache/example.com_abc123"),
            pages=[cached_page],
            created_at=datetime.now(),
        )

        self.mock_repository.find_by_url.return_value = existing_cache

        # Act
        result = self.service.fetch(request)

        # Assert
        assert result.pages_fetched == 1
        assert result.pages_updated == 0
        assert result.total_size == 2048

        # クローラーは呼ばれないことを確認（既存キャッシュが返されるため）
        self.mock_crawler.crawl.assert_not_called()

    def test_fetch_cached_site_force_refresh(self):
        """キャッシュ済みサイトをforce_refresh=Trueで更新すること"""
        # Arrange
        request = FetchRequest(url="https://example.com", force_refresh=True)

        # 既存のキャッシュ
        test_url = WebsiteURL(value="https://example.com/")
        existing_cache = WebsiteCache(
            root_url=test_url,
            cache_directory=Path("/tmp/test_cache/example.com_abc123"),
            pages=[],
            created_at=datetime.now(),
        )

        self.mock_repository.find_by_url.return_value = existing_cache

        # 更新後のページ
        updated_pages = [
            CachedPage(
                page_url=test_url,
                local_path=Path("/tmp/test_cache/example.com_abc123/index.html"),
                content_type="text/html",
                size_bytes=3072,
                fetched_at=datetime.now(),
            )
        ]
        self.mock_crawler.crawl.return_value = updated_pages

        # Act
        result = self.service.fetch(request)

        # Assert
        assert result.pages_fetched == 1
        assert result.pages_updated == 1
        assert result.total_size == 3072

        # クローラーが呼ばれたことを確認
        self.mock_crawler.crawl.assert_called_once()

    def test_fetch_with_custom_cache_dir(self):
        """カスタムキャッシュディレクトリを使用できること"""
        # Arrange
        custom_dir = "/custom/cache/dir"
        request = FetchRequest(url="https://example.com", cache_dir=custom_dir)

        self.mock_repository.find_by_url.return_value = None

        test_url = WebsiteURL(value="https://example.com/")
        expected_cache_dir = f"{custom_dir}/example.com_182ccedb"
        cached_pages = [
            CachedPage(
                page_url=test_url,
                local_path=Path(f"{expected_cache_dir}/index.html"),
                content_type="text/html",
                size_bytes=1024,
                fetched_at=datetime.now(),
            )
        ]
        self.mock_crawler.crawl.return_value = cached_pages

        # キャッシュディレクトリとファイル操作をモック
        with patch("pathlib.Path.mkdir") as mock_mkdir:  # noqa: F841
            with patch("builtins.open", create=True) as mock_open:  # noqa: F841
                with patch("pathlib.Path.exists", return_value=True):
                    # Act
                    result = self.service.fetch(request)

        # Assert
        assert custom_dir in result.cache_directory
        assert result.cache_directory == expected_cache_dir

    def test_fetch_network_error(self):
        """ネットワークエラーが適切に処理されること"""
        # Arrange
        request = FetchRequest(url="https://example.com")

        self.mock_repository.find_by_url.return_value = None
        self.mock_crawler.crawl.side_effect = NetworkError("Connection failed")

        # Act & Assert
        with pytest.raises(NetworkError, match="Connection failed"):
            self.service.fetch(request)

    def test_fetch_invalid_url_error(self):
        """無効なURLエラーが適切に処理されること"""
        # Arrange
        # Pydanticの検証エラーをテスト
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            request = FetchRequest(url="not-a-valid-url")  # noqa: F841

    def test_fetch_cache_permission_error(self):
        """キャッシュ権限エラーが適切に処理されること"""
        # Arrange
        request = FetchRequest(url="https://example.com")

        self.mock_repository.find_by_url.return_value = None

        # キャッシュディレクトリの作成でエラーを発生させる
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")

            # Act & Assert
            with pytest.raises(CachePermissionError, match="Permission denied"):
                self.service.fetch(request)

    def test_list_caches(self):
        """キャッシュ一覧が正しく取得できること"""
        # Arrange
        test_url1 = WebsiteURL(value="https://example1.com/")
        test_url2 = WebsiteURL(value="https://example2.com/")

        cache1 = WebsiteCache(
            root_url=test_url1,
            cache_directory=Path("/tmp/cache/example1.com_abc"),
            pages=[
                CachedPage(
                    page_url=test_url1,
                    local_path=Path("/tmp/cache/example1.com_abc/index.html"),
                    content_type="text/html",
                    size_bytes=1024,
                    fetched_at=datetime.now(),
                )
            ],
            created_at=datetime.now(),
        )

        cache2 = WebsiteCache(
            root_url=test_url2,
            cache_directory=Path("/tmp/cache/example2.com_def"),
            pages=[
                CachedPage(
                    page_url=test_url2,
                    local_path=Path("/tmp/cache/example2.com_def/index.html"),
                    content_type="text/html",
                    size_bytes=2048,
                    fetched_at=datetime.now(),
                )
            ],
            created_at=datetime.now(),
        )

        self.mock_repository.find_all.return_value = [cache1, cache2]

        # Act
        result = self.service.list_caches()

        # Assert
        assert len(result.caches) == 2
        assert result.caches[0]["url"] == "https://example1.com/"
        assert result.caches[0]["page_count"] == 1
        assert result.caches[0]["total_size"] == 1024
        assert result.caches[1]["url"] == "https://example2.com/"
        assert result.caches[1]["page_count"] == 1
        assert result.caches[1]["total_size"] == 2048

    def test_fetch_with_depth_parameter(self):
        """クロール深度が正しく渡されること"""
        # Arrange
        request = FetchRequest(url="https://example.com", depth=CrawlDepth(value=5))

        self.mock_repository.find_by_url.return_value = None
        self.mock_crawler.crawl.return_value = []

        # Act
        self.service.fetch(request)

        # Assert
        # クローラーに正しい深度が渡されたことを確認
        call_args = self.mock_crawler.crawl.call_args
        assert call_args[1]["depth"].value == 5  # depth parameter

    def test_fetch_creates_cache_directory(self):
        """キャッシュディレクトリが作成されること"""
        # Arrange
        request = FetchRequest(url="https://example.com")

        self.mock_repository.find_by_url.return_value = None

        test_url = WebsiteURL(value="https://example.com/")
        # 正しいキャッシュディレクトリ名を使用
        cache_dir = "/tmp/test_cache/example.com_182ccedb"
        cached_pages = [
            CachedPage(
                page_url=test_url,
                local_path=Path(f"{cache_dir}/index.html"),
                content_type="text/html",
                size_bytes=1024,
                fetched_at=datetime.now(),
            )
        ]
        self.mock_crawler.crawl.return_value = cached_pages

        # Pathオブジェクトのモック
        with patch("pathlib.Path.exists") as mock_exists:
            with patch("pathlib.Path.mkdir") as mock_mkdir:
                with patch("builtins.open", create=True) as mock_open:  # noqa: F841
                    mock_exists.return_value = True  # FetchResultの検証のため

                    # Act
                    result = self.service.fetch(request)

                    # Assert
                    # ディレクトリが作成されることを確認
                    assert result.pages_fetched == 1
                    mock_mkdir.assert_called()
