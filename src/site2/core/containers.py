"""
dependency-injectorベースのDIコンテナ

アプリケーション全体の依存関係を管理するDIコンテナの実装
"""

from dependency_injector import containers, providers

from ..config.settings import Settings

# 実装クラスは後で追加
from ..adapters.storage.file_repository import FileRepository
from ..adapters.crawlers.wget_crawler import WgetCrawler
from ..adapters.parsers.beautifulsoup_parser import (
    BeautifulSoupAnalyzer,
    BeautifulSoupParser,
    LLMPreprocessor,
)
from ..adapters.parsers.chardet_detector import ChardetDetector
from ..adapters.detectors.detector_factory import DetectorFactory
from ..core.use_cases.fetch_service import FetchService
from ..core.use_cases.detect_service import DetectService
# from ..core.use_cases.build_service import BuildService


class Container(containers.DeclarativeContainer):
    """アプリケーションのDIコンテナ"""

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

    # パーサー層 (Adapters)
    encoding_detector = providers.Factory(ChardetDetector)
    html_parser = providers.Factory(
        BeautifulSoupParser,
    )
    html_analyzer = providers.Factory(BeautifulSoupAnalyzer)
    llm_preprocessor = providers.Factory(LLMPreprocessor)

    # 検出器層 (Adapters)
    main_content_detector = providers.Factory(
        DetectorFactory.create,
        method="heuristic",  # 設定可能にする
        html_analyzer=html_analyzer,
        options=providers.Dict(
            enable_semantic_selectors=True,
            enable_content_analysis=True,
            enable_exclusion_filter=True,
            min_text_density=0.05,
            min_paragraph_count=2,
        ),
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
        DetectService,
        html_parser=html_parser,
        html_analyzer=html_analyzer,
        main_content_detector=main_content_detector,
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
