"""
dependency-injectorベースのDIコンテナ

アプリケーション全体の依存関係を管理するDIコンテナの実装
"""

from dependency_injector import containers, providers

from ..config.settings import Settings

# 実装クラスは後で追加
from ..adapters.storage.file_repository import FileRepository
from ..adapters.crawlers.wget_crawler import WgetCrawler
from ..core.use_cases.fetch_service import FetchService
# from ..core.use_cases.detect_service import DetectService
# from ..core.use_cases.build_service import BuildService


class Container(containers.DeclarativeContainer):
    """アプリケーションのDIコンテナ"""

    # 設定の注入
    config = providers.Configuration()

    # 設定オブジェクト
    settings = providers.Singleton(
        Settings,
    )

    # リポジトリ層
    website_cache_repository = providers.Factory(
        FileRepository,
        cache_dir=settings.provided.cache_dir,
    )

    # インフラストラクチャ層
    web_crawler = providers.Factory(
        WgetCrawler,
        timeout=settings.provided.wget_timeout,
        user_agent=settings.provided.user_agent,
        delay=settings.provided.crawl_delay,
    )

    # アプリケーションサービス層
    fetch_service = providers.Factory(
        FetchService,
        crawler=web_crawler,
        repository=website_cache_repository,
        cache_dir=settings.provided.cache_dir,
    )

    detect_service = providers.Factory(
        # DetectService,  # 実装後に有効化
        providers.Object("placeholder"),  # 一時的なプレースホルダー
    )

    build_service = providers.Factory(
        # BuildService,  # 実装後に有効化
        providers.Object("placeholder"),  # 一時的なプレースホルダー
    )


class TestContainer(Container):
    """テスト用のDIコンテナ"""

    # テスト用の設定で上書き
    settings = providers.Singleton(
        Settings,
        test_mode=True,
        log_level="DEBUG",
        cache_dir="/tmp/site2_test_cache",
    )

    # テスト用のモックオブジェクトで上書き可能
    # web_crawler = providers.Factory(MockCrawler)
    # website_cache_repository = providers.Factory(MockRepository)
