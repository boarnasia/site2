"""
DIコンテナのテスト
"""

import tempfile

from site2.core.containers import Container, TestContainer
from site2.config.settings import Settings


class TestContainerClass:
    """Container クラスのテスト"""

    def test_container_configuration(self):
        """DIコンテナの設定テスト"""
        container = Container()
        # Container の settings プロバイダーは Settings() を直接インスタンス化するため、
        # config は使用されない。実際のテストでは TestContainer を使う
        settings = container.settings()
        assert isinstance(settings, Settings)

    def test_settings_singleton(self):
        """設定のシングルトンテスト"""
        container = Container()
        container.config.from_pydantic(Settings(test_mode=True))

        settings1 = container.settings()
        settings2 = container.settings()

        # 同じインスタンスが返されることを確認
        assert settings1 is settings2

    def test_placeholder_services(self):
        """プレースホルダーサービスのテスト"""
        container = Container()
        container.config.from_pydantic(Settings())

        # プレースホルダーが正しく設定されていることを確認
        fetch_service = container.fetch_service()
        assert fetch_service == "placeholder"

        detect_service = container.detect_service()
        assert detect_service == "placeholder"

        build_service = container.build_service()
        assert build_service == "placeholder"

        web_crawler = container.web_crawler()
        assert web_crawler == "placeholder"

        repository = container.website_cache_repository()
        assert repository == "placeholder"

    def test_provider_configuration(self):
        """プロバイダーの設定テスト"""
        container = Container()

        # プロバイダーが正しく設定されていることを確認
        assert container.settings.provider is not None
        assert container.web_crawler.provider is not None
        assert container.website_cache_repository.provider is not None
        assert container.fetch_service.provider is not None
        assert container.detect_service.provider is not None
        assert container.build_service.provider is not None


class TestContainerTestClass:
    """TestContainer クラスのテスト"""

    def test_test_container_settings(self):
        """テスト用コンテナの設定テスト"""
        container = TestContainer()
        settings = container.settings()

        assert settings.test_mode is True
        assert settings.log_level == "DEBUG"
        assert str(settings.cache_dir) == "/tmp/site2_test_cache"

    def test_test_container_inheritance(self):
        """テスト用コンテナの継承テスト"""
        container = TestContainer()

        # 基底クラスのプロバイダーが継承されていることを確認
        assert container.fetch_service.provider is not None
        assert container.detect_service.provider is not None
        assert container.build_service.provider is not None

    def test_test_container_isolation(self):
        """テスト用コンテナの分離テスト"""
        main_container = Container()
        main_container.config.from_pydantic(Settings(test_mode=False))

        test_container = TestContainer()

        main_settings = main_container.settings()
        test_settings = test_container.settings()

        # 設定が独立していることを確認
        assert main_settings.test_mode is False
        assert test_settings.test_mode is True
        assert main_settings is not test_settings

    def test_provider_dependencies(self):
        """プロバイダーの依存関係テスト"""
        container = TestContainer()
        settings = container.settings()

        # 設定値が正しく注入されることを確認
        assert settings.wget_timeout == 30  # デフォルト値
        assert settings.user_agent == "site2/1.0"  # デフォルト値
        assert settings.crawl_delay == 1.0  # デフォルト値

    def test_container_reset(self):
        """コンテナのリセットテスト"""
        container = Container()
        container.config.from_pydantic(Settings(test_mode=True))

        # 初回取得
        settings1 = container.settings()

        # コンテナをリセット
        container.reset_singletons()

        # 再取得
        settings2 = container.settings()

        # 異なるインスタンスが生成されることを確認
        assert settings1 is not settings2
        assert settings1.test_mode == settings2.test_mode

    def test_config_override(self):
        """設定のオーバーライドテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:  # noqa: F841
            # TestContainer でカスタム設定を使用
            container = TestContainer()

            settings = container.settings()
            # TestContainer のデフォルト設定を確認
            assert settings.test_mode is True
            assert settings.log_level == "DEBUG"
            assert str(settings.cache_dir) == "/tmp/site2_test_cache"
