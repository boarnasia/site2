"""
ビルドパイプラインの統合テスト
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

from src.site2.core.containers import Container
from src.site2.core.domain.build_domain import OutputFormat


class TestBuildPipeline:
    """ビルドパイプラインの統合テスト"""

    def setup_method(self):
        """各テストの前処理"""
        self.container = Container()
        self.container.config.from_dict({})

        # テスト用の一時ディレクトリ
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache_dir = self.temp_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)

    def test_build_service_creation_from_container(self):
        """DIコンテナからBuildServiceが正常に作成されることを確認"""
        build_service = self.container.build_service()

        # BuildServiceが作成されることを確認
        assert build_service is not None

        # 依存関係が正しく注入されていることを確認
        assert hasattr(build_service, "_markdown_converter")
        assert hasattr(build_service, "_pdf_converter")
        assert hasattr(build_service, "_html_parser")

    def test_markdown_converter_integration(self):
        """Markdownコンバーターの統合テスト"""
        markdown_converter = self.container.markdown_converter()

        # テスト用HTMLファイルの作成
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Document</title></head>
        <body>
            <main>
                <h1>Test Heading</h1>
                <p>This is a test paragraph.</p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
            </main>
        </body>
        </html>
        """

        test_file = self.temp_dir / "test.html"
        test_file.write_text(html_content, encoding="utf-8")

        # Markdown変換をテスト
        from src.site2.core.domain.build_domain import MarkdownConvertRequest

        request = MarkdownConvertRequest(
            file_path=test_file,
            main_selector="main",
            include_toc=False,
            heading_offset=0,
        )

        result = markdown_converter.convert(request)

        # 結果の検証
        assert result is not None
        assert result.format == OutputFormat.MARKDOWN
        assert isinstance(result.content, str)
        assert "Test Heading" in result.content
        assert "test paragraph" in result.content

    @patch("src.site2.adapters.converters.pdf_converter.sync_playwright")
    def test_pdf_converter_integration(self, mock_playwright):
        """PDFコンバーターの統合テスト"""
        # Playwrightのモック設定
        mock_page = Mock()
        mock_page.pdf.return_value = b"fake_pdf_content"
        mock_browser = Mock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_playwright_instance

        pdf_converter = self.container.pdf_converter()

        # テスト用HTMLファイルの作成
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>PDF Test Document</title></head>
        <body>
            <main>
                <h1>PDF Test Heading</h1>
                <p>This is a test paragraph for PDF conversion.</p>
            </main>
        </body>
        </html>
        """

        test_file = self.temp_dir / "test_pdf.html"
        test_file.write_text(html_content, encoding="utf-8")

        # PDF変換をテスト
        from src.site2.core.domain.build_domain import PDFConvertRequest

        request = PDFConvertRequest(
            file_path=test_file, main_selector="main", options={}
        )

        result = pdf_converter.convert(request)

        # 結果の検証
        assert result is not None
        assert result.format == OutputFormat.PDF
        assert isinstance(result.content, bytes)
        assert result.content == b"fake_pdf_content"

    def test_build_service_dependencies_integration(self):
        """BuildServiceの依存関係統合テスト"""
        build_service = self.container.build_service()

        # 各コンバーターが個別に取得できることを確認
        markdown_converter = self.container.markdown_converter()
        pdf_converter = self.container.pdf_converter()
        html_parser = self.container.html_parser()

        # 全て異なるインスタンスであることを確認（Factoryパターン）
        assert build_service._markdown_converter != markdown_converter
        assert build_service._pdf_converter != pdf_converter
        assert build_service._html_parser != html_parser

    def test_container_configuration_validation(self):
        """DIコンテナの設定検証テスト"""
        # 各プロバイダーが適切に設定されていることを確認
        assert self.container.markdown_converter is not None
        assert self.container.pdf_converter is not None
        assert self.container.build_service is not None
        assert self.container.html_parser is not None

        # 設定が適切に渡されていることを確認
        markdown_converter = self.container.markdown_converter()
        pdf_converter = self.container.pdf_converter()

        # 設定が適用されていることを確認
        assert hasattr(markdown_converter, "config")
        assert hasattr(pdf_converter, "config")
        assert markdown_converter.config is not None
        assert pdf_converter.config is not None

    def test_all_services_accessibility(self):
        """全てのサービスがDIコンテナから取得できることを確認"""
        services = {
            "build_service": self.container.build_service(),
            "markdown_converter": self.container.markdown_converter(),
            "pdf_converter": self.container.pdf_converter(),
            "html_parser": self.container.html_parser(),
            "fetch_service": self.container.fetch_service(),
            "detect_service": self.container.detect_service(),
        }

        # 全てのサービスが正常に作成されることを確認
        for service_name, service_instance in services.items():
            assert service_instance is not None, f"{service_name} should not be None"

        # ログ出力でサービス作成が確認できることを検証
        print("All services created successfully:")
        for service_name in services.keys():
            print(f"  - {service_name}: ✓")

    def teardown_method(self):
        """各テストの後処理"""
        # 一時ファイルの削除
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
