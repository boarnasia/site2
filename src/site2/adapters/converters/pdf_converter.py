"""
Playwrightを使用したPDFコンバーター
"""

import io
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from loguru import logger

try:
    from pypdf import PdfWriter, PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfWriter, PdfReader  # fallback to PyPDF2
    except ImportError:
        logger.warning(
            "Neither pypdf nor PyPDF2 is installed. PDF merging will not work."
        )
        PdfWriter = None
        PdfReader = None

from ...core.ports.build_contracts import PDFConverterProtocol
from ...core.domain.build_domain import (
    PDFConvertRequest,
    ConvertResult,
    OutputFormat,
    ConvertError,
    ContentNotFoundError,
)
from .playwright_config import DEFAULT_PLAYWRIGHT_PDF_CONFIG, validate_pdf_config


class PlaywrightPDFConverter(PDFConverterProtocol):
    """
    Playwrightを使用したPDFコンバーター

    HTMLファイルからメインコンテンツを抽出し、PDFに変換します。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: Playwright設定（Noneの場合はデフォルト設定を使用）
        """
        self.config = config or DEFAULT_PLAYWRIGHT_PDF_CONFIG.copy()
        validate_pdf_config(self.config)
        logger.debug(f"PlaywrightPDFConverter initialized with config: {self.config}")

    def convert(self, request: PDFConvertRequest) -> ConvertResult:
        """
        HTMLをPDFに変換

        Args:
            request: PDF変換要求

        Returns:
            ConvertResult: 変換結果

        Raises:
            ConvertError: 変換処理に失敗した場合
        """
        logger.info(f"Starting PDF conversion for: {request.file_path}")

        try:
            # HTMLファイルの読み込み
            html_content = self._read_html_file(request.file_path)

            # BeautifulSoupでパース
            soup = BeautifulSoup(html_content, "html.parser")

            # タイトルの抽出
            title = self._extract_title(soup)

            # メインコンテンツの抽出
            main_content = self._extract_main_content(soup, request.main_selector)

            # 不要な要素を除去
            self._remove_unwanted_elements(main_content)

            # 見出しレベルの調整（PDFConvertRequestにはheading_offsetがないため、optionsから取得）
            heading_offset = request.options.get("heading_offset", 0)
            if heading_offset > 0:
                main_content = self._adjust_heading_levels(main_content, heading_offset)

            # 一時的なHTMLファイルを作成
            temp_html = self._create_temp_html(main_content, title)

            # PlaywrightでPDFに変換
            pdf_bytes = self._convert_to_pdf_with_playwright(temp_html)

            # テキスト長の計算
            text_length = len(main_content.get_text(strip=True))

            # 警告の収集
            warnings = []
            if not title:
                warnings.append("No title found in HTML")
            if text_length == 0:
                warnings.append("No text content extracted")

            result = ConvertResult(
                original_file=request.file_path,
                content=pdf_bytes,
                format=OutputFormat.PDF,
                title=title or "Untitled",
                extracted_text_length=text_length,
                warnings=warnings,
            )

            logger.info(
                f"PDF conversion completed. Text length: {text_length}, PDF size: {len(pdf_bytes)} bytes"
            )
            return result

        except FileNotFoundError:
            error_msg = f"File not found: {request.file_path}"
            logger.error(error_msg)
            raise ConvertError(error_msg)
        except Exception as e:
            error_msg = f"PDF conversion failed: {str(e)}"
            logger.error(error_msg)
            raise ConvertError(error_msg)

    def convert_multiple(
        self, requests: List[PDFConvertRequest], merge: bool = True
    ) -> Union[ConvertResult, List[ConvertResult]]:
        """
        複数のHTMLファイルをPDFに変換

        Args:
            requests: PDF変換要求のリスト
            merge: Trueの場合は結合されたPDFを返す、Falseの場合は個別PDFのリストを返す

        Returns:
            Union[ConvertResult, List[ConvertResult]]: 変換結果

        Raises:
            ConvertError: 変換または結合に失敗した場合
        """
        logger.info(
            f"Starting multiple PDF conversion for {len(requests)} files, merge={merge}"
        )

        try:
            # 各ファイルを個別に変換
            individual_results = []
            for request in requests:
                result = self.convert(request)
                individual_results.append(result)

            if not merge:
                return individual_results

            # PDF結合
            if PdfWriter is None:
                raise ConvertError(
                    "PDF merging requires pypdf or PyPDF2 to be installed"
                )

            merged_pdf_bytes = self._merge_pdfs(
                [result.content for result in individual_results]
            )

            # 結合結果の作成
            total_text_length = sum(
                result.extracted_text_length for result in individual_results
            )
            all_warnings = []
            for result in individual_results:
                all_warnings.extend(result.warnings)

            # タイトルを結合
            titles = [
                result.title
                for result in individual_results
                if result.title != "Untitled"
            ]
            merged_title = " + ".join(titles) if titles else "Merged Document"

            merged_result = ConvertResult(
                original_file=requests[0].file_path,  # 最初のファイルを代表として使用
                content=merged_pdf_bytes,
                format=OutputFormat.PDF,
                title=merged_title,
                extracted_text_length=total_text_length,
                warnings=list(set(all_warnings)),  # 重複を除去
            )

            logger.info(
                f"PDF merge completed. Total text length: {total_text_length}, PDF size: {len(merged_pdf_bytes)} bytes"
            )
            return merged_result

        except Exception as e:
            error_msg = f"Multiple PDF conversion failed: {str(e)}"
            logger.error(error_msg)
            raise ConvertError(error_msg)

    def _read_html_file(self, file_path: Path) -> str:
        """
        HTMLファイルを読み込み

        Args:
            file_path: HTMLファイルのパス

        Returns:
            str: HTMLコンテンツ

        Raises:
            FileNotFoundError: ファイルが存在しない場合
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # UTF-8で読めない場合は他のエンコーディングを試す
            encodings = ["cp932", "shift_jis", "euc-jp", "iso-8859-1"]
            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            raise ConvertError(f"Unable to decode file: {file_path}")

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """
        HTMLからタイトルを抽出

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            str: タイトル（見つからない場合は空文字）
        """
        # <title>タグから取得
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            return title_tag.string.strip()

        # <h1>タグから取得
        h1_tag = soup.find("h1")
        if h1_tag:
            return h1_tag.get_text(strip=True)

        return ""

    def _extract_main_content(
        self, soup: BeautifulSoup, selector: str
    ) -> BeautifulSoup:
        """
        メインコンテンツを抽出

        Args:
            soup: BeautifulSoupオブジェクト
            selector: CSSセレクタ

        Returns:
            BeautifulSoup: メインコンテンツのBeautifulSoupオブジェクト

        Raises:
            ContentNotFoundError: セレクタでコンテンツが見つからない場合
        """
        elements = soup.select(selector)
        if not elements:
            raise ContentNotFoundError(f"Content not found with selector: {selector}")

        # 最初にマッチした要素を使用
        main_element = elements[0]

        # 新しいBeautifulSoupオブジェクトを作成
        main_soup = BeautifulSoup(str(main_element), "html.parser")

        return main_soup

    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """
        不要な要素を除去

        Args:
            soup: BeautifulSoupオブジェクト（インプレースで変更）
        """
        # 除去対象のタグリスト
        unwanted_tags = [
            "script",
            "style",
            "nav",
            "header",
            "footer",
            "aside",
            "meta",
            "link",
        ]

        for tag_name in unwanted_tags:
            for element in soup.find_all(tag_name):
                element.decompose()

    def _adjust_heading_levels(self, soup: BeautifulSoup, offset: int) -> BeautifulSoup:
        """
        見出しレベルを調整

        Args:
            soup: BeautifulSoupオブジェクト
            offset: 見出しレベルのオフセット

        Returns:
            BeautifulSoup: 見出しレベルが調整されたBeautifulSoupオブジェクト
        """
        if offset <= 0:
            return soup

        # 見出しタグを取得（h1からh6まで）
        heading_tags = ["h1", "h2", "h3", "h4", "h5", "h6"]

        for tag_name in heading_tags:
            headings = soup.find_all(tag_name)
            for heading in headings:
                current_level = int(tag_name[1])  # h1 -> 1, h2 -> 2, ...
                new_level = min(current_level + offset, 6)  # 最大h6まで

                # 新しいタグ名を作成
                new_tag_name = f"h{new_level}"
                heading.name = new_tag_name

        return soup

    def _create_temp_html(self, content_soup: BeautifulSoup, title: str) -> str:
        """
        一時的なHTMLドキュメントを作成

        Args:
            content_soup: メインコンテンツのBeautifulSoup
            title: ドキュメントタイトル

        Returns:
            str: 完全なHTMLドキュメント
        """
        html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: "Hiragino Sans", "Yu Gothic", "Meiryo", sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 2em;
            margin-bottom: 1em;
        }}
        p {{
            margin-bottom: 1em;
        }}
        ul, ol {{
            margin-bottom: 1em;
            padding-left: 2em;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 1em;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        @media print {{
            body {{
                max-width: none;
                margin: 0;
                padding: 0;
            }}
        }}
    </style>
</head>
<body>
{str(content_soup)}
</body>
</html>"""

        return html_template

    def _convert_to_pdf_with_playwright(self, html_content: str) -> bytes:
        """
        PlaywrightでHTMLをPDFに変換

        Args:
            html_content: HTMLコンテンツ

        Returns:
            bytes: PDFバイナリデータ
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.config.get("headless", True))

            try:
                page = browser.new_page()

                # ビューポートの設定
                if "viewport" in self.config:
                    page.set_viewport_size(**self.config["viewport"])

                # HTMLコンテンツを設定
                page.set_content(html_content)

                # 待機設定
                if "wait_for_load_state" in self.config:
                    page.wait_for_load_state(self.config["wait_for_load_state"])

                if "wait_for_timeout" in self.config:
                    page.wait_for_timeout(self.config["wait_for_timeout"])

                # PDF生成オプションを準備
                pdf_options = {
                    "format": self.config.get("format", "A4"),
                    "print_background": self.config.get("print_background", True),
                    "display_header_footer": self.config.get(
                        "display_header_footer", False
                    ),
                    "prefer_css_page_size": self.config.get(
                        "prefer_css_page_size", True
                    ),
                    "landscape": self.config.get("landscape", False),
                }

                # マージンの設定
                if "margin" in self.config:
                    pdf_options["margin"] = self.config["margin"]

                # ヘッダー・フッターの設定
                if self.config.get("display_header_footer"):
                    pdf_options["header_template"] = self.config.get(
                        "header_template", ""
                    )
                    pdf_options["footer_template"] = self.config.get(
                        "footer_template", ""
                    )

                # PDFを生成
                pdf_bytes = page.pdf(**pdf_options)

                return pdf_bytes

            finally:
                browser.close()

    def _merge_pdfs(self, pdf_bytes_list: List[bytes]) -> bytes:
        """
        複数のPDFを結合

        Args:
            pdf_bytes_list: PDFバイナリデータのリスト

        Returns:
            bytes: 結合されたPDFバイナリデータ
        """
        if not pdf_bytes_list:
            raise ConvertError("No PDFs to merge")

        if len(pdf_bytes_list) == 1:
            return pdf_bytes_list[0]

        writer = PdfWriter()

        for pdf_bytes in pdf_bytes_list:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                writer.add_page(page)

        # 結合されたPDFをバイトストリームに書き込み
        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)

        return output_stream.read()
