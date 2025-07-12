"""
ログシステム

loguru使用のログ設定とセットアップ機能
"""

from loguru import logger
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    format_str: Optional[str] = None,
    debug: bool = False,
) -> None:
    """
    ログの初期設定

    Args:
        level: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        log_file: ログファイルのパス（Noneの場合はファイル出力なし）
        format_str: ログフォーマット文字列（Noneの場合はデフォルト使用）
        debug: デバッグモードフラグ（詳細なエラー情報を出力）
    """

    # デフォルトフォーマット
    if format_str is None:
        format_str = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )

    # 既存のハンドラを削除
    logger.remove()

    # コンソール出力
    logger.add(
        sys.stderr,
        level=level,
        format=format_str,
        colorize=True,
        diagnose=debug,
        backtrace=debug,
    )

    # ファイル出力（設定されている場合）
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_file,
            rotation="10 MB",
            retention=10,
            level=level,
            format=format_str,
            diagnose=debug,
            backtrace=debug,
        )

    logger.info(f"Logging initialized: level={level}, file={log_file}")


def get_logger(name: str = None):
    """
    ロガーインスタンスを取得

    Args:
        name: ロガー名（Noneの場合は呼び出し元のモジュール名を使用）

    Returns:
        loguru.logger インスタンス
    """
    if name:
        return logger.bind(name=name)
    return logger
