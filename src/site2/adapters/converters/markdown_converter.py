"""
Markdownifyを使用したMarkdownコンバーター
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from loguru import logger

try:
    from markdownify import markdownify as md
except ImportError:
    logger.warning(
        "markdownify is not installed. Please install it with: pip install markdownify"
    )
    md = None

from ...core.ports.build_contracts import MarkdownConverterProtocol
from ...core.domain.build_domain import (
    MarkdownConvertRequest,
    ConvertResult,
    OutputFormat,
    ConvertError,
    ContentNotFoundError,
)
from .markdownify_config import DEFAULT_MARKDOWNIFY_CONFIG, validate_config


class MarkdownifyConverter(MarkdownConverterProtocol):
    """
    Markdownifyを使用したMarkdownコンバーター

    HTMLファイルからメインコンテンツを抽出し、Markdownに変換します。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: Markdownify設定（Noneの場合はデフォルト設定を使用）
        """
        if md is None:
            raise ImportError("markdownify is required but not installed")

        self.config = config or DEFAULT_MARKDOWNIFY_CONFIG.copy()
        validate_config(self.config)
        logger.debug(f"MarkdownifyConverter initialized with config: {self.config}")

    def convert(self, request: MarkdownConvertRequest) -> ConvertResult:
        """
        HTMLをMarkdownに変換

        Args:
            request: Markdown変換要求

        Returns:
            ConvertResult: 変換結果

        Raises:
            ConvertError: 変換処理に失敗した場合
        """
        logger.info(f"Starting Markdown conversion for: {request.file_path}")

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

            # 見出しレベルの調整
            if request.heading_offset > 0:
                main_content = self._adjust_heading_levels(
                    main_content, request.heading_offset
                )

            # Markdownに変換
            markdown_content = self._convert_to_markdown(main_content)

            # 目次の追加
            if request.include_toc:
                markdown_content = self._add_table_of_contents(markdown_content)

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
                content=markdown_content,
                format=OutputFormat.MARKDOWN,
                title=title or "Untitled",
                extracted_text_length=text_length,
                warnings=warnings,
            )

            logger.info(f"Markdown conversion completed. Text length: {text_length}")
            return result

        except FileNotFoundError:
            error_msg = f"File not found: {request.file_path}"
            logger.error(error_msg)
            raise ConvertError(error_msg)
        except Exception as e:
            error_msg = f"Markdown conversion failed: {str(e)}"
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

    def _convert_to_markdown(self, soup: BeautifulSoup) -> str:
        """
        BeautifulSoupオブジェクトをMarkdownに変換

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            str: Markdown文字列
        """
        html_string = str(soup)

        # Markdownifyで変換
        markdown = md(html_string, **self.config)

        # 余分な改行を削除
        markdown = re.sub(r"\n\s*\n\s*\n", "\n\n", markdown)

        # 前後の空白を削除
        markdown = markdown.strip()

        return markdown

    def _add_table_of_contents(self, markdown: str) -> str:
        """
        目次を追加

        Args:
            markdown: Markdownコンテンツ

        Returns:
            str: 目次が追加されたMarkdownコンテンツ
        """
        # 見出しを抽出
        headings = []
        lines = markdown.split("\n")

        for line in lines:
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                title = line.lstrip("# ").strip()
                if title:
                    headings.append((level, title))

        if not headings:
            return markdown

        # 目次を生成
        toc_lines = ["## 目次", ""]
        for level, title in headings:
            indent = "  " * (level - 1)
            # アンカーリンクを生成（GitHub Markdown形式）
            anchor = title.lower().replace(" ", "-").replace("(", "").replace(")", "")
            anchor = re.sub(r"[^\w\-_]", "", anchor)
            toc_lines.append(f"{indent}- [{title}](#{anchor})")

        toc_lines.extend(["", "---", ""])

        # 目次を元のコンテンツの前に追加
        return "\n".join(toc_lines) + "\n" + markdown

    def _get_default_config(self) -> Dict[str, Any]:
        """
        デフォルト設定を取得

        Returns:
            Dict[str, Any]: デフォルト設定
        """
        return DEFAULT_MARKDOWNIFY_CONFIG.copy()
