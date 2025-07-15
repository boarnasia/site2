"""
Parser implementations using BeautifulSoup
"""

import re
import time

from bs4 import BeautifulSoup, Tag
from loguru import logger

from ...core.ports.parser_contracts import (
    AnalysisError,
    HTMLAnalyzerProtocol,
    HTMLMetadata,
    HTMLParserProtocol,
    HTMLPreprocessorProtocol,
    HTMLStructureAnalysis,
    ParseError,
    ParseRequest,
    ParseResult,
    SelectorError,
    SelectorSearchRequest,
    SelectorSearchResult,
    TextExtractionRequest,
    TextExtractionResult,
)
from .chardet_detector import ChardetDetector


class BeautifulSoupParser(HTMLParserProtocol):
    """HTML parsing service using BeautifulSoup."""

    def __init__(self, parser: str = "html.parser"):
        self.parser = parser
        self.encoding_detector = ChardetDetector()

    def parse(self, request: ParseRequest) -> ParseResult:
        """Parses an HTML file."""
        start_time = time.time()
        warnings = []

        try:
            encoding = request.encoding
            if not encoding:
                encoding = self.encoding_detector.detect_encoding(request.file_path)
                logger.info(f"Detected encoding: {encoding} for {request.file_path}")

            with open(request.file_path, "r", encoding=encoding, errors="ignore") as f:
                html_content = f.read()

            soup = self.parse_string(html_content)
            parse_time = time.time() - start_time

            return ParseResult(
                file_path=request.file_path,
                soup=soup,
                encoding=encoding,
                parse_time_seconds=parse_time,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f"Failed to parse {request.file_path}: {str(e)}")
            raise ParseError(f"Failed to parse HTML: {str(e)}") from e

    def parse_string(self, html: str) -> BeautifulSoup:
        """Parses an HTML string."""
        if not html:
            raise ValueError("HTML string cannot be empty")
        try:
            return BeautifulSoup(html, self.parser)
        except Exception as e:
            raise ParseError(f"Failed to parse HTML string: {str(e)}") from e

    def extract_text(self, request: TextExtractionRequest) -> TextExtractionResult:
        """Extracts text from a BeautifulSoup element."""
        element = request.element
        if request.remove_scripts:
            for tag in element.find_all(["script", "noscript"]):
                tag.decompose()
        if request.remove_styles:
            for tag in element.find_all(["style"]):
                tag.decompose()
            for tag in element.find_all(style=True):
                del tag["style"]

        text = element.get_text(separator="\\n", strip=True)
        if request.clean_whitespace:
            lines = [line.strip() for line in text.split("\\n")]
            text = "\\n".join(filter(None, lines))

        return TextExtractionResult(
            original_element=element,
            extracted_text=text,
            text_length=len(text),
            cleaned=request.clean_whitespace,
        )

    def find_by_selectors(self, request: SelectorSearchRequest) -> SelectorSearchResult:
        """Finds elements using a list of CSS selectors."""
        soup = request.soup
        elements = []
        matched_selector = None
        try:
            if request.find_all:
                for selector in request.selectors:
                    found = soup.select(selector)
                    if found:
                        elements.extend(found)
                        if not matched_selector:
                            matched_selector = selector
                return SelectorSearchResult(
                    matched_selector=matched_selector,
                    elements=elements,
                    search_method="all_matches",
                )
            else:
                for selector in request.selectors:
                    element = soup.select_one(selector)
                    if element:
                        return SelectorSearchResult(
                            matched_selector=selector,
                            elements=[element],
                            search_method="first_match",
                        )
                return SelectorSearchResult(
                    matched_selector=None, elements=[], search_method="first_match"
                )
        except Exception as e:
            raise SelectorError(f"Selector search failed: {str(e)}") from e


class BeautifulSoupAnalyzer(HTMLAnalyzerProtocol):
    """HTML structure and metadata analysis service."""

    def analyze_structure(self, soup: BeautifulSoup) -> HTMLStructureAnalysis:
        """Analyzes the structure of a BeautifulSoup object."""
        try:
            return HTMLStructureAnalysis(
                has_main=bool(soup.find("main")),
                has_article=bool(soup.find("article")),
                has_nav=bool(soup.find("nav")),
                has_header=bool(soup.find("header")),
                has_footer=bool(soup.find("footer")),
                heading_count={
                    f"h{level}": len(soup.find_all(f"h{level}"))
                    for level in range(1, 7)
                },
                paragraph_count=len(soup.find_all("p")),
                link_count=len(soup.find_all("a")),
                image_count=len(soup.find_all("img")),
                table_count=len(soup.find_all("table")),
                list_count=len(soup.find_all(["ul", "ol"])),
            )
        except Exception as e:
            raise AnalysisError(f"Structure analysis failed: {str(e)}") from e

    def extract_metadata(self, soup: BeautifulSoup) -> HTMLMetadata:
        """Extracts metadata from a BeautifulSoup object."""
        title_tag = soup.find("title")
        title = title_tag.string.strip() if title_tag else None

        meta_tags = {
            meta.get("name", "").lower(): meta.get("content", "")
            for meta in soup.find_all("meta")
            if meta.get("name")
        }
        og_tags = {
            meta.get("property", ""): meta.get("content", "")
            for meta in soup.find_all("meta")
            if meta.get("property", "").startswith("og:")
        }
        html_tag = soup.find("html")
        language = html_tag.get("lang") if html_tag else None

        return HTMLMetadata(
            title=title,
            description=meta_tags.get("description"),
            keywords=meta_tags.get("keywords"),
            author=meta_tags.get("author"),
            language=language,
            meta_tags=meta_tags,
            og_tags=og_tags,
        )

    def calculate_text_density(self, element: Tag) -> float:
        """Calculates the text-to-HTML ratio of an element."""
        if not isinstance(element, Tag):
            return 0.0
        text = element.get_text(strip=True)
        html_length = len(str(element))
        return len(text) / html_length if html_length > 0 else 0.0


class LLMPreprocessor(HTMLPreprocessorProtocol):
    """HTML preprocessor for LLM input."""

    def preprocess_for_llm(self, soup: BeautifulSoup, max_length: int = 50000) -> str:
        """Preprocesses HTML for Large Language Model consumption."""
        soup_copy = BeautifulSoup(str(soup), "html.parser")

        for tag in soup_copy.find_all(
            ["script", "style", "noscript", "iframe", "header", "footer", "nav"]
        ):
            tag.decompose()

        for comment in soup_copy.find_all(
            string=lambda text: isinstance(text, str) and "<!--" in text
        ):
            comment.extract()

        for tag in soup_copy.find_all():
            attrs_to_keep = {
                "id": tag.attrs.get("id"),
                "class": " ".join(tag.attrs.get("class", [])),
                "href": tag.attrs.get("href") if tag.name == "a" else None,
            }
            tag.attrs = {k: v for k, v in attrs_to_keep.items() if v is not None}

        html_str = str(soup_copy.prettify())
        html_str = re.sub(r"\\n\\s*\\n", "\\n", html_str)

        if len(html_str) > max_length:
            html_str = html_str[:max_length] + "\\n<!-- truncated -->"

        return html_str
