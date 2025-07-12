# Todo 02: 共通インフラストラクチャの実装（dependency-injector版）

## 目的

プロジェクト全体で使用する共通コンポーネントを実装する。
dependency-injectorライブラリを使用した本格的なDI実装を行う。

## 背景

各サービスが依存する基盤コンポーネント（設定管理、ログ、依存性注入など）を整備する必要がある。
オリジナルのDIコンテナではなく、`dependency-injector`を使用することで、より堅牢で機能豊富なDI環境を構築する。

## 成果物

1. **設定管理システム**
   - `src/site2/config/settings.py`
   - 環境変数とデフォルト値の管理

2. **dependency-injectorベースのDIコンテナ**
   - `src/site2/core/containers.py`
   - 各サービスの依存性を定義

3. **共通ユーティリティ**
   - `src/site2/core/utils/`
   - ファイル操作、URL処理など

4. **アプリケーション初期化**
   - `src/site2/app.py`
   - DIコンテナの初期化とワイヤリング

## 実装詳細

### 1. 依存関係の追加

※依存関係は追加済みです

```toml
# pyproject.toml に追加
dependencies = [
    # 既存の依存関係...
    "dependency-injector>=4.40.0",
    "pydantic-settings>=2.0.0",
    "loguru>=0.7.0",
]
```

### 2. 設定管理（pydantic-settings使用）

```python
# src/site2/config/settings.py
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional, Dict, Any, List

class Settings(BaseSettings):
    """アプリケーション設定"""

    # キャッシュ設定
    cache_dir: Path = Path.home() / ".cache" / "site2"
    cache_duration_hours: int = 24

    # クローラー設定
    wget_timeout: int = 30
    max_depth: int = 10
    user_agent: str = "site2/1.0"
    crawl_delay: float = 1.0  # 秒

    # 変換設定
    markdown_extensions: List[str] = ["extra", "codehilite", "toc"]
    pdf_options: Dict[str, Any] = {
        "format": "A4",
        "margin": {"top": "1cm", "right": "1cm", "bottom": "1cm", "left": "1cm"}
    }

    # ログ設定
    log_level: str = "INFO"
    log_file: Optional[Path] = None
    log_format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

    # 開発・テスト設定
    debug: bool = False
    test_mode: bool = False

    model_config = {
        "env_prefix": "SITE2_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    def __post_init__(self):
        """設定後の初期化処理"""
        # キャッシュディレクトリの作成
        self.cache_dir.mkdir(parents=True, exist_ok=True)
```

### 3. dependency-injectorベースのDIコンテナ

```python
# src/site2/core/containers.py
from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from ..config.settings import Settings
from .ports.fetch_contracts import (
    FetchServiceProtocol,
    WebsiteCacheRepositoryProtocol,
    WebCrawlerProtocol,
)
from .ports.detect_contracts import DetectServiceProtocol
from .ports.build_contracts import BuildServiceProtocol
# 実装クラスは後で追加
# from ..adapters.repositories.file_repository import FileRepository
# from ..adapters.crawlers.wget_crawler import WgetCrawler
# from ..core.use_cases.fetch_service import FetchService

class Container(containers.DeclarativeContainer):
    """アプリケーションのDIコンテナ"""

    # 設定の注入
    config = providers.Configuration()

    # 設定オブジェクト
    settings = providers.Singleton(
        Settings,
    )

    # リポジトリ層
    website_cache_repository = providers.Factory(
        # FileRepository,  # 実装後に有効化
        providers.Object("placeholder"),  # 一時的なプレースホルダー
        cache_dir=settings.provided.cache_dir,
    )

    # インフラストラクチャ層
    web_crawler = providers.Factory(
        # WgetCrawler,  # 実装後に有効化
        providers.Object("placeholder"),  # 一時的なプレースホルダー
        timeout=settings.provided.wget_timeout,
        user_agent=settings.provided.user_agent,
        delay=settings.provided.crawl_delay,
    )

    # アプリケーションサービス層
    fetch_service = providers.Factory(
        # FetchService,  # 実装後に有効化
        providers.Object("placeholder"),  # 一時的なプレースホルダー
        crawler=web_crawler,
        repository=website_cache_repository,
    )

    detect_service = providers.Factory(
        # DetectService,  # 実装後に有効化
        providers.Object("placeholder"),  # 一時的なプレースホルダー
    )

    build_service = providers.Factory(
        # BuildService,  # 実装後に有効化
        providers.Object("placeholder"),  # 一時的なプレースホルダー
    )

class TestContainer(Container):
    """テスト用のDIコンテナ"""

    # テスト用の設定で上書き
    settings = providers.Singleton(
        Settings,
        test_mode=True,
        log_level="DEBUG",
        cache_dir="/tmp/site2_test_cache",
    )

    # テスト用のモックオブジェクトで上書き可能
    # web_crawler = providers.Factory(MockCrawler)
    # website_cache_repository = providers.Factory(MockRepository)
```

### 4. ログ設定

```python
# src/site2/core/logging.py
from loguru import logger
import sys
from pathlib import Path
from typing import Optional

def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    format_str: Optional[str] = None,
    debug: bool = False
):
    """ログの初期設定"""

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
```

### 5. アプリケーション初期化

```python
# src/site2/app.py
from dependency_injector.wiring import Provide, inject
from .core.containers import Container
from .core.logging import setup_logging
from .config.settings import Settings

def create_app(test_mode: bool = False) -> Container:
    """アプリケーションを初期化してDIコンテナを返す"""

    if test_mode:
        from .core.containers import TestContainer
        container = TestContainer()
    else:
        container = Container()

    # 設定の初期化
    container.config.from_pydantic(Settings())

    # ワイヤリング（CLIコマンドなど）
    container.wire(modules=[
        "site2.cli.commands",  # 実装後に追加
    ])

    # ログの初期化
    settings = container.settings()
    setup_logging(
        level=settings.log_level,
        log_file=settings.log_file,
        format_str=settings.log_format,
        debug=settings.debug,
    )

    return container

# 依存性注入の使用例
@inject
def some_function(
    fetch_service: FetchServiceProtocol = Provide[Container.fetch_service],
    settings: Settings = Provide[Container.settings],
) -> None:
    """依存性注入を使用する関数の例"""
    pass
```

### 6. 共通ユーティリティ

```python
# src/site2/core/utils/url_utils.py
from urllib.parse import urljoin, urlparse, quote, unquote
from pathlib import Path
import hashlib

def resolve_relative_url(base_url: str, relative_url: str) -> str:
    """相対URLを絶対URLに変換"""
    return urljoin(base_url, relative_url)

def url_to_filename(url: str, max_length: int = 255) -> str:
    """URLをファイル名に変換（ハッシュベース）"""
    parsed = urlparse(url)

    # パスからファイル名を生成
    path = parsed.path.strip("/") or "index"
    if not path.endswith((".html", ".htm")):
        path += ".html"

    # 安全なファイル名に変換
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in path)

    # 長すぎる場合はハッシュを使用
    if len(safe_name) > max_length - 10:  # ハッシュ分の余裕
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        safe_name = f"{safe_name[:max_length-10]}_{url_hash}.html"

    return safe_name

def is_same_domain(url1: str, url2: str) -> bool:
    """2つのURLが同じドメインかチェック"""
    domain1 = urlparse(url1).netloc.lower()
    domain2 = urlparse(url2).netloc.lower()
    return domain1 == domain2

# src/site2/core/utils/file_utils.py
from pathlib import Path
from typing import Union
import tempfile
import shutil
import hashlib

def ensure_directory(path: Path) -> Path:
    """ディレクトリを作成（既存の場合は何もしない）"""
    path.mkdir(parents=True, exist_ok=True)
    return path

def safe_write(path: Path, content: Union[str, bytes], encoding: str = "utf-8"):
    """安全にファイルを書き込み（アトミック）"""
    ensure_directory(path.parent)

    # 一時ファイルに書き込み
    with tempfile.NamedTemporaryFile(
        dir=path.parent,
        delete=False,
        mode="wb" if isinstance(content, bytes) else "w",
        encoding=encoding if isinstance(content, str) else None,
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    # アトミックに移動
    tmp_path.replace(path)

def calculate_file_hash(path: Path) -> str:
    """ファイルのハッシュ値を計算"""
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def copy_file_atomic(src: Path, dst: Path):
    """ファイルをアトミックにコピー"""
    ensure_directory(dst.parent)

    # 一時ファイルにコピー
    with tempfile.NamedTemporaryFile(dir=dst.parent, delete=False) as tmp:
        shutil.copy2(src, tmp.name)
        tmp_path = Path(tmp.name)

    # アトミックに移動
    tmp_path.replace(dst)
```

### 7. CLI統合

```python
# src/site2/cli/commands.py（将来実装）
from dependency_injector.wiring import Provide, inject
import typer
from ..core.containers import Container
from ..core.ports.fetch_contracts import FetchServiceProtocol

app = typer.Typer()

@app.command()
@inject
def fetch(
    url: str,
    fetch_service: FetchServiceProtocol = Provide[Container.fetch_service],
):
    """Webサイトをフェッチ"""
    # 実装は後で
    pass
```

## テスト要件

### 単体テスト

```python
# tests/unit/test_containers.py
import pytest
from site2.core.containers import Container, TestContainer
from site2.config.settings import Settings

def test_container_configuration():
    """DIコンテナの設定テスト"""
    container = Container()
    container.config.from_pydantic(Settings(test_mode=True))

    settings = container.settings()
    assert settings.test_mode is True

def test_test_container():
    """テスト用コンテナのテスト"""
    container = TestContainer()
    settings = container.settings()
    assert settings.test_mode is True
    assert "test" in str(settings.cache_dir)

# tests/unit/utils/test_url_utils.py
import pytest
from site2.core.utils.url_utils import resolve_relative_url, url_to_filename

def test_resolve_relative_url():
    base = "https://example.com/docs/"
    relative = "../api/index.html"
    result = resolve_relative_url(base, relative)
    assert result == "https://example.com/api/index.html"

def test_url_to_filename():
    url = "https://example.com/docs/api.html"
    filename = url_to_filename(url)
    assert filename.endswith(".html")
    assert len(filename) <= 255
```

### 統合テスト

- [ ] 完全なコンテナの構築とワイヤリング
- [ ] 設定の環境変数上書き
- [ ] テスト用コンテナの独立性

## 受け入れ基準

- [ ] dependency-injectorが正しく設定されている
- [ ] 環境変数で設定を上書きできる
- [ ] DIコンテナですべてのサービスを解決できる（プレースホルダー段階）
- [ ] ログが適切に出力される
- [ ] ユーティリティ関数が堅牢
- [ ] テスト用コンテナが本番用から独立している
- [ ] アトミックなファイル操作が実装されている

## 推定工数

4-5時間

## 依存関係

- [01. 設計ドキュメントの完成](20250706-01-complete-design-docs.md)
- [19. 契約定義のPydantic移行](completed) ✅

## 次のタスク

→ [03. Fetchサービスの実装](20250706-03-implement-fetch-service.md)

## 注意事項

### dependency-injectorの利点
1. **宣言的設定**: 依存関係の設定が明確
2. **ライフサイクル管理**: Singleton、Factory等の適切な管理
3. **設定の注入**: 外部設定の自動注入
4. **ワイヤリング**: 自動的な依存性の解決
5. **テスト支援**: テスト用の依存関係の差し替えが容易

### 段階的実装
1. まず基本構造とプレースホルダーを実装
2. 各サービス実装時に対応するプロバイダーを有効化
3. テストとともに依存関係を検証

### 設定管理の改善
- 環境別設定ファイルの対応
- バリデーション強化
- 機密情報の安全な管理
