import pytest
from pathlib import Path
import logging
from site2.adapters.parsers.chardet_detector import ChardetDetector


@pytest.fixture
def detector():
    return ChardetDetector()


@pytest.fixture
def html_fixtures(tmp_path: Path) -> Path:
    # Use more distinct Japanese text for SJIS
    sjis_content = "<html><head><title>テスト</title></head><body>これはShift_JISの日本語テキストです。</body></html>".encode(
        "shift_jis"
    )
    utf8_content = (
        "<html><head><title>Test</title></head><body>Hello</body></html>".encode(
            "utf-8"
        )
    )

    sjis_path = tmp_path / "sjis.html"
    sjis_path.write_bytes(sjis_content)

    utf8_path = tmp_path / "utf8.html"
    utf8_path.write_bytes(utf8_content)

    return tmp_path


def test_detect_encoding_sjis(detector: ChardetDetector, html_fixtures: Path):
    """Test Shift_JIS encoding detection from file."""
    encoding = detector.detect_encoding(html_fixtures / "sjis.html")
    assert encoding == "shift_jis"


def test_detect_encoding_utf8(detector: ChardetDetector, html_fixtures: Path):
    """Test UTF-8 encoding detection from file."""
    encoding = detector.detect_encoding(html_fixtures / "utf8.html")
    assert encoding == "utf-8"


def test_detect_encoding_from_bytes(detector: ChardetDetector):
    """Test encoding detection from bytes."""
    sjis_bytes = "これはShift_JISの日本語テキストです。".encode("shift_jis")
    encoding = detector.detect_encoding_from_bytes(sjis_bytes)
    assert encoding == "shift_jis"


def test_detect_encoding_file_not_found(detector: ChardetDetector):
    """Test that FileNotFoundError is raised for non-existent files."""
    with pytest.raises(FileNotFoundError):
        detector.detect_encoding(Path("non_existent_file.html"))


def test_detect_encoding_from_empty_bytes(detector: ChardetDetector):
    """Test that default encoding is returned for empty bytes."""
    encoding = detector.detect_encoding_from_bytes(b"")
    assert encoding == "utf-8"


def test_low_confidence_detection(detector: ChardetDetector, caplog, mocker):
    """Test that a warning is logged for low-confidence detection."""
    # Mock chardet.detect to return a low-confidence result
    mocker.patch(
        "chardet.detect",
        return_value={"encoding": "ISO-8859-1", "confidence": 0.5, "language": ""},
    )

    with caplog.at_level(logging.WARNING):
        detector.detect_encoding_from_bytes(b"some bytes")
    assert "Low confidence encoding detection" in caplog.text
