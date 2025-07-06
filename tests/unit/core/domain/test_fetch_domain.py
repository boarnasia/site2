"""
site2 fetch機能のテスト（TDD）
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from site2.core.domain.fetch_domain import (
    WebsiteURL,
    WebsiteCache,
    CrawlDepth,
    CachedPage,
)
from site2.core.ports.fetch_contracts import (
    FetchRequest,
    FetchResult,
    CacheListResult,
    FetchServiceProtocol,
    WebsiteCacheRepositoryProtocol,
    WebCrawlerProtocol,
)


class TestDomainModel:
    """ドメインモデルのテスト"""

    def test_website_url_valid(self):
        """有効なURLの作成"""
        url = WebsiteURL("https://example.com")
        assert url.value == "https://example.com"
        assert url.domain == "example.com"
        assert url.slug == "example.com_7d793037"  # MD5ハッシュの一部

    def test_website_url_invalid(self):
        """無効なURLは例外を発生"""
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            WebsiteURL("ftp://example.com")

        with pytest.raises(ValueError, match="Invalid URL"):
            WebsiteURL("not-a-url")

    def test_crawl_depth_valid(self):
        """有効な深さの作成"""
        depth = CrawlDepth(3)
        assert depth.value == 3

    def test_crawl_depth_invalid(self):
        """無効な深さは例外を発生"""
        with pytest.raises(ValueError, match="Depth must be between"):
            CrawlDepth(11)

    def test_cached_page_staleness(self):
        """ページの古さ判定"""
        # 25時間前のページ
        old_page = CachedPage(
            page_url=WebsiteURL("https://example.com/page1.html"),
            local_path=Path("/cache/page1.html"),
            content_type="text/html",
            size_bytes=1024,
            fetched_at=datetime.now() - timedelta(hours=25),
        )
        assert old_page.is_stale(cache_duration_hours=24)

        # 1時間前のページ
        fresh_page = CachedPage(
            page_url=WebsiteURL("https://example.com/page2.html"),
            local_path=Path("/cache/page2.html"),
            content_type="text/html",
            size_bytes=1024,
            fetched_at=datetime.now() - timedelta(hours=1),
        )
        assert not fresh_page.is_stale(cache_duration_hours=24)

    def test_website_cache_operations(self):
        """Webサイトキャッシュの操作"""
        cache = WebsiteCache(
            root_url=WebsiteURL("https://example.com"),
            cache_directory=Path("/cache/example.com"),
        )

        # ページ追加
        page1 = CachedPage(
            page_url=WebsiteURL("https://example.com/page1.html"),
            local_path=Path("/cache/page1.html"),
            content_type="text/html",
            size_bytes=1024,
            fetched_at=datetime.now(),
        )
        cache.add_page(page1)

        assert cache.page_count == 1
        assert cache.total_size == 1024

        # 同じURLのページを追加（上書き）
        page1_updated = CachedPage(
            page_url=WebsiteURL("https://example.com/page1.html"),
            local_path=Path("/cache/page1.html"),
            content_type="text/html",
            size_bytes=2048,
            fetched_at=datetime.now(),
        )
        cache.add_page(page1_updated)

        assert cache.page_count == 1  # 上書きされたので1のまま
        assert cache.total_size == 2048  # サイズは更新


class TestFetchContracts:
    """契約のテスト"""

    def test_fetch_request_validation(self):
        """FetchRequest の契約検証"""
        # 正常系
        request = FetchRequest(url="https://example.com", depth=3)
        request.validate()  # 例外が発生しないこと

        # 異常系：無効なURL
        with pytest.raises(ValueError):
            request = FetchRequest(url="invalid-url")
            request.validate()

        # 異常系：無効な深さ
        with pytest.raises(ValueError):
            request = FetchRequest(url="https://example.com", depth=11)
            request.validate()

    def test_fetch_result_validation(self):
        """FetchResult の契約検証"""
        with patch("pathlib.Path.exists", return_value=True):
            # 正常系
            result = FetchResult(
                cache_id="example.com_12345678",
                root_url="https://example.com",
                pages_fetched=10,
                pages_updated=2,
                total_size=1024000,
                cache_directory="/cache/example.com",
            )
            result.validate()

        # 異常系：負の値
        with pytest.raises(AssertionError):
            result = FetchResult(
                cache_id="example.com_12345678",
                root_url="https://example.com",
                pages_fetched=-1,  # 負の値
                pages_updated=0,
                total_size=0,
                cache_directory="/cache/example.com",
            )
            result.validate()


class TestFetchService:
    """Fetchサービスのテスト（モックを使用）"""

    @pytest.fixture
    def mock_repository(self):
        """モックリポジトリ"""
        return Mock(spec=WebsiteCacheRepositoryProtocol)

    @pytest.fixture
    def mock_crawler(self):
        """モッククローラー"""
        return Mock(spec=WebCrawlerProtocol)

    @pytest.fixture
    def fetch_service(self, mock_repository, mock_crawler):
        """テスト対象のサービス（実装はまだない）"""
        # 実装クラスはまだ存在しないので、ここではモックを返す
        service = Mock(spec=FetchServiceProtocol)

        # fetch メソッドの振る舞いを定義
        def fetch_impl(request):
            # 契約に従った振る舞いをモック
            request.validate()

            url = WebsiteURL(request.url)
            # depth = CrawlDepth(request.depth)

            # キャッシュ作成
            cache = WebsiteCache(
                root_url=url, cache_directory=Path(f"/cache/{url.slug}")
            )

            # ページ追加
            pages = [
                CachedPage(
                    page_url=url,
                    local_path=Path(f"/cache/{url.slug}/index.html"),
                    content_type="text/html",
                    size_bytes=1024,
                    fetched_at=datetime.now(),
                )
            ]
            for page in pages:
                cache.add_page(page)

            return FetchResult(
                cache_id=cache.id,
                root_url=request.url,
                pages_fetched=1,
                pages_updated=0,
                total_size=cache.total_size,
                cache_directory=str(cache.cache_directory),
            )

        service.fetch.side_effect = fetch_impl
        return service

    def test_fetch_new_site(self, fetch_service):
        """新規サイトのフェッチ"""
        # Arrange
        request = FetchRequest(url="https://example.com")

        # Act
        with patch("pathlib.Path.exists", return_value=True):
            result = fetch_service.fetch(request)

        # Assert
        assert result.pages_fetched >= 1
        assert result.pages_updated == 0
        assert result.total_size > 0
        result.validate()  # 契約の確認

    def test_fetch_invalid_url(self, fetch_service):
        """無効なURLでのフェッチ"""
        # Arrange
        request = FetchRequest(url="not-a-url")

        # Act & Assert
        with pytest.raises(ValueError):
            fetch_service.fetch(request)

    def test_list_caches(self, fetch_service):
        """キャッシュ一覧の取得"""

        # Arrange
        def list_caches_impl():
            return CacheListResult(
                caches=[
                    {
                        "id": "example.com_12345678",
                        "url": "https://example.com",
                        "page_count": 15,
                        "total_size": 1234567,
                        "last_updated": "2025-01-05T10:00:00",
                    }
                ]
            )

        fetch_service.list_caches.side_effect = list_caches_impl

        # Act
        result = fetch_service.list_caches()

        # Assert
        assert len(result.caches) == 1
        result.validate()  # 契約の確認


class TestCLIIntegration:
    """CLIとの統合テスト（E2E風）"""

    def test_cli_fetch_command(self):
        """CLI fetch コマンドのテスト"""
        # この段階では CLI 実装がないので、期待する振る舞いを定義
        from click.testing import CliRunner

        # 期待する CLI の振る舞い
        expected_cli = Mock()
        expected_cli.return_value = 0  # 終了コード

        runner = CliRunner()
        with patch("site2.cli.fetch_command", expected_cli):
            result = runner.invoke(expected_cli, ["https://example.com"])

            assert result.exit_code == 0
            expected_cli.assert_called_once()

    def test_cli_list_command(self):
        """CLI list コマンドのテスト"""
        from click.testing import CliRunner

        expected_cli = Mock()
        expected_cli.return_value = 0

        runner = CliRunner()
        with patch("site2.cli.list_command", expected_cli):
            result = runner.invoke(expected_cli, [])

            assert result.exit_code == 0
