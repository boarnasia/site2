#!/usr/bin/env python3
"""
site2 CLI - Convert websites to Markdown/PDF
"""

from typing import List, Optional

import typer
from loguru import logger
from pydantic import HttpUrl
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from .core.containers import Container
from .core.domain.fetch_domain import CrawlDepth
from .core.ports.fetch_contracts import (
    CachePermissionError,
    FetchError,
    FetchRequest,
    InvalidURLError,
    NetworkError,
)
from enum import Enum

# Typerアプリケーションとコンソール
app = typer.Typer(
    name="site2",
    help="Convert websites to Markdown/PDF documents",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()

# グローバルコンテナ（main()で初期化）
container: Optional[Container] = None


class OutputFormat(str, Enum):
    """Output format for the CLI commands."""

    md = "md"
    pdf = "pdf"


def version_callback(value: bool):
    """バージョン情報を表示"""
    if value:
        try:
            from . import __version__

            console.print(f"site2 version {__version__}")
        except ImportError:
            console.print("[red]Version information not found.[/red]")
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


@app.command("auto")
def auto(
    uri: str = typer.Argument(..., help="The URI to fetch and process."),
    format: OutputFormat = typer.Option(
        "md", "--format", "-f", help="Output format (md or pdf)."
    ),
):
    """Convert website to single markdown or PDF file and output to stdout."""
    console.print(f"Fetching {uri} and outputting as {format.name}.")


@app.command("fetch")
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
        1,  # Default depth as per wget standard
        "--depth",
        "-d",
        min=0,
        max=10,
        help="クロールする深さ（0は無制限、デフォルト: 1）",
    ),
) -> None:
    """Webサイトをフェッチしてキャッシュする"""
    fetch_service = container.fetch_service()

    try:
        # URLの検証
        try:
            url = HttpUrl(uri)
        except Exception:
            console.print(f"[red]Error: 無効なURL: {uri}[/red]")
            raise typer.Exit(1)

        # フェッチ実行
        with console.status(f"[bold green]Fetching {uri}...") as status:  # noqa: F841
            request = FetchRequest(
                url=url,
                force_refresh=force,
                depth=CrawlDepth(value=depth),
            )
            result = fetch_service.fetch(request)

        # 成功メッセージ
        rprint("\n[bold green]✓[/bold green] Fetch completed successfully!")
        rprint(f"  [cyan]Cache ID:[/cyan] {result.cache_id}")
        rprint(f"  [cyan]Root URL:[/cyan] {result.root_url}")
        rprint(f"  [cyan]Pages Fetched:[/cyan] {result.pages_fetched}")
        rprint(f"  [cyan]Pages Updated:[/cyan] {result.pages_updated}")
        rprint(f"  [cyan]Total Size:[/cyan] {result.total_size:,} bytes")
        rprint(f"  [cyan]Cache Directory:[/cyan] {result.cache_directory}")

        # 警告があれば表示
        if result.errors:
            rprint("\n[yellow]⚠ Warnings:[/yellow]")
            for error in result.errors:
                rprint(
                    f"  -{error.get('url', 'Unknown')}: {error.get('message', 'Unknown error')}"
                )

    except InvalidURLError as e:
        console.print(f"[red]Error: 無効なURL - {str(e)}[/red]")
        raise typer.Exit(1)
    except NetworkError as e:
        console.print(f"[red]Error: ネットワークエラー - {str(e)}[/red]")
        raise typer.Exit(2)
    except CachePermissionError as e:
        console.print(
            f"[red]Error: キャッシュディレクトリへのアクセス権限がありません - {str(e)}[/red]"
        )
        raise typer.Exit(3)
    except FetchError as e:
        console.print(f"[red]Error: フェッチエラー - {str(e)}[/red]")
        raise typer.Exit(4)
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        raise typer.Exit(5)


def _format_size(size_bytes: int) -> str:
    """バイトサイズを人間が読みやすい形式に変換"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


@app.command("fetch:list")
def fetch_list_command() -> None:
    """キャッシュ済みサイトの一覧を表示"""
    fetch_service = container.fetch_service()

    try:
        # キャッシュ一覧を取得
        result = fetch_service.list_caches()
        caches = result.caches

        if not caches:
            console.print("[yellow]キャッシュされたWebサイトはありません。[/yellow]")
            console.print(
                "\n[dim]Tip: 'site2 fetch <URL>' でWebサイトをキャッシュできます。[/dim]"
            )
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

        # 日付でソート
        sorted_caches = sorted(caches, key=lambda c: c["last_updated"], reverse=True)

        for cache in sorted_caches:
            size_bytes = cache["total_size"]
            size_str = _format_size(size_bytes)
            total_size += size_bytes
            total_pages += cache["page_count"]

            table.add_row(
                cache["url"].rstrip("/"),
                cache["id"][:8] + "...",
                str(cache["page_count"]),
                size_str,
                cache["last_updated"].split("T")[0],
            )

        # テーブルを表示
        console.print(table)

        # サマリー
        console.print(
            f"\n[dim]Total: {total_pages} pages, {_format_size(total_size)}[/dim]"
        )

    except Exception as e:
        logger.exception(f"Failed to list caches: {e}")
        console.print(
            f"[red]Error: キャッシュ一覧の取得に失敗しました - {str(e)}[/red]"
        )
        raise typer.Exit(1)


@app.command("detect:main")
def detect_main(
    uri: str = typer.Argument(..., help="The URI to detect main block."),
):
    """Detect CSS selector for main content block."""
    console.print(f"Detectting main block from: {uri}")


@app.command("detect:nav")
def detect_nav(
    uri: str = typer.Argument(..., help="The URI to detect navication block."),
):
    """Detect CSS selector for navigation block."""
    console.print(f"Detecting navication block from: {uri}")


@app.command("detect:order")
def detect_order(
    uri: str = typer.Argument(..., help="The URI to detect order of URIs."),
):
    """Detect and output document order to stdout."""
    console.print(f"Detectting URIs order from: {uri}")


@app.command("build")
def build(
    files_or_uris: List[str] = typer.Argument(..., help="Files or URIs to build."),
    format: OutputFormat = typer.Option(
        "md", "--format", "-f", help="Output format (md or pdf)."
    ),
):
    """Build and merge files/URIs to specified format and output to stdout."""
    console.print(f"Build {format.name} from: {', '.join(files_or_uris)}")


def setup_container() -> Container:
    """DIコンテナの設定"""
    container = Container()
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
        logger.exception(f"A fatal error occurred: {e}")
        console.print(f"[bold red]Fatal error:[/bold red] {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    main()
