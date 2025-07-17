"""
Markdownコンバーターの単体テスト
"""

import pytest
import tempfile
from pathlib import Path

from site2.adapters.converters.markdown_converter import MarkdownifyConverter
from site2.core.ports.build_contracts import MarkdownConverterProtocol
from site2.core.domain.build_domain import (
    MarkdownConvertRequest,
    ConvertResult,
    OutputFormat,
    ConvertError,
)


class TestMarkdownifyConverter:
    """MarkdownifyConverterの単体テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.converter = MarkdownifyConverter()

    def test_markdown_converter_implements_protocol(self):
        """MarkdownifyConverterがProtocolを実装していることを確認"""
        assert isinstance(self.converter, MarkdownConverterProtocol)

    def test_convert_simple_html(self):
        """シンプルなHTMLの変換テスト"""
        # テスト用のHTMLファイルを作成
        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <main>
                    <h1>Main Title</h1>
                    <p>This is a paragraph.</p>
                    <h2>Subtitle</h2>
                    <p>Another paragraph with <strong>bold text</strong>.</p>
                </main>
            </body>
        </html>
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            test_file = Path(f.name)

        try:
            request = MarkdownConvertRequest(file_path=test_file, main_selector="main")

            result = self.converter.convert(request)

            # 結果の検証
            assert isinstance(result, ConvertResult)
            assert result.original_file == test_file
            assert result.format == OutputFormat.MARKDOWN
            assert isinstance(result.content, str)
            assert result.title == "Test Page"
            assert result.extracted_text_length > 0

            # Markdownコンテンツの検証
            content = result.content
            assert "# Main Title" in content
            assert "## Subtitle" in content
            assert "This is a paragraph." in content
            assert "**bold text**" in content

        finally:
            # テストファイルを削除
            test_file.unlink()

    def test_convert_with_include_toc(self):
        """目次を含む変換テスト"""
        html_content = """
        <html>
            <head><title>Test with TOC</title></head>
            <body>
                <main>
                    <h1>Chapter 1</h1>
                    <p>Content of chapter 1.</p>
                    <h2>Section 1.1</h2>
                    <p>Content of section 1.1.</p>
                    <h1>Chapter 2</h1>
                    <p>Content of chapter 2.</p>
                </main>
            </body>
        </html>
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            test_file = Path(f.name)

        try:
            request = MarkdownConvertRequest(
                file_path=test_file, main_selector="main", include_toc=True
            )

            result = self.converter.convert(request)

            # 目次が含まれていることを確認
            assert (
                "## Table of Contents" in result.content or "## 目次" in result.content
            )

        finally:
            test_file.unlink()

    def test_convert_with_heading_offset(self):
        """見出しオフセットを適用した変換テスト"""
        html_content = """
        <html>
            <head><title>Test Heading Offset</title></head>
            <body>
                <main>
                    <h1>Original H1</h1>
                    <h2>Original H2</h2>
                    <h3>Original H3</h3>
                </main>
            </body>
        </html>
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            test_file = Path(f.name)

        try:
            request = MarkdownConvertRequest(
                file_path=test_file,
                main_selector="main",
                heading_offset=1,  # 見出しレベルを1つ下げる
            )

            result = self.converter.convert(request)

            # 見出しレベルが調整されていることを確認
            content = result.content
            assert "## Original H1" in content  # H1 -> H2
            assert "### Original H2" in content  # H2 -> H3
            assert "#### Original H3" in content  # H3 -> H4

        finally:
            test_file.unlink()

    def test_convert_file_not_found(self):
        """存在しないファイルの変換エラーテスト"""
        non_existent_file = Path("/non/existent/file.html")
        request = MarkdownConvertRequest(
            file_path=non_existent_file, main_selector="main"
        )

        with pytest.raises(ConvertError) as exc_info:
            self.converter.convert(request)

        assert "File not found" in str(exc_info.value)

    def test_convert_invalid_selector(self):
        """無効なセレクタのエラーテスト"""
        html_content = "<html><body><p>No main content</p></body></html>"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            test_file = Path(f.name)

        try:
            request = MarkdownConvertRequest(
                file_path=test_file,
                main_selector="main",  # 存在しないセレクタ
            )

            with pytest.raises(ConvertError) as exc_info:
                self.converter.convert(request)

            assert "Content not found" in str(exc_info.value)

        finally:
            test_file.unlink()

    def test_convert_with_custom_options(self):
        """カスタムオプションでの変換テスト"""
        custom_options = {
            "strip": ["script", "style", "nav"],
            "escape_misc": False,
            "wrap": True,
        }

        converter = MarkdownifyConverter(config=custom_options)

        html_content = """
        <html>
            <head><title>Custom Options Test</title></head>
            <body>
                <nav>Navigation</nav>
                <main>
                    <h1>Title</h1>
                    <p>Content</p>
                    <script>alert('test');</script>
                </main>
            </body>
        </html>
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            test_file = Path(f.name)

        try:
            request = MarkdownConvertRequest(file_path=test_file, main_selector="main")

            result = converter.convert(request)

            # scriptタグが除去されていることを確認
            assert "alert" not in result.content

        finally:
            test_file.unlink()

    def test_convert_empty_content(self):
        """空のコンテンツの変換テスト"""
        html_content = """
        <html>
            <head><title>Empty Content</title></head>
            <body>
                <main></main>
            </body>
        </html>
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            test_file = Path(f.name)

        try:
            request = MarkdownConvertRequest(file_path=test_file, main_selector="main")

            result = self.converter.convert(request)

            # 空のコンテンツでも正常に処理されることを確認
            assert isinstance(result, ConvertResult)
            assert result.extracted_text_length == 0

        finally:
            test_file.unlink()
