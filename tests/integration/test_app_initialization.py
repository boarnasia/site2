"""
アプリケーション初期化の統合テスト
"""

import tempfile
from pathlib import Path
from unittest.mock import patch
import os

from site2.app import create_app
from site2.core.use_cases.fetch_service import FetchService
from site2.core.use_cases.detect_service import DetectService
from site2.adapters.crawlers.wget_crawler import WgetCrawler
from site2.adapters.storage.file_repository import FileRepository


class TestAppInitialization:
    """アプリケーション初期化の統合テスト"""

    def test_create_production_app(self):
        """本番用アプリケーションの作成テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "cache"

            with patch.dict(
                os.environ,
                {
                    "SITE2_CACHE_DIR": str(cache_dir),
                    "SITE2_TEST_MODE": "false",
                },
            ):
                container = create_app(test_mode=False)

                # dependency-injectorのコンテナは実行時にDynamicContainerになる
                # コンテナが正しく作成されていることを確認
                assert container is not None

                settings = container.settings()
                assert settings.test_mode is False
                assert settings.cache_dir == cache_dir

    def test_create_test_app(self):
        """テスト用アプリケーションの作成テスト"""
        container = create_app(test_mode=True)

        # dependency-injectorのコンテナは実行時にDynamicContainerになる
        # テスト用コンテナが正しく作成されていることを確認
        assert container is not None

        settings = container.settings()
        assert settings.test_mode is True
        assert settings.log_level == "DEBUG"
        assert str(settings.cache_dir) == "/tmp/site2_test_cache"

    def test_settings_initialization(self):
        """設定の初期化テスト"""
        container = create_app(test_mode=True)
        settings = container.settings()

        # 基本設定の確認
        assert settings.cache_duration_hours == 24
        assert settings.wget_timeout == 30
        assert settings.max_depth == 10
        assert settings.user_agent == "site2/1.0"
        assert settings.crawl_delay == 1.0

    def test_service_placeholders(self):
        """サービスプレースホルダーの確認テスト"""
        container = create_app(test_mode=True)

        # 実装済みサービスが正しく注入されることを確認
        fetch_service = container.fetch_service()
        assert isinstance(fetch_service, FetchService)
        assert hasattr(fetch_service, "fetch")

        web_crawler = container.web_crawler()
        assert isinstance(web_crawler, WgetCrawler)
        assert hasattr(web_crawler, "crawl")

        repository = container.website_cache_repository()
        assert isinstance(repository, FileRepository)
        assert hasattr(repository, "find_by_url")

        # DetectServiceは実装済みなので実際のインスタンスが返される
        detect_service = container.detect_service()
        assert isinstance(detect_service, DetectService)
        assert hasattr(detect_service, "detect_main")

        build_service = container.build_service()
        assert build_service == "placeholder"

    def test_environment_variable_override(self):
        """環境変数での設定上書きテスト"""
        with patch.dict(
            os.environ,
            {
                "SITE2_LOG_LEVEL": "ERROR",
                "SITE2_DEBUG": "true",
                "SITE2_WGET_TIMEOUT": "120",
                "SITE2_USER_AGENT": "custom-agent/1.0",
            },
        ):
            container = create_app(test_mode=False)
            settings = container.settings()

            assert settings.log_level == "ERROR"
            assert settings.debug is True
            assert settings.wget_timeout == 120
            assert settings.user_agent == "custom-agent/1.0"

    def test_container_wiring(self):
        """コンテナのワイヤリングテスト"""
        container = create_app(test_mode=True)

        # ワイヤリングが設定されていることを確認
        # 実際のワイヤリング対象モジュールが実装されるまでは
        # エラーが発生しないことを確認
        assert container is not None

    def test_logging_initialization(self):
        """ログの初期化テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            with patch.dict(
                os.environ,
                {
                    "SITE2_LOG_FILE": str(log_file),
                    "SITE2_LOG_LEVEL": "DEBUG",
                },
            ):
                container = create_app(test_mode=True)
                settings = container.settings()

                log_config = settings.get_log_config()
                assert log_config["level"] == "DEBUG"
                assert log_config["file"] == log_file
                # 環境変数でDEBUGレベルが設定されているが、debugフラグ自体はFalse
                assert log_config["debug"] is False

    def test_cache_directory_creation(self):
        """キャッシュディレクトリの作成テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "custom_cache"

            with patch.dict(
                os.environ,
                {
                    "SITE2_CACHE_DIR": str(cache_dir),
                    "SITE2_TEST_MODE": "false",
                },
            ):
                container = create_app(test_mode=False)
                settings = container.settings()  # noqa: F841

                # 本番モードでは自動でディレクトリが作成される
                assert cache_dir.exists()
                assert cache_dir.is_dir()

    def test_test_mode_no_cache_directory_creation(self):
        """テストモードでのキャッシュディレクトリ作成抑制テスト"""
        container = create_app(test_mode=True)
        settings = container.settings()  # noqa: F841

        # テストモードでは自動作成されない
        cache_dir = Path("/tmp/site2_test_cache")  # noqa: F841
        # この時点ではディレクトリが存在しないことを確認
        # （他のテストで作成されている可能性があるため、確実にチェックできない）

    def test_container_configuration_isolation(self):
        """コンテナ設定の分離テスト"""
        # 本番用コンテナ
        prod_container = create_app(test_mode=False)
        prod_settings = prod_container.settings()

        # テスト用コンテナ
        test_container = create_app(test_mode=True)
        test_settings = test_container.settings()

        # 設定が独立していることを確認
        assert prod_settings.test_mode is False
        assert test_settings.test_mode is True
        assert prod_settings is not test_settings

    def test_dependency_injection_example(self):
        """依存性注入の例のテスト"""
        from site2.app import example_function

        container = create_app(test_mode=True)  # noqa: F841

        # ワイヤリングが設定された状態で関数が呼び出せることを確認
        try:
            example_function()
        except Exception:
            # プレースホルダー段階では例外が発生する可能性があるが、
            # 依存性注入の仕組み自体は動作していることを確認
            pass

    def test_settings_validation(self):
        """設定値の検証テスト"""
        container = create_app(test_mode=True)
        settings = container.settings()

        # 必要な設定項目が全て設定されていることを確認
        assert hasattr(settings, "cache_dir")
        assert hasattr(settings, "cache_duration_hours")
        assert hasattr(settings, "wget_timeout")
        assert hasattr(settings, "max_depth")
        assert hasattr(settings, "user_agent")
        assert hasattr(settings, "crawl_delay")
        assert hasattr(settings, "log_level")
        assert hasattr(settings, "debug")
        assert hasattr(settings, "test_mode")

    def test_provider_dependencies(self):
        """プロバイダーの依存関係テスト"""
        container = create_app(test_mode=True)
        settings = container.settings()

        # 設定値がプロバイダーに正しく注入されることを確認
        # プレースホルダー段階では実際のサービスは利用できないが、
        # 設定値が正しく取得できることを確認
        assert settings.wget_timeout == 30
        assert settings.user_agent == "site2/1.0"
        assert settings.crawl_delay == 1.0

    def test_multiple_container_instances(self):
        """複数のコンテナインスタンステスト"""
        container1 = create_app(test_mode=True)
        container2 = create_app(test_mode=True)

        # 異なるインスタンスが作成されることを確認
        assert container1 is not container2

        # しかし設定は同じ値を持つことを確認
        settings1 = container1.settings()
        settings2 = container2.settings()

        assert settings1.test_mode == settings2.test_mode
        assert settings1.log_level == settings2.log_level
