"""
PlaywrightPDFConverterのテスト
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.site2.adapters.converters.pdf_converter import PlaywrightPDFConverter
from src.site2.core.ports.build_contracts import PDFConverterProtocol
from src.site2.core.domain.build_domain import (
    PDFConvertRequest,
    ConvertResult,
    OutputFormat,
    ConvertError,
)


class TestPlaywrightPDFConverter:
    """PlaywrightPDFConverterのテストクラス"""

    def setup_method(self):
        """各テストの前処理"""
        self.converter = PlaywrightPDFConverter()
        self.test_html_file = Path("test.html")

    def test_pdf_converter_implements_protocol(self):
        """PlaywrightPDFConverterがProtocolを実装していることを確認"""
        assert isinstance(self.converter, PDFConverterProtocol)

    @patch("src.site2.adapters.converters.pdf_converter.sync_playwright")
    def test_convert_simple_html(self, mock_playwright):
        """シンプルなHTMLのPDF変換テスト"""
        # モックの設定
        mock_page = Mock()
        mock_page.pdf.return_value = b"fake_pdf_content"
        mock_browser = Mock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_playwright_instance

        # テスト用HTMLファイルの作成
        test_html_content = """
        <html>
        <head><title>Test Document</title></head>
        <body>
            <main>
                <h1>Test Heading</h1>
                <p>Test paragraph content.</p>
            </main>
        </body>
        </html>
        """

        # ファイル読み込みのモック
        with patch("builtins.open", mock_open_with_content(test_html_content)):
            with patch.object(Path, "exists", return_value=True):
                request = PDFConvertRequest(
                    file_path=self.test_html_file, main_selector="main", options={}
                )

                result = self.converter.convert(request)

                # 結果の検証
                assert isinstance(result, ConvertResult)
                assert result.original_file == self.test_html_file
                assert result.content == b"fake_pdf_content"
                assert result.format == OutputFormat.PDF
                assert result.title == "Test Document"
                assert result.extracted_text_length > 0

    @patch("src.site2.adapters.converters.pdf_converter.sync_playwright")
    def test_convert_with_heading_offset(self, mock_playwright):
        """見出しレベル調整を含むPDF変換テスト"""
        # モックの設定
        mock_page = Mock()
        mock_page.pdf.return_value = b"fake_pdf_content_offset"
        mock_browser = Mock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_playwright_instance

        test_html_content = """
        <html>
        <head><title>Test Document with Headings</title></head>
        <body>
            <main>
                <h1>Main Heading</h1>
                <h2>Sub Heading</h2>
                <p>Content here.</p>
            </main>
        </body>
        </html>
        """

        with patch("builtins.open", mock_open_with_content(test_html_content)):
            with patch.object(Path, "exists", return_value=True):
                request = PDFConvertRequest(
                    file_path=self.test_html_file,
                    main_selector="main",
                    options={"heading_offset": 1},  # h1->h2, h2->h3に調整
                )

                result = self.converter.convert(request)

                assert isinstance(result, ConvertResult)
                assert result.content == b"fake_pdf_content_offset"
                assert result.format == OutputFormat.PDF

    def test_convert_file_not_found(self):
        """存在しないファイルのPDF変換エラーテスト"""
        with patch.object(Path, "exists", return_value=False):
            request = PDFConvertRequest(
                file_path=self.test_html_file, main_selector="main", options={}
            )

            with pytest.raises(ConvertError) as exc_info:
                self.converter.convert(request)

            assert "File not found" in str(exc_info.value)

    def test_convert_invalid_selector(self):
        """無効なセレクタでのPDF変換エラーテスト"""
        test_html_content = """
        <html>
        <head><title>Test</title></head>
        <body>
            <div>No main element</div>
        </body>
        </html>
        """

        with patch("builtins.open", mock_open_with_content(test_html_content)):
            with patch.object(Path, "exists", return_value=True):
                request = PDFConvertRequest(
                    file_path=self.test_html_file,
                    main_selector="main",  # 存在しないセレクタ
                    options={},
                )

                with pytest.raises(ConvertError) as exc_info:
                    self.converter.convert(request)

                assert "PDF conversion failed" in str(exc_info.value)

    @patch("src.site2.adapters.converters.pdf_converter.sync_playwright")
    @patch("src.site2.adapters.converters.pdf_converter.PdfWriter")
    @patch("src.site2.adapters.converters.pdf_converter.PdfReader")
    def test_convert_multiple_with_merge(
        self, mock_pdf_reader, mock_pdf_writer, mock_playwright
    ):
        """複数ファイルのPDF変換（結合あり）テスト"""
        # Playwrightモックの設定
        mock_page = Mock()
        mock_page.pdf.return_value = b"fake_pdf_content"
        mock_browser = Mock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_playwright_instance

        # PDF結合モックの設定
        mock_writer_instance = Mock()
        mock_pdf_writer.return_value = mock_writer_instance
        mock_writer_instance.write = Mock()

        mock_reader_instance = Mock()
        mock_reader_instance.pages = [Mock(), Mock()]  # 2ページ
        mock_pdf_reader.return_value = mock_reader_instance

        test_html_content_1 = """
        <html><head><title>Doc 1</title></head>
        <body><main><h1>Document 1</h1><p>Content 1</p></main></body></html>
        """

        test_html_content_2 = """
        <html><head><title>Doc 2</title></head>
        <body><main><h1>Document 2</h1><p>Content 2</p></main></body></html>
        """

        # ファイル読み込みモックの設定
        def mock_open_side_effect(file_path, *args, **kwargs):
            if str(file_path).endswith("test1.html"):
                return mock_open_with_content(test_html_content_1)()
            elif str(file_path).endswith("test2.html"):
                return mock_open_with_content(test_html_content_2)()
            return mock_open_with_content("")()

        with patch("builtins.open", side_effect=mock_open_side_effect):
            with patch.object(Path, "exists", return_value=True):
                with patch("io.BytesIO") as mock_bytesio:
                    mock_stream = Mock()
                    mock_stream.read.return_value = b"merged_pdf_content"
                    mock_bytesio.return_value = mock_stream

                    requests = [
                        PDFConvertRequest(
                            file_path=Path("test1.html"),
                            main_selector="main",
                            options={},
                        ),
                        PDFConvertRequest(
                            file_path=Path("test2.html"),
                            main_selector="main",
                            options={},
                        ),
                    ]

                    result = self.converter.convert_multiple(requests, merge=True)

                    assert isinstance(result, ConvertResult)
                    assert result.content == b"merged_pdf_content"
                    assert result.format == OutputFormat.PDF
                    assert "Doc 1 + Doc 2" in result.title

    @patch("src.site2.adapters.converters.pdf_converter.sync_playwright")
    def test_convert_multiple_without_merge(self, mock_playwright):
        """複数ファイルのPDF変換（結合なし）テスト"""
        # Playwrightモックの設定
        mock_page = Mock()
        mock_page.pdf.return_value = b"fake_pdf_content"
        mock_browser = Mock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_playwright_instance

        test_html_content = """
        <html><head><title>Test Doc</title></head>
        <body><main><h1>Test</h1><p>Content</p></main></body></html>
        """

        with patch("builtins.open", mock_open_with_content(test_html_content)):
            with patch.object(Path, "exists", return_value=True):
                requests = [
                    PDFConvertRequest(
                        file_path=Path("test1.html"), main_selector="main", options={}
                    ),
                    PDFConvertRequest(
                        file_path=Path("test2.html"), main_selector="main", options={}
                    ),
                ]

                results = self.converter.convert_multiple(requests, merge=False)

                assert isinstance(results, list)
                assert len(results) == 2
                for result in results:
                    assert isinstance(result, ConvertResult)
                    assert result.format == OutputFormat.PDF

    def test_convert_with_custom_config(self):
        """カスタム設定でのPDF変換テスト"""
        custom_config = {
            "format": "A3",
            "print_background": False,
            "margin": {
                "top": "10mm",
                "right": "10mm",
                "bottom": "10mm",
                "left": "10mm",
            },
        }

        converter = PlaywrightPDFConverter(config=custom_config)
        assert converter.config["format"] == "A3"
        assert converter.config["print_background"] is False

    def test_convert_empty_content(self):
        """空のコンテンツのPDF変換テスト"""
        test_html_content = """
        <html>
        <head><title>Empty Document</title></head>
        <body>
            <main></main>
        </body>
        </html>
        """

        with patch(
            "src.site2.adapters.converters.pdf_converter.sync_playwright"
        ) as mock_playwright:
            mock_page = Mock()
            mock_page.pdf.return_value = b"empty_pdf_content"
            mock_browser = Mock()
            mock_browser.new_page.return_value = mock_page
            mock_playwright_instance = Mock()
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            mock_playwright.return_value.__enter__.return_value = (
                mock_playwright_instance
            )

            with patch("builtins.open", mock_open_with_content(test_html_content)):
                with patch.object(Path, "exists", return_value=True):
                    request = PDFConvertRequest(
                        file_path=self.test_html_file, main_selector="main", options={}
                    )

                    result = self.converter.convert(request)

                    assert isinstance(result, ConvertResult)
                    assert result.extracted_text_length == 0
                    assert "No text content extracted" in result.warnings


def mock_open_with_content(content: str):
    """指定されたコンテンツでファイルを開くモック"""
    from unittest.mock import mock_open

    return mock_open(read_data=content)
