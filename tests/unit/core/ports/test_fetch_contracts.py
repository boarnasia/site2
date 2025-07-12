"""
site2 fetch機能のテスト（TDD）
"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from pydantic import ValidationError

from site2.core.domain.fetch_domain import (
    WebsiteURL,
    WebsiteCache,
    CachedPage,
    CrawlDepth,
)
from site2.core.ports.fetch_contracts import (
    FetchRequest,
    FetchResult,
    CacheListResult,
    FetchServiceProtocol,
    WebsiteCacheRepositoryProtocol,
    WebCrawlerProtocol,
)


class TestFetchContracts:
    """契約のテスト"""

    @pytest.mark.fetch
    def test_fetch_request_validation(self):
        """FetchRequest の契約検証"""
        # 正常系 - Pydanticではインスタンス作成時に検証される
        request = FetchRequest(url="https://example.com", depth=CrawlDepth(value=3))
        assert str(request.url) == "https://example.com/"  # HttpUrlは正規化される
        assert request.depth.value == 3  # CrawlDepthオブジェクトの値

        # 異常系：無効なURL
        with pytest.raises(ValidationError):
            FetchRequest(url="invalid-url")

        # 異常系：無効な深さ
        with pytest.raises(ValidationError):
            FetchRequest(url="https://example.com", depth=CrawlDepth(value=11))

    @pytest.mark.fetch
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
            assert result.pages_fetched == 10
            assert result.pages_updated == 2

        # 異常系：負の値
        with pytest.raises(ValueError):
            FetchResult(
                cache_id="example.com_12345678",
                root_url="https://example.com",
                pages_fetched=-1,  # 負の値
                pages_updated=0,
                total_size=0,
                cache_directory="/cache/example.com",
            )


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
            # Pydanticでは契約はインスタンス作成時に検証済み
            # request.validate() は不要

            url = WebsiteURL(value=request.url)
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

    @pytest.mark.fetch
    def test_fetch_new_site(self, fetch_service):
        """新規サイトのフェッチ"""
        # Arrange
        request = FetchRequest(url="https://example.com")

        # Act
        with patch("pathlib.Path.exists", return_value=True):
            result = fetch_service.fetch(request)
            # Pydanticでは結果の契約はインスタンス作成時に検証済み

        # Assert
        assert result.pages_fetched >= 1
        assert result.pages_updated == 0
        assert result.total_size > 0

    @pytest.mark.fetch
    def test_fetch_invalid_url(self, fetch_service):
        """無効なURLでのフェッチ"""
        # Act & Assert - Pydanticではインスタンス作成時にValidationErrorが発生
        with pytest.raises(ValidationError):
            FetchRequest(url="not-a-url")

    @pytest.mark.fetch
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
        # Pydanticでは結果の契約はインスタンス作成時に検証済み
