"""
パーサー関連のファクトリークラス
"""

from typing import Dict, Type
from loguru import logger

from ...core.ports.parser_contracts import (
    HTMLParserProtocol,
    HTMLAnalyzerProtocol,
    HTMLPreprocessorProtocol,
    EncodingDetectorProtocol,
)
from .beautifulsoup_parser import (
    BeautifulSoupParser,
    BeautifulSoupAnalyzer,
    LLMPreprocessor,
)
from .chardet_detector import ChardetDetector


class ParserFactory:
    """パーサー関連のファクトリークラス"""

    _parsers: Dict[str, Type[HTMLParserProtocol]] = {
        "beautifulsoup": BeautifulSoupParser,
        # 将来的な拡張
        # "lxml": LXMLParser,
        # "html5lib": HTML5libParser,
    }

    _analyzers: Dict[str, Type[HTMLAnalyzerProtocol]] = {
        "beautifulsoup": BeautifulSoupAnalyzer,
        # 将来的な拡張
        # "lxml": LXMLAnalyzer,
    }

    _preprocessors: Dict[str, Type[HTMLPreprocessorProtocol]] = {
        "llm": LLMPreprocessor,
        # 将来的な拡張
        # "minify": MinifyPreprocessor,
        # "cleanup": CleanupPreprocessor,
    }

    _detectors: Dict[str, Type[EncodingDetectorProtocol]] = {
        "chardet": ChardetDetector,
        # 将来的な拡張
        # "cchardet": CChardetDetector,
        # "charset_normalizer": CharsetNormalizerDetector,
    }

    @classmethod
    def create_parser(
        cls, method: str = "beautifulsoup", **kwargs
    ) -> HTMLParserProtocol:
        """
        HTMLパーサーを作成

        Args:
            method: パーサーの種類 ("beautifulsoup", "lxml", "html5lib")
            **kwargs: パーサーの初期化引数

        Returns:
            HTMLParserProtocol: パーサーインスタンス

        Raises:
            ValueError: 不正なパーサー種類が指定された場合
        """
        if method not in cls._parsers:
            available_methods = ", ".join(cls._parsers.keys())
            raise ValueError(
                f"Unknown parser method: {method}. Available: {available_methods}"
            )

        parser_class = cls._parsers[method]
        logger.info(f"Creating {method} parser")

        return parser_class(**kwargs)

    @classmethod
    def create_analyzer(
        cls, method: str = "beautifulsoup", **kwargs
    ) -> HTMLAnalyzerProtocol:
        """
        HTMLアナライザーを作成

        Args:
            method: アナライザーの種類 ("beautifulsoup", "lxml")
            **kwargs: アナライザーの初期化引数

        Returns:
            HTMLAnalyzerProtocol: アナライザーインスタンス

        Raises:
            ValueError: 不正なアナライザー種類が指定された場合
        """
        if method not in cls._analyzers:
            available_methods = ", ".join(cls._analyzers.keys())
            raise ValueError(
                f"Unknown analyzer method: {method}. Available: {available_methods}"
            )

        analyzer_class = cls._analyzers[method]
        logger.info(f"Creating {method} analyzer")

        return analyzer_class(**kwargs)

    @classmethod
    def create_preprocessor(
        cls, method: str = "llm", **kwargs
    ) -> HTMLPreprocessorProtocol:
        """
        HTMLプリプロセッサーを作成

        Args:
            method: プリプロセッサーの種類 ("llm", "minify", "cleanup")
            **kwargs: プリプロセッサーの初期化引数

        Returns:
            HTMLPreprocessorProtocol: プリプロセッサーインスタンス

        Raises:
            ValueError: 不正なプリプロセッサー種類が指定された場合
        """
        if method not in cls._preprocessors:
            available_methods = ", ".join(cls._preprocessors.keys())
            raise ValueError(
                f"Unknown preprocessor method: {method}. Available: {available_methods}"
            )

        preprocessor_class = cls._preprocessors[method]
        logger.info(f"Creating {method} preprocessor")

        return preprocessor_class(**kwargs)

    @classmethod
    def create_encoding_detector(
        cls, method: str = "chardet", **kwargs
    ) -> EncodingDetectorProtocol:
        """
        エンコーディング検出器を作成

        Args:
            method: 検出器の種類 ("chardet", "cchardet", "charset_normalizer")
            **kwargs: 検出器の初期化引数

        Returns:
            EncodingDetectorProtocol: 検出器インスタンス

        Raises:
            ValueError: 不正な検出器種類が指定された場合
        """
        if method not in cls._detectors:
            available_methods = ", ".join(cls._detectors.keys())
            raise ValueError(
                f"Unknown detector method: {method}. Available: {available_methods}"
            )

        detector_class = cls._detectors[method]
        logger.info(f"Creating {method} encoding detector")

        return detector_class(**kwargs)

    @classmethod
    def get_available_parsers(cls) -> list[str]:
        """利用可能なパーサー種類を取得"""
        return list(cls._parsers.keys())

    @classmethod
    def get_available_analyzers(cls) -> list[str]:
        """利用可能なアナライザー種類を取得"""
        return list(cls._analyzers.keys())

    @classmethod
    def get_available_preprocessors(cls) -> list[str]:
        """利用可能なプリプロセッサー種類を取得"""
        return list(cls._preprocessors.keys())

    @classmethod
    def get_available_detectors(cls) -> list[str]:
        """利用可能な検出器種類を取得"""
        return list(cls._detectors.keys())
