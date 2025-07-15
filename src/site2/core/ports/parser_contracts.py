"""
HTML Parser Contracts
"""

from pathlib import Path
from typing import Any, List, Optional, Protocol

from pydantic import BaseModel, Field

from ..domain.parser_domain import HTMLMetadata, HTMLStructureAnalysis


# Custom Exceptions
class ParserError(Exception):
    """Base exception for parsing errors."""


class ParseError(ParserError):
    """Raised when HTML parsing fails."""


class SelectorError(ParserError):
    """Raised for errors related to CSS selectors."""


class AnalysisError(ParserError):
    """Raised during HTML structure or metadata analysis."""


class DetectionError(ParserError):
    """Raised when character encoding detection fails."""


# Data Transfer Objects (DTOs)
class ParseRequest(BaseModel):
    file_path: Path
    encoding: Optional[str] = None


class ParseResult(BaseModel):
    file_path: Path
    soup: Any  # BeautifulSoup object
    encoding: str
    parse_time_seconds: float
    warnings: List[str] = Field(default_factory=list)


class TextExtractionRequest(BaseModel):
    element: Any  # BeautifulSoup Tag object
    remove_scripts: bool = True
    remove_styles: bool = True
    clean_whitespace: bool = True


class TextExtractionResult(BaseModel):
    original_element: Any
    extracted_text: str
    text_length: int
    cleaned: bool


class SelectorSearchRequest(BaseModel):
    soup: Any  # BeautifulSoup object
    selectors: List[str]
    find_all: bool = False


class SelectorSearchResult(BaseModel):
    matched_selector: Optional[str]
    elements: List[Any]  # List of BeautifulSoup Tag objects
    search_method: str


# Protocols (Ports)
class EncodingDetectorProtocol(Protocol):
    def detect_encoding(self, file_path: Path) -> str: ...

    def detect_encoding_from_bytes(self, data: bytes) -> str: ...


class HTMLParserProtocol(Protocol):
    def parse(self, request: ParseRequest) -> ParseResult: ...

    def parse_string(self, html: str) -> Any: ...

    def extract_text(self, request: TextExtractionRequest) -> TextExtractionResult: ...

    def find_by_selectors(
        self, request: SelectorSearchRequest
    ) -> SelectorSearchResult: ...


class HTMLAnalyzerProtocol(Protocol):
    def analyze_structure(self, soup: Any) -> HTMLStructureAnalysis: ...

    def extract_metadata(self, soup: Any) -> HTMLMetadata: ...

    def calculate_text_density(self, element: Any) -> float: ...


class HTMLPreprocessorProtocol(Protocol):
    def preprocess_for_llm(self, soup: Any, max_length: int = 50000) -> str: ...
