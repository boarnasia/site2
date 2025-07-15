# Execute Task 24: CLIのfetch/fetch:listコマンド実装

## Commander Role: タスク分析と設計

### 目的
Task 03で実装したFetchServiceを実際に使えるようにCLIコマンドを実装します。これにより：
- 開発中の動作確認が容易に
- 実際のWebサイトでのテストが可能
- 後続タスクのためのテストデータ準備

### 実装方針
1. Typerを使った直感的なCLI
2. dependency-injectorによるDI
3. Richによる美しい出力
4. 適切なエラーハンドリング

## Worker Role: 実装手順

### Step 1: 必要なimportと基本構造

```python
# src/site2/cli.py

#!/usr/bin/env python3
"""
site2 CLI - Convert websites to Markdown/PDF
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from dependency_injector.wiring import inject, Provide
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from pydantic import HttpUrl

from .core.containers import Container
from .core.ports import (
    FetchServiceProtocol,
    WebsiteCacheRepositoryProtocol,
    FetchRequest,
    FetchError,
    InvalidURLError,
    NetworkError,
    CachePermissionError,
)

# Typerアプリケーションとコンソール
app = typer.Typer(
    name="site2",
    help="Convert websites to Markdown/PDF documents",
    add_completion=False,
)
console = Console()

# グローバルコンテナ（main()で初期化）
container: Optional[Container] = None
```

### Step 2: fetchコマンドの実装

```python
@app.command("fetch")
@inject
def fetch_command(
    uri: str = typer.Argument(
        ...,
        help="WebサイトのURL (例: https://example.com)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="キャッシュを無視して強制的に再取得",
    ),
    depth: int = typer.Option(
        3,
        "--depth",
        "-d",
        min=0,
        max=10,
        help="クロールする深さ（デフォルト: 3）",
    ),
    fetch_service: FetchServiceProtocol = Provide[Container.fetch_service],
) -> None:
    """Webサイトをフェッチしてキャッシュする"""

    try:
        # URLの検証
        try:
            url = HttpUrl(uri)
        except Exception:
            console.print(f"[red]Error: 無効なURL: {uri}[/red]")
            raise typer.Exit(1)

        # フェッチ実行
        with console.status(f"[bold green]Fetching {uri}...") as status:
            request = FetchRequest(
                url=url,
                force_refresh=force,
                depth=depth,
            )
            result = fetch_service.fetch(request)

        # 成功メッセージ
        rprint("\n[bold green]✓[/bold green] Fetch completed successfully!")
        rprint(f"  [cyan]Cache ID:[/cyan] {result.cache_id}")
        rprint(f"  [cyan]Root URL:[/cyan] {result.root_url}")
        rprint(f"  [cyan]Pages fetched:[/cyan] {result.pages_fetched}")
        rprint(f"  [cyan]Pages updated:[/cyan] {result.pages_updated}")
        rprint(f"  [cyan]Total size:[/cyan] {result.total_size:,} bytes")
        rprint(f"  [cyan]Cache directory:[/cyan] {result.cache_directory}")

        # 警告があれば表示
        if result.errors:
            rprint("\n[yellow]⚠ Warnings:[/yellow]")
            for error in result.errors:
                rprint(f"  - {error.get('url', 'Unknown')}: {error.get('message', 'Unknown error')}")

    except InvalidURLError as e:
        console.print(f"[red]Error: 無効なURL - {str(e)}[/red]")
        raise typer.Exit(1)
    except NetworkError as e:
        console.print(f"[red]Error: ネットワークエラー - {str(e)}[/red]")
        raise typer.Exit(2)
    except CachePermissionError as e:
        console.print(f"[red]Error: キャッシュディレクトリへのアクセス権限がありません - {str(e)}[/red]")
        raise typer.Exit(3)
    except FetchError as e:
        console.print(f"[red]Error: フェッチエラー - {str(e)}[/red]")
        raise typer.Exit(4)
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        raise typer.Exit(5)
```

### Step 3: fetch:listコマンドの実装

```python
@app.command("fetch:list", name="fetch:list")
@inject
def fetch_list_command(
    repository: WebsiteCacheRepositoryProtocol = Provide[Container.website_cache_repository],
) -> None:
    """キャッシュ済みサイトの一覧を表示"""

    try:
        # キャッシュ一覧を取得
        caches = repository.find_all()

        if not caches:
            console.print("[yellow]キャッシュされたWebサイトはありません。[/yellow]")
            console.print("\n[dim]Tip: 'site2 fetch <URL>' でWebサイトをキャッシュできます。[/dim]")
            return

        # テーブルの作成
        table = Table(
            title=f"Cached Websites ({len(caches)} sites)",
            show_header=True,
            header_style="bold magenta",
        )

        # カラムの定義
        table.add_column("URL", style="cyan", no_wrap=True)
        table.add_column("Cache ID", style="green")
        table.add_column("Pages", justify="right", style="yellow")
        table.add_column("Size", justify="right", style="blue")
        table.add_column("Last Updated", style="white")

        # データの追加
        total_size = 0
        total_pages = 0

        for cache in sorted(caches, key=lambda c: c.last_updated, reverse=True):
            # サイズの人間が読みやすい表記
            size_str = _format_size(cache.total_size)
            total_size += cache.total_size
            total_pages += len(cache.pages)

            table.add_row(
                str(cache.url).rstrip('/'),
                cache.id[:8] + "...",
                str(len(cache.pages)),
                size_str,
                cache.last_updated.strftime("%Y-%m-%d %H:%M"),
            )

        # テーブルを表示
        console.print(table)

        # サマリー
        console.print(
            f"\n[dim]Total: {total_pages} pages, {_format_size(total_size)}[/dim]"
        )

    except Exception as e:
        console.print(f"[red]Error: キャッシュ一覧の取得に失敗しました - {str(e)}[/red]")
        raise typer.Exit(1)


def _format_size(size_bytes: int) -> str:
    """バイトサイズを人間が読みやすい形式に変換"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
```

### Step 4: メイン関数とDI設定

```python
def setup_container() -> Container:
    """DIコンテナの設定"""
    container = Container()

    # 設定の読み込み（環境変数やconfigファイルから）
    config = {
        "cache_dir": str(Path.home() / ".cache" / "site2"),
        "log_level": "INFO",
        "wget_timeout": 30,
        "user_agent": "site2/1.0",
        "crawl_delay": 0.5,
    }

    container.config.from_dict(config)

    # 依存性注入の設定
    container.wire(modules=[sys.modules[__name__]])

    return container


def main():
    """メインエントリーポイント"""
    global container

    try:
        # コンテナの初期化
        container = setup_container()

        # CLIアプリケーションの実行
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[red]Fatal error: {str(e)}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    main()
```

### Step 5: ヘルプとバージョン情報の追加

```python
def version_callback(value: bool):
    """バージョン情報を表示"""
    if value:
        from . import __version__
        console.print(f"site2 version {__version__}")
        raise typer.Exit()


@app.callback()
def callback(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="バージョン情報を表示",
    ),
):
    """
    site2 - Convert websites to Markdown/PDF

    Webサイトをローカルにキャッシュし、Markdown形式やPDF形式に変換するツールです。
    """
    pass
```

## テスト実装のポイント

1. **モックの使用**
   - FetchServiceとRepositoryをモック
   - 実際のネットワークアクセスは行わない

2. **CLIテストの方法**
   - CliRunnerを使用
   - 出力内容の検証
   - 終了コードの確認

3. **エラーケースのテスト**
   - 各種例外のハンドリング確認
   - 適切なエラーメッセージの表示

## 動作確認

```bash
# インストール
pip install -e .

# ヘルプの表示
site2 --help
site2 fetch --help

# Webサイトのフェッチ
site2 fetch https://example.com
site2 fetch https://example.com --force
site2 fetch https://example.com --depth 2

# キャッシュ一覧
site2 fetch:list
```

これで、FetchServiceを実際に使用できるCLIが完成します。
