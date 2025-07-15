"""
Encoding detector implementation using chardet
"""

from pathlib import Path

import chardet
from loguru import logger

from ...core.ports.parser_contracts import DetectionError, EncodingDetectorProtocol


class ChardetDetector(EncodingDetectorProtocol):
    """Encoding detection service using chardet."""

    ENCODING_ALIASES = {
        "ascii": "utf-8",
        "iso-8859-1": "latin-1",
        "windows-1252": "cp1252",
        "shift-jis": "shift_jis",
        "euc-jp": "euc_jp",
    }

    def detect_encoding(self, file_path: Path) -> str:
        """Detects the encoding of a file."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # Read the first 10KB for detection
            with open(file_path, "rb") as f:
                raw_data = f.read(10240)

            return self.detect_encoding_from_bytes(raw_data)

        except Exception as e:
            logger.error(f"Encoding detection failed for {file_path}: {str(e)}")
            raise DetectionError(f"Failed to detect encoding: {str(e)}") from e

    def detect_encoding_from_bytes(self, data: bytes) -> str:
        """Detects the encoding from a byte stream."""
        if not data:
            # Return default encoding for empty data
            return "utf-8"

        try:
            result = chardet.detect(data)

            if not result or not result.get("encoding"):
                logger.warning("chardet failed to detect encoding, using utf-8")
                return "utf-8"

            encoding = result["encoding"]
            confidence = result.get("confidence", 0)

            logger.debug(f"Detected encoding: {encoding} (confidence: {confidence})")

            # Normalize aliases
            normalized = self.ENCODING_ALIASES.get(encoding.lower(), encoding)

            if confidence < 0.7:
                logger.warning(
                    f"Low confidence encoding detection: {encoding} ({confidence:.2f})"
                )

            return normalized.lower()

        except Exception as e:
            raise DetectionError(f"Encoding detection failed: {str(e)}") from e
