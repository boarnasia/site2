import pytest
from pathlib import Path
from bs4 import BeautifulSoup

from site2.adapters.parsers.beautifulsoup_parser import (
    BeautifulSoupParser,
    BeautifulSoupAnalyzer,
    LLMPreprocessor,
)
from site2.core.ports.parser_contracts import (
    ParseRequest,
    TextExtractionRequest,
    SelectorSearchRequest,
)

FIXTURE_DIR = Path(__file__).parent.parent.parent.parent / "fixtures" / "html"


@pytest.fixture
def parser():
    return BeautifulSoupParser()


@pytest.fixture
def analyzer():
    return BeautifulSoupAnalyzer()


@pytest.fixture
def preprocessor():
    return LLMPreprocessor()


@pytest.fixture
def utf8_html_path():
    return FIXTURE_DIR / "utf8_sample.html"


@pytest.fixture
def complex_html_path():
    return FIXTURE_DIR / "complex_sample.html"


# --- BeautifulSoupParser Tests ---


def test_parse_utf8_file(parser: BeautifulSoupParser, utf8_html_path: Path):
    """Test parsing a standard UTF-8 HTML file."""
    request = ParseRequest(file_path=utf8_html_path)
    result = parser.parse(request)
    assert isinstance(result.soup, BeautifulSoup)
    assert result.encoding == "utf-8"
    assert result.file_path == utf8_html_path
    assert "UTF-8 Test Page" in result.soup.title.string


def test_extract_text(parser: BeautifulSoupParser, complex_html_path: Path):
    """Test text extraction, ensuring scripts and styles are removed."""
    parse_result = parser.parse(ParseRequest(file_path=complex_html_path))
    request = TextExtractionRequest(element=parse_result.soup)
    result = parser.extract_text(request)

    assert "alert('hello')" not in result.extracted_text
    assert "display: none" not in result.extracted_text
    assert "Site Name" in result.extracted_text
    assert "Main Content" in result.extracted_text


def test_find_by_selectors(parser: BeautifulSoupParser, utf8_html_path: Path):
    """Test finding elements by CSS selectors."""
    parse_result = parser.parse(ParseRequest(file_path=utf8_html_path))

    # Find first match - should find h2 first as it's first in the selector list
    request_first = SelectorSearchRequest(
        soup=parse_result.soup, selectors=["h2", "h1"]
    )
    result_first = parser.find_by_selectors(request_first)
    assert len(result_first.elements) == 1
    assert result_first.elements[0].name == "h2"
    assert result_first.matched_selector == "h2"

    # Find all matches
    request_all = SelectorSearchRequest(
        soup=parse_result.soup, selectors=["p"], find_all=True
    )
    result_all = parser.find_by_selectors(request_all)
    assert len(result_all.elements) == 3


# --- BeautifulSoupAnalyzer Tests ---


def test_analyze_structure(
    analyzer: BeautifulSoupAnalyzer, parser: BeautifulSoupParser, utf8_html_path: Path
):
    """Test HTML structure analysis."""
    soup = parser.parse(ParseRequest(file_path=utf8_html_path)).soup
    analysis = analyzer.analyze_structure(soup)

    assert analysis.has_main is True
    assert analysis.has_nav is True
    assert analysis.heading_count["h1"] == 1
    assert analysis.heading_count["h2"] == 1
    assert analysis.link_count == 3


def test_extract_metadata(
    analyzer: BeautifulSoupAnalyzer, parser: BeautifulSoupParser, utf8_html_path: Path
):
    """Test metadata extraction."""
    soup = parser.parse(ParseRequest(file_path=utf8_html_path)).soup
    metadata = analyzer.extract_metadata(soup)

    assert metadata.title == "UTF-8 Test Page"
    assert metadata.description == "A test page for site2"
    assert metadata.author == "Test Author"
    assert metadata.language == "en"


def test_calculate_text_density(
    analyzer: BeautifulSoupAnalyzer, parser: BeautifulSoupParser, utf8_html_path: Path
):
    """Test text density calculation."""
    soup = parser.parse(ParseRequest(file_path=utf8_html_path)).soup
    main_element = soup.find("main")
    density = analyzer.calculate_text_density(main_element)
    assert 0 < density < 1.0


# --- LLMPreprocessor Tests ---


def test_preprocess_for_llm(
    preprocessor: LLMPreprocessor, parser: BeautifulSoupParser, complex_html_path: Path
):
    """Test HTML preprocessing for LLM consumption."""
    soup = parser.parse(ParseRequest(file_path=complex_html_path)).soup
    # Use a large max_length to ensure truncation doesn't happen in this test
    processed_html = preprocessor.preprocess_for_llm(soup, max_length=50000)

    # Check for removed tags
    assert "<script>" not in processed_html
    assert "<nav>" not in processed_html

    # Check that truncation comment is NOT present
    assert "<!-- truncated -->" not in processed_html

    # Check for simplified attributes
    assert 'id="content"' in processed_html
    assert "style=" not in processed_html
