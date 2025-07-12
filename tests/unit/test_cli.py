"""
site2 fetch機能のテスト（TDD）
"""

import pytest

from typer.testing import CliRunner

from site2.cli import app


class TestCLIIntegration:
    """CLIとの統合テスト（E2E風）"""

    @pytest.mark.fetch
    def test_cli_fetch_command(self):
        """CLI fetch コマンドのテスト"""
        # Typer対応のテストランナーを使用

        runner = CliRunner()
        # 実際のTyperアプリを実行してテスト
        result = runner.invoke(app, ["fetch", "https://example.com"])

        # 現在の実装では単純なechoなので、終了コードが0であることを確認
        assert result.exit_code == 0
        assert "https://example.com" in result.stdout

    @pytest.mark.fetch
    def test_cli_list_command(self):
        """CLI list コマンドのテスト"""

        runner = CliRunner()
        # 実際のTyperアプリを実行してテスト
        result = runner.invoke(app, ["fetch:list"])

        # 現在の実装では単純なechoなので、終了コードが0であることを確認
        assert result.exit_code == 0
        assert "List cached URIs" in result.stdout
