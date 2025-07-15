"""
TestContainerの設定テスト

DIコンテナにモックサービスを注入してテストする
"""

from dependency_injector import providers

from site2.core.containers import TestContainer
from site2.adapters.storage.file_repository import FileRepository
from tests.mocks.services import (
    MockFetchService,
    MockDetectService,
    MockBuildService,
    MockRepository,
)


def test_container_setup():
    """TestContainerが正しく設定されることを確認"""
    container = TestContainer()

    # モックサービスで上書き
    container.website_cache_repository.override(providers.Singleton(MockRepository))
    container.fetch_service.override(
        providers.Factory(
            MockFetchService,
            repository=container.website_cache_repository,
        )
    )
    container.detect_service.override(providers.Factory(MockDetectService))
    container.build_service.override(providers.Factory(MockBuildService))

    # 各サービスが正しく注入されることを確認
    fetch_service = container.fetch_service()
    assert isinstance(fetch_service, MockFetchService)

    detect_service = container.detect_service()
    assert isinstance(detect_service, MockDetectService)

    build_service = container.build_service()
    assert isinstance(build_service, MockBuildService)

    repository = container.website_cache_repository()
    assert isinstance(repository, MockRepository)


def test_service_dependencies():
    """サービス間の依存関係が正しく解決されることを確認"""
    container = TestContainer()

    # モックサービスで上書き
    container.website_cache_repository.override(providers.Singleton(MockRepository))
    container.fetch_service.override(
        providers.Factory(
            MockFetchService,
            repository=container.website_cache_repository,
        )
    )

    # 依存関係が正しく注入されることを確認
    fetch_service = container.fetch_service()
    repository = container.website_cache_repository()

    assert fetch_service.repository is repository


def test_container_isolation():
    """各テストで独立したコンテナインスタンスが使用されることを確認"""
    container1 = TestContainer()
    container2 = TestContainer()

    # 異なるインスタンスであることを確認
    assert container1 is not container2

    # モックサービスで上書き
    container1.website_cache_repository.override(providers.Singleton(MockRepository))

    # container1のみがオーバーライドされていることを確認
    repo1 = container1.website_cache_repository()
    repo2 = container2.website_cache_repository()

    assert isinstance(repo1, MockRepository)
    # container2は元の実装のまま
    assert isinstance(repo2, FileRepository)
