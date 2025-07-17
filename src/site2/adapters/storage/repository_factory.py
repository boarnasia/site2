"""
リポジトリのファクトリークラス
"""

from typing import Dict, Type
from loguru import logger

from ...core.ports.fetch_contracts import WebsiteCacheRepositoryProtocol
from .file_repository import FileRepository


class RepositoryFactory:
    """リポジトリのファクトリークラス"""

    _repositories: Dict[str, Type[WebsiteCacheRepositoryProtocol]] = {
        "file": FileRepository,
        # 将来的な拡張
        # "redis": RedisRepository,
        # "database": DatabaseRepository,
    }

    @classmethod
    def create(cls, method: str = "file", **kwargs) -> WebsiteCacheRepositoryProtocol:
        """
        リポジトリを作成

        Args:
            method: リポジトリの種類 ("file", "redis", "database")
            **kwargs: リポジトリの初期化引数

        Returns:
            WebsiteCacheRepositoryProtocol: リポジトリインスタンス

        Raises:
            ValueError: 不正なリポジトリ種類が指定された場合
        """
        if method not in cls._repositories:
            available_methods = ", ".join(cls._repositories.keys())
            raise ValueError(
                f"Unknown repository method: {method}. Available: {available_methods}"
            )

        repository_class = cls._repositories[method]
        logger.info(f"Creating {method} repository")

        return repository_class(**kwargs)

    @classmethod
    def get_available_methods(cls) -> list[str]:
        """利用可能なリポジトリ種類を取得"""
        return list(cls._repositories.keys())
