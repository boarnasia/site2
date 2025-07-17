"""
ビルドサービスの実装
"""

from pathlib import Path
from typing import List, Any
from loguru import logger

from ..ports.build_contracts import (
    BuildServiceProtocol,
    BuildRequest,
    BuildResult,
    MarkdownConverterProtocol,
    PDFConverterProtocol,
)
from ..ports.parser_contracts import (
    HTMLParserProtocol,
    ParseRequest,
    TextExtractionRequest,
)
from ..domain.build_domain import (
    OutputFormat,
    MarkdownConvertRequest,
    PDFConvertRequest,
    ConvertResult,
    ExtractedContent,
    BuildError,
    DocumentMetadata,
    ContentFragment,
    ContentType,
)
from ..domain.detect_domain import OrderedFile


class BuildService(BuildServiceProtocol):
    """
    ビルドサービスの実装

    複数のHTMLファイルを指定されたフォーマット（Markdown/PDF）に変換し、
    結合されたドキュメントを生成します。
    """

    def __init__(
        self,
        markdown_converter: MarkdownConverterProtocol,
        pdf_converter: PDFConverterProtocol,
        html_parser: HTMLParserProtocol,
    ):
        """
        Args:
            markdown_converter: Markdownコンバーター
            pdf_converter: PDFコンバーター
            html_parser: HTMLパーサー
        """
        self._markdown_converter = markdown_converter
        self._pdf_converter = pdf_converter
        self._html_parser = html_parser
        logger.debug("BuildService initialized with all required converters")

    def build(self, request: BuildRequest) -> BuildResult:
        """
        ドキュメントのビルド

        Args:
            request: ビルド要求

        Returns:
            BuildResult: ビルド結果

        Raises:
            BuildError: ビルド処理に失敗した場合
        """
        logger.info(
            f"Starting build process. Format: {request.format}, Files: {len(request.ordered_files)}"
        )

        try:
            # 1. ordered_filesを順番に処理してコンテンツを抽出
            extracted_contents = self._extract_contents_from_files(
                request.ordered_files, request.main_selector
            )

            # 2. 指定されたフォーマットで変換
            if request.format == OutputFormat.MARKDOWN:
                build_result = self._build_markdown(request, extracted_contents)
            elif request.format == OutputFormat.PDF:
                build_result = self._build_pdf(request, extracted_contents)
            else:
                raise BuildError(f"Unsupported output format: {request.format}")

            # 3. 出力パスが指定されている場合はファイルに保存
            if request.output_path:
                self._save_to_file(build_result, request.output_path)

            logger.info(
                f"Build completed successfully. Output size: {len(build_result.content)} bytes"
            )
            return build_result

        except Exception as e:
            error_msg = f"Build process failed: {str(e)}"
            logger.error(error_msg)
            raise BuildError(error_msg)

    def _extract_contents_from_files(
        self, ordered_files: List[OrderedFile], main_selector: str
    ) -> List[ExtractedContent]:
        """
        ファイルリストからコンテンツを抽出

        Args:
            ordered_files: 順序付きファイル一覧
            main_selector: メインコンテンツセレクタ

        Returns:
            List[ExtractedContent]: 抽出されたコンテンツ一覧
        """
        extracted_contents = []

        for ordered_file in ordered_files:
            try:
                logger.debug(f"Extracting content from: {ordered_file.file_path}")

                # HTMLパーサーを使用してHTMLをパース
                parse_request = ParseRequest(file_path=ordered_file.file_path)
                parse_result = self._html_parser.parse(parse_request)

                # メインコンテンツを選択
                from ..ports.parser_contracts import SelectorSearchRequest

                selector_request = SelectorSearchRequest(
                    soup=parse_result.soup, selectors=[main_selector], find_all=False
                )
                selector_result = self._html_parser.find_by_selectors(selector_request)

                if not selector_result.elements:
                    logger.warning(
                        f"No content found with selector '{main_selector}' in {ordered_file.file_path}"
                    )
                    continue

                # ExtractedContentを構築
                extracted_content = self._build_extracted_content(
                    ordered_file.file_path, selector_result.elements[0], parse_result
                )

                extracted_contents.append(extracted_content)

            except Exception as e:
                logger.warning(
                    f"Failed to extract content from {ordered_file.file_path}: {str(e)}"
                )
                # 失敗したファイルは警告のみで処理を継続
                continue

        if not extracted_contents:
            raise BuildError("No content could be extracted from any file")

        logger.info(
            f"Successfully extracted content from {len(extracted_contents)} files"
        )
        return extracted_contents

    def _build_extracted_content(
        self, file_path: Path, main_element: Any, parse_result: Any
    ) -> ExtractedContent:
        """
        ExtractedContentオブジェクトを構築

        Args:
            file_path: ファイルパス
            main_element: メイン要素（BeautifulSoup Tag）
            parse_result: パース結果

        Returns:
            ExtractedContent: 抽出されたコンテンツ
        """
        # タイトルを抽出
        title = "Untitled"
        title_tag = parse_result.soup.find("title")
        if title_tag and title_tag.string:
            title = title_tag.string.strip()
        elif main_element.find("h1"):
            title = main_element.find("h1").get_text(strip=True)

        # テキストを抽出
        text_request = TextExtractionRequest(
            element=main_element,
            remove_scripts=True,
            remove_styles=True,
            clean_whitespace=True,
        )
        text_result = self._html_parser.extract_text(text_request)

        # ContentFragmentを作成
        fragment = ContentFragment(
            content_type=ContentType.PARAGRAPH,  # 簡単のため全てPARAGRAPHとする
            raw_content=str(main_element),
            formatted_content=text_result.extracted_text,  # フォーマット済みコンテンツ
            metadata={},
        )

        # DocumentMetadataを作成
        metadata = DocumentMetadata(title=title)

        return ExtractedContent(
            file_path=file_path, title=title, fragments=[fragment], metadata=metadata
        )

    def _build_markdown(
        self, request: BuildRequest, extracted_contents: List[ExtractedContent]
    ) -> BuildResult:
        """
        Markdownビルドの実行

        Args:
            request: ビルド要求
            extracted_contents: 抽出されたコンテンツ一覧

        Returns:
            BuildResult: Markdownビルド結果
        """
        logger.info("Building Markdown document")

        # 各ファイルをMarkdownに変換
        markdown_results = []
        all_warnings = []

        for idx, extracted_content in enumerate(extracted_contents):
            convert_request = MarkdownConvertRequest(
                file_path=extracted_content.file_path,
                main_selector=request.main_selector,
                include_toc=request.options.get("include_toc", False),
                heading_offset=idx,  # ファイル順序に応じて見出しレベルを調整
            )

            convert_result = self._markdown_converter.convert(convert_request)
            markdown_results.append(convert_result)
            all_warnings.extend(convert_result.warnings)

        # Markdownコンテンツを結合
        combined_markdown = self._combine_markdown_contents(markdown_results)

        # 統計情報の計算
        total_text_length = sum(
            result.extracted_text_length for result in markdown_results
        )
        page_count = max(
            1, len(markdown_results)
        )  # Markdownの場合はファイル数をページ数とする

        # タイトルの生成
        titles = [
            result.title for result in markdown_results if result.title != "Untitled"
        ]
        combined_title = " - ".join(titles) if titles else "Combined Document"

        return BuildResult(
            content=combined_markdown,
            format=OutputFormat.MARKDOWN,
            output_path=request.output_path,
            page_count=page_count,
            extracted_files=extracted_contents,
            warnings=list(set(all_warnings)),  # 重複を除去
            statistics={
                "total_files": len(extracted_contents),
                "total_text_length": total_text_length,
                "conversion_results": len(markdown_results),
                "combined_title": combined_title,
            },
        )

    def _build_pdf(
        self, request: BuildRequest, extracted_contents: List[ExtractedContent]
    ) -> BuildResult:
        """
        PDFビルドの実行

        Args:
            request: ビルド要求
            extracted_contents: 抽出されたコンテンツ一覧

        Returns:
            BuildResult: PDFビルド結果
        """
        logger.info("Building PDF document")

        # 各ファイルをPDFに変換するためのリクエストを作成
        pdf_requests = []
        for idx, extracted_content in enumerate(extracted_contents):
            pdf_request = PDFConvertRequest(
                file_path=extracted_content.file_path,
                main_selector=request.main_selector,
                options={
                    "heading_offset": idx,  # ファイル順序に応じて見出しレベルを調整
                    **request.options.get("pdf_options", {}),
                },
            )
            pdf_requests.append(pdf_request)

        # 複数ファイルをPDFに変換（結合あり）
        pdf_result = self._pdf_converter.convert_multiple(pdf_requests, merge=True)

        # 統計情報の計算
        page_count = len(extracted_contents)  # PDFの場合はファイル数をページ数とする

        return BuildResult(
            content=pdf_result.content,
            format=OutputFormat.PDF,
            output_path=request.output_path,
            page_count=page_count,
            extracted_files=extracted_contents,
            warnings=pdf_result.warnings,
            statistics={
                "total_files": len(extracted_contents),
                "total_text_length": pdf_result.extracted_text_length,
                "pdf_size_bytes": len(pdf_result.content),
                "merged_title": pdf_result.title,
            },
        )

    def _combine_markdown_contents(self, markdown_results: List[ConvertResult]) -> str:
        """
        複数のMarkdown変換結果を結合

        Args:
            markdown_results: Markdown変換結果のリスト

        Returns:
            str: 結合されたMarkdownコンテンツ
        """
        combined_parts = []

        for idx, result in enumerate(markdown_results):
            # ファイル間の区切りを追加
            if idx > 0:
                combined_parts.append("\n\n---\n\n")

            # タイトルがある場合は見出しとして追加
            if result.title and result.title != "Untitled":
                combined_parts.append(f"# {result.title}\n\n")

            # コンテンツを追加
            combined_parts.append(result.content)

        return "".join(combined_parts)

    def _save_to_file(self, build_result: BuildResult, output_path: Path) -> None:
        """
        ビルド結果をファイルに保存

        Args:
            build_result: ビルド結果
            output_path: 出力パス
        """
        try:
            # 出力ディレクトリが存在しない場合は作成
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if build_result.format == OutputFormat.MARKDOWN:
                # Markdownの場合はテキストファイルとして保存
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(build_result.content)
            elif build_result.format == OutputFormat.PDF:
                # PDFの場合はバイナリファイルとして保存
                with open(output_path, "wb") as f:
                    f.write(build_result.content)

            logger.info(f"Build result saved to: {output_path}")

        except Exception as e:
            logger.error(f"Failed to save build result to {output_path}: {str(e)}")
            raise BuildError(f"Failed to save output file: {str(e)}")
