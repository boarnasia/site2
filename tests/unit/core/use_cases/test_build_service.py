"""
BuildServiceのテスト
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.site2.core.use_cases.build_service import BuildService
from src.site2.core.ports.build_contracts import (
    BuildServiceProtocol,
    BuildRequest,
    BuildResult,
    MarkdownConverterProtocol,
    PDFConverterProtocol,
)
from src.site2.core.ports.parser_contracts import (
    HTMLParserProtocol,
    ParseResult,
    TextExtractionResult,
    SelectorSearchResult,
)
from src.site2.core.domain.build_domain import (
    OutputFormat,
    ConvertResult,
    ExtractedContent,
    BuildError,
    DocumentMetadata,
    ContentFragment,
    ContentType,
)
from src.site2.core.domain.detect_domain import (
    OrderedFile,
    DocumentOrder,
    FileType,
    ProcessingOrder,
)


class TestBuildService:
    """BuildServiceのテストクラス"""

    def setup_method(self):
        """各テストの前処理"""
        self.mock_markdown_converter = Mock(spec=MarkdownConverterProtocol)
        self.mock_pdf_converter = Mock(spec=PDFConverterProtocol)
        self.mock_html_parser = Mock(spec=HTMLParserProtocol)

        self.build_service = BuildService(
            markdown_converter=self.mock_markdown_converter,
            pdf_converter=self.mock_pdf_converter,
            html_parser=self.mock_html_parser,
        )

        # テストデータの準備
        self.test_cache_dir = Path("/tmp/test_cache")
        self.test_output_path = Path("/tmp/test_output.md")

        self.sample_ordered_files = [
            OrderedFile(
                file_path=Path("test1.html"),
                file_type=FileType.HTML,
                processing_order=ProcessingOrder.DOCUMENT,
                order_index=0,
                metadata={},
            ),
            OrderedFile(
                file_path=Path("test2.html"),
                file_type=FileType.HTML,
                processing_order=ProcessingOrder.DOCUMENT,
                order_index=1,
                metadata={},
            ),
        ]

    def test_build_service_implements_protocol(self):
        """BuildServiceがProtocolを実装していることを確認"""
        assert isinstance(self.build_service, BuildServiceProtocol)

    def test_build_markdown_success(self):
        """Markdownビルドの成功テスト"""
        # モックの設定
        mock_extracted_content1 = ExtractedContent(  # noqa: F841
            file_path=Path("test1.html"),
            title="Test Document 1",
            fragments=[
                ContentFragment(
                    content="Test content 1",
                    content_type=ContentType.PARAGRAPH,
                    raw_content="<p>Test content 1</p>",
                    metadata={},
                )
            ],
            metadata=DocumentMetadata(title="Test Document 1"),
        )

        mock_extracted_content2 = ExtractedContent(  # noqa: F841
            file_path=Path("test2.html"),
            title="Test Document 2",
            fragments=[
                ContentFragment(
                    content="Test content 2",
                    content_type=ContentType.PARAGRAPH,
                    raw_content="<p>Test content 2</p>",
                    metadata={},
                )
            ],
            metadata=DocumentMetadata(title="Test Document 2"),
        )

        # HTMLパーサーのモック設定
        mock_soup = Mock()
        mock_soup.find.return_value.string = "Test Document"
        mock_main_element = Mock()
        mock_main_element.find.return_value.get_text.return_value = "Test Document 1"

        mock_parse_result = ParseResult(
            file_path=Path("test.html"),
            soup=mock_soup,
            encoding="utf-8",
            parse_time_seconds=0.1,
            warnings=[],
        )

        mock_selector_result = SelectorSearchResult(
            matched_selector="main", elements=[mock_main_element], search_method="find"
        )

        mock_text_result = TextExtractionResult(
            original_element=mock_main_element,
            extracted_text="Test content",
            text_length=12,
            cleaned=True,
        )

        self.mock_html_parser.parse.return_value = mock_parse_result
        self.mock_html_parser.find_by_selectors.return_value = mock_selector_result
        self.mock_html_parser.extract_text.return_value = mock_text_result

        mock_convert_result1 = ConvertResult(
            original_file=Path("test1.html"),
            content="# Test Document 1\n\nTest content 1",
            format=OutputFormat.MARKDOWN,
            title="Test Document 1",
            extracted_text_length=15,
            warnings=[],
        )

        mock_convert_result2 = ConvertResult(
            original_file=Path("test2.html"),
            content="# Test Document 2\n\nTest content 2",
            format=OutputFormat.MARKDOWN,
            title="Test Document 2",
            extracted_text_length=15,
            warnings=[],
        )

        self.mock_markdown_converter.convert.side_effect = [
            mock_convert_result1,
            mock_convert_result2,
        ]

        # テスト実行
        request = BuildRequest(
            cache_directory=self.test_cache_dir,
            main_selector="main",
            ordered_files=self.sample_ordered_files,
            doc_order=DocumentOrder(
                directory_path=Path("test"),
                file_patterns=["*.html"],
                processing_order=ProcessingOrder.DOCUMENT,
            ),
            format=OutputFormat.MARKDOWN,
            output_path=None,
            options={},
        )

        with patch.object(Path, "exists", return_value=True):
            result = self.build_service.build(request)

        # 結果の検証
        assert isinstance(result, BuildResult)
        assert result.format == OutputFormat.MARKDOWN
        assert isinstance(result.content, str)
        assert result.page_count == 2
        assert len(result.extracted_files) == 2
        assert result.statistics["total_files"] == 2

        # モックの呼び出し確認
        assert self.mock_html_parser.parse_html_file.call_count == 2
        assert self.mock_markdown_converter.convert.call_count == 2

    def test_build_pdf_success(self):
        """PDFビルドの成功テスト"""
        # モックの設定
        mock_extracted_content = ExtractedContent(
            file_path=Path("test.html"),
            title="Test PDF Document",
            fragments=[
                ContentFragment(
                    content="Test PDF content",
                    content_type=ContentType.PARAGRAPH,
                    raw_content="<p>Test PDF content</p>",
                    metadata={},
                )
            ],
            metadata=DocumentMetadata(title="Test PDF Document"),
        )

        self.mock_html_parser.parse_html_file.return_value = mock_extracted_content

        mock_pdf_result = ConvertResult(
            original_file=Path("test.html"),
            content=b"fake_pdf_content",
            format=OutputFormat.PDF,
            title="Merged PDF Document",
            extracted_text_length=17,
            warnings=[],
        )

        self.mock_pdf_converter.convert_multiple.return_value = mock_pdf_result

        # テスト実行
        request = BuildRequest(
            cache_directory=self.test_cache_dir,
            main_selector="main",
            ordered_files=[self.sample_ordered_files[0]],  # 1ファイルのみ
            doc_order=DocumentOrder(
                directory_path=Path("test"),
                file_patterns=["*.html"],
                processing_order=ProcessingOrder.DOCUMENT,
            ),
            format=OutputFormat.PDF,
            output_path=None,
            options={},
        )

        with patch.object(Path, "exists", return_value=True):
            result = self.build_service.build(request)

        # 結果の検証
        assert isinstance(result, BuildResult)
        assert result.format == OutputFormat.PDF
        assert isinstance(result.content, bytes)
        assert result.page_count == 1
        assert len(result.extracted_files) == 1

        # モックの呼び出し確認
        assert self.mock_html_parser.parse_html_file.call_count == 1
        assert self.mock_pdf_converter.convert_multiple.call_count == 1

    def test_build_with_output_file(self):
        """出力ファイル指定ありのビルドテスト"""
        # モックの設定
        mock_extracted_content = ExtractedContent(
            file_path=Path("test.html"),
            title="Test Document",
            fragments=[],
            metadata=DocumentMetadata(title="Test Document"),
        )

        self.mock_html_parser.parse_html_file.return_value = mock_extracted_content

        mock_convert_result = ConvertResult(
            original_file=Path("test.html"),
            content="# Test\n\nContent",
            format=OutputFormat.MARKDOWN,
            title="Test Document",
            extracted_text_length=7,
            warnings=[],
        )

        self.mock_markdown_converter.convert.return_value = mock_convert_result

        # テスト実行
        request = BuildRequest(
            cache_directory=self.test_cache_dir,
            main_selector="main",
            ordered_files=[self.sample_ordered_files[0]],
            doc_order=DocumentOrder(
                directory_path=Path("test"),
                file_patterns=["*.html"],
                processing_order=ProcessingOrder.DOCUMENT,
            ),
            format=OutputFormat.MARKDOWN,
            output_path=self.test_output_path,
            options={},
        )

        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", create=True) as mock_open:
                with patch.object(Path, "mkdir"):
                    result = self.build_service.build(request)

        # 結果の検証
        assert result.output_path == self.test_output_path

        # ファイル保存の確認
        mock_open.assert_called_once()

    def test_build_no_files_error(self):
        """ファイルが見つからない場合のエラーテスト"""
        request = BuildRequest(
            cache_directory=self.test_cache_dir,
            main_selector="main",
            ordered_files=[],  # 空のファイルリスト
            doc_order=DocumentOrder(
                directory_path=Path("test"),
                file_patterns=["*.html"],
                processing_order=ProcessingOrder.DOCUMENT,
            ),
            format=OutputFormat.MARKDOWN,
            output_path=None,
            options={},
        )

        with pytest.raises(BuildError) as exc_info:
            self.build_service.build(request)

        assert "No content could be extracted from any file" in str(exc_info.value)

    def test_build_unsupported_format_error(self):
        """サポートされていないフォーマットのエラーテスト"""
        mock_extracted_content = ExtractedContent(
            file_path=Path("test.html"),
            title="Test Document",
            fragments=[],
            metadata=DocumentMetadata(title="Test Document"),
        )

        self.mock_html_parser.parse_html_file.return_value = mock_extracted_content

        # 無効なフォーマットを使用
        request = BuildRequest(
            cache_directory=self.test_cache_dir,
            main_selector="main",
            ordered_files=[self.sample_ordered_files[0]],
            doc_order=DocumentOrder(
                directory_path=Path("test"),
                file_patterns=["*.html"],
                processing_order=ProcessingOrder.DOCUMENT,
            ),
            format="INVALID_FORMAT",  # 無効なフォーマット
            output_path=None,
            options={},
        )

        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(BuildError) as exc_info:
                self.build_service.build(request)

        assert "Unsupported output format" in str(exc_info.value)

    def test_build_parser_error_handling(self):
        """HTMLパーサーエラーのハンドリングテスト"""
        # パーサーが例外を発生させる
        self.mock_html_parser.parse_html_file.side_effect = Exception("Parser error")

        request = BuildRequest(
            cache_directory=self.test_cache_dir,
            main_selector="main",
            ordered_files=[self.sample_ordered_files[0]],
            doc_order=DocumentOrder(
                directory_path=Path("test"),
                file_patterns=["*.html"],
                processing_order=ProcessingOrder.DOCUMENT,
            ),
            format=OutputFormat.MARKDOWN,
            output_path=None,
            options={},
        )

        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(BuildError) as exc_info:
                self.build_service.build(request)

        assert "No content could be extracted from any file" in str(exc_info.value)

    def test_build_converter_error_handling(self):
        """コンバーターエラーのハンドリングテスト"""
        # モックの設定
        mock_extracted_content = ExtractedContent(
            file_path=Path("test.html"),
            title="Test Document",
            fragments=[],
            metadata=DocumentMetadata(title="Test Document"),
        )

        self.mock_html_parser.parse_html_file.return_value = mock_extracted_content

        # コンバーターが例外を発生させる
        self.mock_markdown_converter.convert.side_effect = Exception("Converter error")

        request = BuildRequest(
            cache_directory=self.test_cache_dir,
            main_selector="main",
            ordered_files=[self.sample_ordered_files[0]],
            doc_order=DocumentOrder(
                directory_path=Path("test"),
                file_patterns=["*.html"],
                processing_order=ProcessingOrder.DOCUMENT,
            ),
            format=OutputFormat.MARKDOWN,
            output_path=None,
            options={},
        )

        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(BuildError) as exc_info:
                self.build_service.build(request)

        assert "Build process failed" in str(exc_info.value)

    def test_combine_markdown_contents(self):
        """Markdownコンテンツ結合のテスト"""
        # テスト用のMarkdown変換結果
        results = [
            ConvertResult(
                original_file=Path("test1.html"),
                content="Content 1",
                format=OutputFormat.MARKDOWN,
                title="Document 1",
                extracted_text_length=9,
                warnings=[],
            ),
            ConvertResult(
                original_file=Path("test2.html"),
                content="Content 2",
                format=OutputFormat.MARKDOWN,
                title="Document 2",
                extracted_text_length=9,
                warnings=[],
            ),
        ]

        combined = self.build_service._combine_markdown_contents(results)

        # 結合結果の確認
        assert "# Document 1" in combined
        assert "# Document 2" in combined
        assert "Content 1" in combined
        assert "Content 2" in combined
        assert "---" in combined  # ファイル区切り
