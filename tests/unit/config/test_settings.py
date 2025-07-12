"""
設定管理システムのテスト
"""

import tempfile
from pathlib import Path
from unittest.mock import patch
import os

from site2.config.settings import Settings


class TestSettings:
    """Settings クラスのテスト"""

    def test_default_settings(self):
        """デフォルト設定のテスト"""
        settings = Settings()

        assert settings.cache_duration_hours == 24
        assert settings.wget_timeout == 30
        assert settings.max_depth == 10
        assert settings.user_agent == "site2/1.0"
        assert settings.crawl_delay == 1.0
        assert settings.log_level == "INFO"
        assert settings.debug is False
        assert settings.test_mode is False
        assert settings.gemini_api_key == ""

    def test_cache_directory_creation(self):
        """キャッシュディレクトリの作成テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "test_cache"
            settings = Settings(cache_dir=cache_dir)  # noqa: F841

            # test_mode=False の場合、model_post_init でディレクトリが作成される
            assert cache_dir.exists()

    def test_test_mode_no_directory_creation(self):
        """テストモードではディレクトリを作成しないテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "test_cache"
            settings = Settings(cache_dir=cache_dir, test_mode=True)  # noqa: F841

            # test_mode=True の場合、ディレクトリは作成されない
            assert not cache_dir.exists()

    def test_environment_variable_override(self):
        """環境変数での設定上書きテスト"""
        with patch.dict(
            os.environ,
            {
                "SITE2_LOG_LEVEL": "DEBUG",
                "SITE2_DEBUG": "true",
                "SITE2_WGET_TIMEOUT": "60",
            },
        ):
            settings = Settings()

            assert settings.log_level == "DEBUG"
            assert settings.debug is True
            assert settings.wget_timeout == 60

    def test_is_development_property(self):
        """is_development プロパティのテスト"""
        # 通常モード
        settings = Settings()
        assert settings.is_development is False

        # デバッグモード
        settings = Settings(debug=True)
        assert settings.is_development is True

        # テストモード
        settings = Settings(test_mode=True)
        assert settings.is_development is True

        # 両方有効
        settings = Settings(debug=True, test_mode=True)
        assert settings.is_development is True

    def test_get_cache_path(self):
        """get_cache_path メソッドのテスト"""
        settings = Settings(cache_dir=Path("/tmp/test_cache"))

        # サブディレクトリなし
        assert settings.get_cache_path() == Path("/tmp/test_cache")

        # サブディレクトリあり
        assert settings.get_cache_path("subdir") == Path("/tmp/test_cache/subdir")

    def test_get_log_config(self):
        """get_log_config メソッドのテスト"""
        log_file = Path("/tmp/test.log")
        settings = Settings(log_level="DEBUG", log_file=log_file, debug=True)

        config = settings.get_log_config()

        assert config["level"] == "DEBUG"
        assert config["file"] == log_file
        assert config["debug"] is True
        assert "format" in config

    def test_markdown_extensions_default(self):
        """Markdown拡張のデフォルト値テスト"""
        settings = Settings()

        expected_extensions = ["extra", "codehilite", "toc"]
        assert settings.markdown_extensions == expected_extensions

    def test_pdf_options_default(self):
        """PDF オプションのデフォルト値テスト"""
        settings = Settings()

        expected_options = {
            "format": "A4",
            "margin": {"top": "1cm", "right": "1cm", "bottom": "1cm", "left": "1cm"},
        }
        assert settings.pdf_options == expected_options

    def test_env_file_loading(self):
        """環境ファイルの読み込みテスト"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".env", delete=False
        ) as env_file:
            env_file.write("SITE2_USER_AGENT=custom-agent\n")
            env_file.write("SITE2_MAX_DEPTH=5\n")
            env_file_path = env_file.name

        try:
            # 環境ファイルを指定して設定を読み込み
            settings = Settings(_env_file=env_file_path)

            assert settings.user_agent == "custom-agent"
            assert settings.max_depth == 5
        finally:
            os.unlink(env_file_path)

    def test_extra_settings_allowed(self):
        """追加設定の許可テスト"""
        # extra="allow" により、追加の設定も受け入れられる
        settings = Settings(custom_setting="test_value")

        # カスタム設定が追加されていることを確認
        assert hasattr(settings, "custom_setting")
        assert settings.custom_setting == "test_value"
