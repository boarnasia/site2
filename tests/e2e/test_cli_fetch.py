import shutil
from pathlib import Path
from typer.testing import CliRunner
from site2 import cli

runner = CliRunner()


class TestCLICommands:
    """CLIコマンドのヘルプ表示テスト"""

    def setup_method(self):
        """各テストの前にコンテナとキャッシュをセットアップ"""
        cli.container = cli.setup_container()
        # テスト用のキャッシュディレクトリをクリーンアップ
        cache_dir = Path(cli.container.settings().cache_dir)
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
        cache_dir.mkdir(parents=True)

    def test_auto_command_help(self):
        """autoコマンドのヘルプ"""
        result = runner.invoke(cli.app, ["auto", "--help"])
        assert result.exit_code == 0
        assert "Convert website to single markdown or PDF file" in result.stdout

    def test_fetch_command_help(self):
        """fetchコマンドのヘルプ"""
        result = runner.invoke(cli.app, ["fetch", "--help"])
        assert result.exit_code == 0
        assert "Webサイトをフェッチしてキャッシュする" in result.stdout

    def test_fetch_list_command_empty(self):
        """fetch:listコマンドが空の状態で正しく動作するか"""
        result = runner.invoke(cli.app, ["fetch:list"])
        assert result.exit_code == 0
        assert "キャッシュされたWebサイトはありません" in result.stdout

    def test_detect_main_command_help(self):
        """detect:mainコマンドのヘルプ"""
        result = runner.invoke(cli.app, ["detect:main", "--help"])
        assert result.exit_code == 0
        assert "Detect CSS selector for main content block" in result.stdout

    def test_detect_nav_command_help(self):
        """detect:navコマンドのヘルプ"""
        result = runner.invoke(cli.app, ["detect:nav", "--help"])
        assert result.exit_code == 0
        assert "Detect CSS selector for navigation block" in result.stdout

    def test_detect_order_command_help(self):
        """detect:orderコマンドのヘルプ"""
        result = runner.invoke(cli.app, ["detect:order", "--help"])
        assert result.exit_code == 0
        assert "Detect and output document order to stdout" in result.stdout

    def test_build_command_help(self):
        """buildコマンドのヘルプ"""
        result = runner.invoke(cli.app, ["build", "--help"])
        assert result.exit_code == 0
        assert "Build and merge files/URIs" in result.stdout


class TestCLIExecution:
    """CLIコマンドの実行テスト"""

    def setup_method(self):
        """各テストの前にコンテナをセットアップ"""
        cli.container = cli.setup_container()

    def test_auto_with_invalid_url(self):
        """autoコマンドに無効なURLを渡した場合"""
        result = runner.invoke(cli.app, ["auto", "not-a-url"])
        assert result.exit_code == 0
        assert "Fetching not-a-url" in result.stdout

    def test_auto_with_format_option(self):
        """autoコマンドのformatオプション"""
        result = runner.invoke(
            cli.app, ["auto", "--format", "pdf", "https://example.com"]
        )
        assert result.exit_code == 0
        assert "outputting as pdf" in result.stdout

    def test_fetch_with_force_option(self):
        """fetchコマンドのforceオプション"""
        # このテストは実際のネットワークアクセスに依存するため、より高度なモックが必要
        # ここではコマンドがエラーなく実行されることのみを確認
        result = runner.invoke(cli.app, ["fetch", "--force", "https://example.com"])
        assert result.exit_code == 0

    def test_build_multiple_files(self):
        """buildコマンドに複数ファイルを指定"""
        result = runner.invoke(cli.app, ["build", "file1.html", "file2.html"])
        assert result.exit_code == 0
