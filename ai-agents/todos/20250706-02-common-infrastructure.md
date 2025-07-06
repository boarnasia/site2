# Todo 02: 共通インフラストラクチャの実装

## 目的

プロジェクト全体で使用する共通コンポーネントを実装する。

## 背景

各サービスが依存する基盤コンポーネント（設定管理、ログ、依存性注入など）を整備する必要がある。

## 成果物

1. **設定管理システム**
   - `src/site2/config/settings.py`
   - 環境変数とデフォルト値の管理

2. **依存性注入コンテナ**
   - `src/site2/core/container.py`
   - サービスの組み立て

3. **共通ユーティリティ**
   - `src/site2/core/utils/`
   - ファイル操作、URL処理など

## 実装詳細

### 1. 設定管理（pydantic-settings使用）

```python
# src/site2/config/settings.py
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # キャッシュ設定
    cache_dir: Path = Path.home() / ".cache" / "site2"
    cache_duration_hours: int = 24

    # クローラー設定
    wget_timeout: int = 30
    max_depth: int = 10
    user_agent: str = "site2/1.0"

    # 変換設定
    markdown_extensions: list[str] = ["extra", "codehilite"]
    pdf_options: dict = {"format": "A4"}

    # ログ設定
    log_level: str = "INFO"
    log_file: Optional[Path] = None

    class Config:
        env_prefix = "SITE2_"
        env_file = ".env"

# シングルトン
settings = Settings()
```

### 2. 依存性注入コンテナ

```python
# src/site2/core/container.py
from typing import Dict, Type, Any

class Container:
    """簡易DIコンテナ"""

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, callable] = {}

    def register(self, interface: Type, implementation: Any):
        """サービスを登録"""
        self._services[interface] = implementation

    def register_factory(self, interface: Type, factory: callable):
        """ファクトリを登録"""
        self._factories[interface] = factory

    def resolve(self, interface: Type) -> Any:
        """サービスを解決"""
        if interface in self._services:
            return self._services[interface]
        if interface in self._factories:
            return self._factories[interface]()
        raise ValueError(f"No registration for {interface}")

# アプリケーションコンテナの設定
def create_container() -> Container:
    container = Container()

    # リポジトリの登録
    container.register_factory(
        WebsiteCacheRepositoryProtocol,
        lambda: FileRepository(settings.cache_dir)
    )

    # クローラーの登録
    container.register_factory(
        WebCrawlerProtocol,
        lambda: WgetCrawler(timeout=settings.wget_timeout)
    )

    # サービスの登録
    container.register_factory(
        FetchServiceProtocol,
        lambda: FetchService(
            crawler=container.resolve(WebCrawlerProtocol),
            repository=container.resolve(WebsiteCacheRepositoryProtocol)
        )
    )

    return container
```

### 3. ログ設定

```python
# src/site2/core/logging.py
from loguru import logger
import sys

def setup_logging(settings: Settings):
    """ログの初期設定"""
    # 既存のハンドラを削除
    logger.remove()

    # コンソール出力
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    # ファイル出力（設定されている場合）
    if settings.log_file:
        logger.add(
            settings.log_file,
            rotation="10 MB",
            retention=10,
            level=settings.log_level
        )
```

### 4. 共通ユーティリティ

```python
# src/site2/core/utils/url_utils.py
from urllib.parse import urljoin, urlparse
from pathlib import Path

def resolve_relative_url(base_url: str, relative_url: str) -> str:
    """相対URLを絶対URLに変換"""
    return urljoin(base_url, relative_url)

def url_to_filename(url: str) -> str:
    """URLをファイル名に変換"""
    parsed = urlparse(url)
    path = parsed.path.strip("/") or "index"
    if not path.endswith(".html"):
        path += ".html"
    return path.replace("/", "_")

# src/site2/core/utils/file_utils.py
def ensure_directory(path: Path) -> Path:
    """ディレクトリを作成（既存の場合は何もしない）"""
    path.mkdir(parents=True, exist_ok=True)
    return path

def safe_write(path: Path, content: Union[str, bytes]):
    """安全にファイルを書き込み（アトミック）"""
    import tempfile

    # 一時ファイルに書き込み
    with tempfile.NamedTemporaryFile(
        dir=path.parent,
        delete=False,
        mode="wb" if isinstance(content, bytes) else "w"
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    # アトミックに移動
    tmp_path.replace(path)
```

## テスト要件

### 単体テスト

- [ ] 設定の読み込み（環境変数、デフォルト値）
- [ ] DIコンテナの動作
- [ ] URLユーティリティ
- [ ] ファイルユーティリティ

### 統合テスト

- [ ] 完全なコンテナの構築
- [ ] 設定の上書き

## 受け入れ基準

- [ ] 環境変数で設定を上書きできる
- [ ] DIコンテナですべてのサービスを解決できる
- [ ] ログが適切に出力される
- [ ] ユーティリティ関数が堅牢

## 推定工数

3-4時間

## 依存関係

- [01. 設計ドキュメントの完成](20250706-01-complete-design-docs.md)

## 次のタスク

→ [03. Fetchサービスの実装](20250706-03-implement-fetch-service.md)
