"""
アプリケーション初期化

dependency-injectorコンテナとログ設定の初期化を管理
"""

from dependency_injector.wiring import Provide, inject
from .core.containers import Container, TestContainer
from .core.logging import setup_logging
from .config.settings import Settings


def create_app(test_mode: bool = False) -> Container:
    """
    アプリケーションを初期化してDIコンテナを返す

    Args:
        test_mode: テストモードフラグ

    Returns:
        初期化されたDIコンテナ
    """

    if test_mode:
        container = TestContainer()
    else:
        container = Container()

    # ワイヤリング（CLIコマンドなど）
    # プレースホルダー段階では、まだ実装されていないモジュールのワイヤリングは行わない
    # container.wire(modules=[
    #     "site2.cli.commands",  # 実装後に追加
    # ])

    # ログの初期化
    settings = container.settings()
    log_config = settings.get_log_config()
    setup_logging(
        level=log_config["level"],
        log_file=log_config["file"],
        format_str=log_config["format"],
        debug=log_config["debug"],
    )

    return container


# 依存性注入の使用例
@inject
def example_function(
    fetch_service: object = Provide[
        Container.fetch_service
    ],  # プレースホルダー期間中はobject型
    settings: Settings = Provide[Container.settings],
) -> None:
    """依存性注入を使用する関数の例"""
    pass
