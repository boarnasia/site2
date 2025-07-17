"""
アプリケーション設定管理

pydantic-settingsを使用した環境変数対応の設定システム
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional, Dict, Any, List


class Settings(BaseSettings):
    """アプリケーション設定"""

    # キャッシュ設定
    cache_dir: Path = Path.home() / ".cache" / "site2"
    cache_duration_hours: int = 24

    # クローラー設定
    wget_timeout: int = 30  # 各ページ取得のタイムアウト（秒）
    max_depth: int = 10
    user_agent: str = "site2/1.0"
    crawl_delay: float = 1.0  # 秒

    # 変換設定
    markdown_extensions: List[str] = ["extra", "codehilite", "toc"]
    pdf_options: Dict[str, Any] = {
        "format": "A4",
        "margin": {"top": "1cm", "right": "1cm", "bottom": "1cm", "left": "1cm"},
    }

    # ログ設定
    log_level: str = "INFO"
    log_file: Optional[Path] = None
    log_format: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # 開発・テスト設定
    debug: bool = False
    test_mode: bool = False

    # API設定（既存）
    gemini_api_key: str = ""

    model_config = SettingsConfigDict(
        env_prefix="SITE2_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",  # 追加設定を許可
    )

    def model_post_init(self, __context) -> None:
        """設定後の初期化処理"""
        # キャッシュディレクトリの作成
        if not self.test_mode:  # テストモードでは自動作成しない
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def is_development(self) -> bool:
        """開発環境かどうか"""
        return self.debug or self.test_mode

    def get_cache_path(self, subdirectory: str = "") -> Path:
        """キャッシュパスを取得"""
        if subdirectory:
            return self.cache_dir / subdirectory
        return self.cache_dir

    def get_log_config(self) -> Dict[str, Any]:
        """ログ設定を取得"""
        return {
            "level": self.log_level,
            "file": self.log_file,
            "format": self.log_format,
            "debug": self.debug,
        }
