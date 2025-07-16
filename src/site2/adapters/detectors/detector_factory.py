"""
メインコンテンツ検出器のファクトリー
設定に基づいて適切な検出器を作成する
"""

from typing import Dict, Type
from loguru import logger

from ...core.ports.detect_contracts import MainContentDetectorProtocol
from ...core.ports.parser_contracts import HTMLAnalyzerProtocol
from .heuristic_detector import HeuristicMainContentDetector


class DetectorFactory:
    """
    検出器ファクトリー
    設定に基づいて適切な検出器を作成
    """

    _detectors: Dict[str, Type[MainContentDetectorProtocol]] = {
        "heuristic": HeuristicMainContentDetector,
        # 将来的に追加される実装
        # "ai_gemini": GeminiMainContentDetector,
        # "hybrid": HybridMainContentDetector,
    }

    @classmethod
    def create(
        self,
        method: str,
        html_analyzer: HTMLAnalyzerProtocol,
        options: dict = None,
    ) -> MainContentDetectorProtocol:
        """
        検出器を作成

        Args:
            method: 検出手法 ("heuristic", "ai_gemini", "hybrid")
            html_analyzer: HTMLアナライザー
            options: 検出オプション

        Returns:
            MainContentDetectorProtocol: 検出器インスタンス

        Raises:
            ValueError: 不正な検出手法が指定された場合
        """
        if method not in self._detectors:
            available_methods = ", ".join(self._detectors.keys())
            raise ValueError(
                f"Unknown detection method: {method}. Available: {available_methods}"
            )

        detector_class = self._detectors[method]
        logger.info(f"Creating {method} detector")

        return detector_class(html_analyzer=html_analyzer, options=options or {})

    @classmethod
    def get_available_methods(cls) -> list[str]:
        """利用可能な検出手法を取得"""
        return list(cls._detectors.keys())
