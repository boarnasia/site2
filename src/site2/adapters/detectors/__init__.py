"""
メインコンテンツ検出器アダプター
"""

from .heuristic_detector import HeuristicMainContentDetector
from .detector_factory import DetectorFactory

__all__ = [
    "HeuristicMainContentDetector",
    "DetectorFactory",
]
