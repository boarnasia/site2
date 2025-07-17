"""
クローラーのファクトリークラス
"""

from typing import Dict, Type
from loguru import logger

from ...core.ports.fetch_contracts import WebCrawlerProtocol
from .wget_crawler import WgetCrawler


class CrawlerFactory:
    """クローラーのファクトリークラス"""

    _crawlers: Dict[str, Type[WebCrawlerProtocol]] = {
        "wget": WgetCrawler,
        # 将来的な拡張
        # "selenium": SeleniumCrawler,
        # "requests": RequestsCrawler,
    }

    @classmethod
    def create(cls, method: str = "wget", **kwargs) -> WebCrawlerProtocol:
        """
        クローラーを作成

        Args:
            method: クローラーの種類 ("wget", "selenium", "requests")
            **kwargs: クローラーの初期化引数

        Returns:
            WebCrawlerProtocol: クローラーインスタンス

        Raises:
            ValueError: 不正なクローラー種類が指定された場合
        """
        if method not in cls._crawlers:
            available_methods = ", ".join(cls._crawlers.keys())
            raise ValueError(
                f"Unknown crawler method: {method}. Available: {available_methods}"
            )

        crawler_class = cls._crawlers[method]
        logger.info(f"Creating {method} crawler")

        return crawler_class(**kwargs)

    @classmethod
    def get_available_methods(cls) -> list[str]:
        """利用可能なクローラー種類を取得"""
        return list(cls._crawlers.keys())
