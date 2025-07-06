"""
CLI fetch機能のE2Eテスト
"""

from typer.testing import CliRunner
from site2.cli import app

runner = CliRunner()


class TestCLICommands:
    """CLIコマンドのテスト"""

    def test_auto_command_help(self):
        """autoコマンドのヘルプ"""
        result = runner.invoke(app, ["auto", "--help"])
        assert result.exit_code == 0
        assert "Convert website to single markdown or PDF file" in result.stdout
        assert "--format" in result.stdout

    def test_fetch_command_help(self):
        """fetchコマンドのヘルプ"""
        result = runner.invoke(app, ["fetch", "--help"])
        assert result.exit_code == 0
        assert "Fetch and cache website content" in result.stdout

    def test_fetch_list_command(self):
        """fetch:listコマンドの実行"""
        result = runner.invoke(app, ["fetch:list"])
        assert result.exit_code == 0
        assert "List cached URIs" in result.stdout

    def test_detect_main_command_help(self):
        """detect:mainコマンドのヘルプ"""
        result = runner.invoke(app, ["detect:main", "--help"])
        assert result.exit_code == 0
        assert "Detect main content" in result.stdout

    def test_detect_nav_command_help(self):
        """detect:navコマンドのヘルプ"""
        result = runner.invoke(app, ["detect:nav", "--help"])
        assert result.exit_code == 0
        assert "Detect navigation" in result.stdout

    def test_detect_order_command_help(self):
        """detect:orderコマンドのヘルプ"""
        result = runner.invoke(app, ["detect:order", "--help"])
        assert result.exit_code == 0
        assert "Detect document order" in result.stdout

    def test_build_command_help(self):
        """buildコマンドのヘルプ"""
        result = runner.invoke(app, ["build", "--help"])
        assert result.exit_code == 0
        assert "Build output from" in result.stdout
        assert "--format" in result.stdout


class TestCLIExecution:
    """CLIコマンドの実行テスト"""

    def test_auto_with_invalid_url(self):
        """autoコマンドに無効なURLを渡した場合"""
        result = runner.invoke(app, ["auto", "not-a-url"])
        # 現時点では単純なechoなので成功する
        # 実装後はエラーになるべき
        assert result.exit_code == 0
        assert "Fetching not-a-url" in result.stdout

    def test_auto_with_format_option(self):
        """autoコマンドのformatオプション"""
        result = runner.invoke(app, ["auto", "--format", "pdf", "https://example.com"])
        assert result.exit_code == 0
        assert "outputting as pdf" in result.stdout

    def test_fetch_with_force_option(self):
        """fetchコマンドのforceオプション"""
        result = runner.invoke(app, ["fetch", "--force", "https://example.com"])
        assert result.exit_code == 0
        assert "force: True" in result.stdout

    def test_build_multiple_files(self):
        """buildコマンドに複数ファイルを指定"""
        # 注意: 現在のCLI実装では複数ファイルを受け取れない
        # 実装を修正する必要がある
        result = runner.invoke(app, ["build", "file1.html", "file2.html"])
        assert result.exit_code == 0  # または適切なエラーコード
