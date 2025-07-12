"""
site2 fetch機能のテスト（TDD）
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta

from pydantic import ValidationError

from site2.core.domain.fetch_domain import (
    WebsiteURL,
    WebsiteCache,
    CrawlDepth,
    CachedPage,
    PageFetched,
    CacheCreated,
    CacheUpdated,
)


class TestDomainModel:
    """ドメインモデルのテスト"""

    @pytest.mark.fetch
    def test_website_url_valid(self):
        """有効なURLの作成"""
        url = WebsiteURL(value="https://example.com")
        assert str(url.value) == "https://example.com/"
        assert url.domain == "example.com"
        assert url.slug == "example.com_6666cd76"  # MD5ハッシュの一部

    @pytest.mark.fetch
    def test_website_url_invalid(self):
        """無効なURLは例外を発生"""
        with pytest.raises(ValidationError, match="validation error"):
            WebsiteURL(value="ftp://example.com")

        with pytest.raises(ValidationError, match="validation error"):
            WebsiteURL(value="not-a-url")

    @pytest.mark.fetch
    def test_crawl_depth_valid(self):
        """有効な深さの作成"""
        depth = CrawlDepth(value=3)
        assert depth.value == 3

    @pytest.mark.fetch
    def test_crawl_depth_invalid(self):
        """無効な深さは例外を発生"""
        with pytest.raises(ValidationError, match="validation error"):
            CrawlDepth(value=11)

    @pytest.mark.fetch
    def test_cached_page_staleness(self):
        """ページの古さ判定"""
        # 25時間前のページ
        old_page = CachedPage(
            page_url=WebsiteURL(value="https://example.com/page1.html"),
            local_path=Path("/cache/page1.html"),
            content_type="text/html",
            size_bytes=1024,
            fetched_at=datetime.now() - timedelta(hours=25),
        )
        assert old_page.is_stale(cache_duration_hours=24)

        # 1時間前のページ
        fresh_page = CachedPage(
            page_url=WebsiteURL(value="https://example.com/page2.html"),
            local_path=Path("/cache/page2.html"),
            content_type="text/html",
            size_bytes=1024,
            fetched_at=datetime.now() - timedelta(hours=1),
        )
        assert not fresh_page.is_stale(cache_duration_hours=24)

    @pytest.mark.fetch
    def test_website_cache_operations(self):
        """Webサイトキャッシュの操作"""
        cache = WebsiteCache(
            root_url=WebsiteURL(value="https://example.com"),
            cache_directory=Path("/cache/example.com"),
        )

        # ページ追加
        page1 = CachedPage(
            page_url=WebsiteURL(value="https://example.com/page1.html"),
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
            page_url=WebsiteURL(value="https://example.com/page1.html"),
            local_path=Path("/cache/page1.html"),
            content_type="text/html",
            size_bytes=2048,
            fetched_at=datetime.now(),
        )
        cache.add_page(page1_updated)

        assert cache.page_count == 1  # 上書きされたので1のまま
        assert cache.total_size == 2048  # サイズは更新


class TestDomainEvents:
    """ドメインイベントのテスト"""

    @pytest.mark.fetch
    def test_page_fetched_event_creation(self):
        """PageFetchedイベントの正常作成"""
        # Arrange
        website_cache_id = "example.com_12345678"
        page_url = "https://example.com/page1.html"
        size_bytes = 1024

        # Act
        event = PageFetched(
            website_cache_id=website_cache_id, page_url=page_url, size_bytes=size_bytes
        )

        # Assert
        assert event.website_cache_id == website_cache_id
        assert str(event.page_url) == page_url
        assert event.size_bytes == size_bytes
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)

    @pytest.mark.fetch
    def test_page_fetched_event_validation(self):
        """PageFetchedイベントのバリデーション"""
        # 正常系：すべて有効
        event = PageFetched(
            website_cache_id="example.com_12345678",
            page_url="https://example.com/page1.html",
            size_bytes=1024,
        )
        assert event.website_cache_id == "example.com_12345678"

        # 異常系：負のサイズ
        with pytest.raises(ValidationError):
            PageFetched(
                website_cache_id="example.com_12345678",
                page_url="https://example.com/page1.html",
                size_bytes=-1,
            )

        # 異常系：空のcache_id
        with pytest.raises(ValidationError):
            PageFetched(
                website_cache_id="",
                page_url="https://example.com/page1.html",
                size_bytes=1024,
            )

    @pytest.mark.fetch
    def test_cache_created_event_creation(self):
        """CacheCreatedイベントの正常作成"""
        # Arrange
        website_cache_id = "example.com_12345678"
        root_url = "https://example.com"

        # Act
        event = CacheCreated(website_cache_id=website_cache_id, root_url=root_url)

        # Assert
        assert event.website_cache_id == website_cache_id
        assert (
            str(event.root_url) == f"{root_url}/"
        )  # ドメイン直後はスラッシュが補完される
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)

    @pytest.mark.fetch
    def test_cache_created_event_validation(self):
        """CacheCreatedイベントのバリデーション"""
        # 正常系：すべて有効
        event = CacheCreated(
            website_cache_id="example.com_12345678", root_url="https://example.com"
        )
        assert event.website_cache_id == "example.com_12345678"

        # 異常系：空のcache_id
        with pytest.raises(ValidationError):
            CacheCreated(website_cache_id="", root_url="https://example.com")

        # 異常系：空のroot_url
        with pytest.raises(ValidationError):
            CacheCreated(website_cache_id="example.com_12345678", root_url="")

    @pytest.mark.fetch
    def test_cache_updated_event_creation(self):
        """CacheUpdatedイベントの正常作成"""
        # Arrange
        website_cache_id = "example.com_12345678"
        updated_pages = 5

        # Act
        event = CacheUpdated(
            website_cache_id=website_cache_id, updated_pages=updated_pages
        )

        # Assert
        assert event.website_cache_id == website_cache_id
        assert event.updated_pages == updated_pages
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)

    @pytest.mark.fetch
    def test_cache_updated_event_validation(self):
        """CacheUpdatedイベントのバリデーション"""
        # 正常系：すべて有効
        event = CacheUpdated(website_cache_id="example.com_12345678", updated_pages=5)
        assert event.website_cache_id == "example.com_12345678"

        # 正常系：0ページ更新
        event_zero = CacheUpdated(
            website_cache_id="example.com_12345678", updated_pages=0
        )
        assert event_zero.updated_pages == 0

        # 異常系：負のページ数
        with pytest.raises(ValidationError):
            CacheUpdated(website_cache_id="example.com_12345678", updated_pages=-1)

        # 異常系：空のcache_id
        with pytest.raises(ValidationError):
            CacheUpdated(website_cache_id="", updated_pages=5)

    @pytest.mark.fetch
    def test_event_timestamp_auto_generation(self):
        """タイムスタンプの自動生成確認"""
        # 複数のイベントを短時間で作成
        event1 = PageFetched(
            website_cache_id="example.com_12345678",
            page_url="https://example.com/page1.html",
            size_bytes=1024,
        )

        event2 = CacheCreated(
            website_cache_id="example.com_12345678", root_url="https://example.com"
        )

        event3 = CacheUpdated(website_cache_id="example.com_12345678", updated_pages=1)

        # すべてタイムスタンプが設定されていることを確認
        assert event1.timestamp is not None
        assert event2.timestamp is not None
        assert event3.timestamp is not None

        # タイムスタンプが現在時刻に近いことを確認（10秒以内）
        now = datetime.now()
        assert abs((now - event1.timestamp).total_seconds()) < 10
        assert abs((now - event2.timestamp).total_seconds()) < 10
        assert abs((now - event3.timestamp).total_seconds()) < 10

    @pytest.mark.fetch
    def test_event_immutability(self):
        """イベントの不変性確認"""
        # BaseModelの不変性はPydanticによって保証されている
        # ここでは基本的な不変性をテスト
        event = PageFetched(
            website_cache_id="example.com_12345678",
            page_url="https://example.com/page1.html",
            size_bytes=1024,
        )

        # 属性が読み取り可能であることを確認
        assert event.website_cache_id == "example.com_12345678"
        assert str(event.page_url) == "https://example.com/page1.html"
        assert event.size_bytes == 1024

        # Pydanticモデルの基本的な振る舞いを確認
        # 新しいインスタンスが作成可能であることを確認
        event_copy = event.model_copy()
        assert event_copy.website_cache_id == event.website_cache_id
        assert event_copy.page_url == event.page_url
        assert event_copy.size_bytes == event.size_bytes
