#!/usr/bin/env python3
"""
site2 CLI - Convert websites to Markdown/PDF
"""

from typing import List, Optional
from pathlib import Path
import sys

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
    output: str = typer.Argument(..., help="Output file path."),
    format: OutputFormat = typer.Option(
        "md", "--format", "-f", help="Output format (md or pdf)."
    ),
):
    """Convert website to single markdown or PDF file and output to specified file."""
    from pathlib import Path

    try:
        # 出力パスの検証
        output_path = Path(output)
        if output_path.exists() and not typer.confirm(
            f"File {output} already exists. Overwrite?"
        ):
            console.print("Operation cancelled.")
            sys.exit(0)
        # DIコンテナの初期化
        from .core.containers import Container

        container = Container()
        container.config.from_dict({})

        # 各サービスの取得
        fetch_service = container.fetch_service()
        detect_service = container.detect_service()
        build_service = container.build_service()

        console.print(f"🌐 Fetching: {uri}")

        # 1. fetch - Webサイトの取得
        from .core.ports.fetch_contracts import FetchRequest

        fetch_request = FetchRequest(url=uri)
        fetch_result = fetch_service.fetch(fetch_request)

        console.print(f"✅ Cached to: {fetch_result.cache_directory}")
        console.print(f"📁 Files: {len(fetch_result.cached_files)} downloaded")

        # 2. detect:main - メインコンテンツ検出
        console.print("🔍 Detecting main content...")

        # インデックスファイルの検索
        index_file = _find_index_file(fetch_result.cached_files)
        if not index_file:
            console.print("❌ Error: No index file found")
            sys.exit(1)

        # メインコンテンツセレクタの検出
        from .core.domain.detect_domain import MainContentDetectionRequest

        main_request = MainContentDetectionRequest(file_path=index_file)
        main_result = detect_service.detect_main_content(main_request)

        console.print(f"🎯 Main selector: {main_result.main_selector}")

        # 3. detect:order - ドキュメント順序検出
        console.print("📋 Detecting document order...")

        from .core.domain.detect_domain import DocumentOrderRequest

        order_request = DocumentOrderRequest(
            directory_path=fetch_result.cache_directory, file_patterns=["*.html"]
        )
        order_result = detect_service.detect_document_order(order_request)

        console.print(f"📚 Found {len(order_result.ordered_files)} documents")

        # 4. build - ドキュメント生成
        console.print(f"🔨 Building {format.name.upper()} document...")

        from .core.ports.build_contracts import BuildRequest
        from .core.domain.build_domain import OutputFormat as BuildOutputFormat

        # OutputFormatの変換
        build_format = (
            BuildOutputFormat.MARKDOWN
            if format.name.lower() == "md"
            else BuildOutputFormat.PDF
        )

        build_request = BuildRequest(
            cache_directory=fetch_result.cache_directory,
            main_selector=main_result.main_selector,
            ordered_files=order_result.ordered_files,
            doc_order=order_result,
            format=build_format,
            output_path=output_path,
            options={},
        )

        build_result = build_service.build(build_request)

        # 5. ファイルへの出力
        if isinstance(build_result.content, str):
            # Markdownの場合
            output_path.write_text(build_result.content, encoding="utf-8")
        else:
            # PDFの場合
            output_path.write_bytes(build_result.content)

        # 成功メッセージと統計情報の出力
        stats = build_result.statistics
        console.print(f"✅ Generated {build_format.value}: {output_path}")
        console.print(
            f"📊 Stats: {stats.get('total_files', 0)} files, "
            f"{stats.get('total_text_length', 0)} characters"
        )

    except Exception as e:
        sys.stderr.write(f"❌ Error: {str(e)}\n")
        sys.exit(1)


def _find_index_file(cached_files: list) -> Path:
    """
    インデックスファイルを検索

    Args:
        cached_files: キャッシュされたファイルのリスト

    Returns:
        Path: インデックスファイルのパス（見つからない場合はNone）
    """

    # index.html を優先的に検索
    for file_path in cached_files:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        if file_path.name.lower() == "index.html":
            return file_path

    # index.html が見つからない場合は最初の .html ファイルを使用
    for file_path in cached_files:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        if file_path.suffix.lower() == ".html":
            return file_path

    return None


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
    import json

    try:
        # DIコンテナの初期化
        from .core.containers import Container

        container = Container()
        container.config.from_dict({})

        # サービスの取得
        fetch_service = container.fetch_service()
        detect_service = container.detect_service()

        # 1. Webサイトの取得
        from .core.ports.fetch_contracts import FetchRequest

        fetch_request = FetchRequest(url=uri)
        fetch_result = fetch_service.fetch(fetch_request)

        # 2. インデックスファイルの検索
        index_file = _find_index_file(fetch_result.cached_files)
        if not index_file:
            sys.stderr.write("❌ Error: No index file found\n")
            sys.exit(1)

        # 3. メインコンテンツセレクタの検出
        from .core.domain.detect_domain import MainContentDetectionRequest

        main_request = MainContentDetectionRequest(file_path=index_file)
        main_result = detect_service.detect_main_content(main_request)

        # 4. JSON形式で結果を出力
        result = {
            "main_selector": main_result.main_selector,
            "confidence": main_result.confidence,
            "file_path": str(index_file),
            "detected_candidates": [
                {
                    "selector": candidate.selector,
                    "score": candidate.score,
                    "reasons": candidate.reasons,
                }
                for candidate in main_result.candidates
            ],
        }

        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)

    except Exception as e:
        sys.stderr.write(f"❌ Error: {str(e)}\n")
        sys.exit(1)


@app.command("detect:nav")
def detect_nav(
    uri: str = typer.Argument(..., help="The URI to detect navication block."),
):
    """Detect CSS selector for navigation block."""
    import json

    try:
        # DIコンテナの初期化
        from .core.containers import Container

        container = Container()
        container.config.from_dict({})

        # サービスの取得
        fetch_service = container.fetch_service()
        detect_service = container.detect_service()

        # 1. Webサイトの取得
        from .core.ports.fetch_contracts import FetchRequest

        fetch_request = FetchRequest(url=uri)
        fetch_result = fetch_service.fetch(fetch_request)

        # 2. インデックスファイルの検索
        index_file = _find_index_file(fetch_result.cached_files)
        if not index_file:
            sys.stderr.write("❌ Error: No index file found\n")
            sys.exit(1)

        # 3. ナビゲーションセレクタの検出
        from .core.domain.detect_domain import NavigationDetectionRequest

        nav_request = NavigationDetectionRequest(file_path=index_file)
        nav_result = detect_service.detect_navigation(nav_request)

        # 4. JSON形式で結果を出力
        result = {
            "navigation_selector": nav_result.nav_selector,
            "confidence": nav_result.confidence,
            "file_path": str(index_file),
            "detected_links": [
                {"url": link.url, "text": link.text, "order": link.order}
                for link in nav_result.navigation_links
            ],
        }

        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)

    except Exception as e:
        sys.stderr.write(f"❌ Error: {str(e)}\n")
        sys.exit(1)


@app.command("detect:order")
def detect_order(
    uri: str = typer.Argument(..., help="The URI to detect order of URIs."),
):
    """Detect and output document order to stdout."""
    import json

    try:
        # DIコンテナの初期化
        from .core.containers import Container

        container = Container()
        container.config.from_dict({})

        # サービスの取得
        fetch_service = container.fetch_service()
        detect_service = container.detect_service()

        # 1. Webサイトの取得
        from .core.ports.fetch_contracts import FetchRequest

        fetch_request = FetchRequest(url=uri)
        fetch_result = fetch_service.fetch(fetch_request)

        # 2. ドキュメント順序の検出
        from .core.domain.detect_domain import DocumentOrderRequest

        order_request = DocumentOrderRequest(
            directory_path=fetch_result.cache_directory, file_patterns=["*.html"]
        )
        order_result = detect_service.detect_document_order(order_request)

        # 3. JSON形式で結果を出力
        result = {
            "ordered_files": [
                {
                    "order": file_info.order,
                    "path": str(file_info.path),
                    "title": file_info.title,
                    "level": file_info.level,
                }
                for file_info in order_result.ordered_files
            ],
            "total_files": len(order_result.ordered_files),
            "cache_directory": str(fetch_result.cache_directory),
        }

        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)

    except Exception as e:
        sys.stderr.write(f"❌ Error: {str(e)}\n")
        sys.exit(1)


@app.command("build")
def build(
    files_or_uris: List[str] = typer.Argument(..., help="Files or URIs to build."),
    format: OutputFormat = typer.Option(
        "md", "--format", "-f", help="Output format (md or pdf)."
    ),
):
    """Build and merge files/URIs to specified format and output to stdout."""
    from pathlib import Path

    try:
        # DIコンテナの初期化
        from .core.containers import Container

        container = Container()
        container.config.from_dict({})

        # サービスの取得
        build_service = container.build_service()

        # ファイルパスのリストを作成
        file_paths = []
        for item in files_or_uris:
            if item.startswith(("http://", "https://")):
                # URIの場合はエラー（この実装では直接URIをサポートしない）
                sys.stderr.write(
                    f"❌ Error: URI support not implemented in build command: {item}\n"
                )
                sys.stderr.write("Hint: Use 'auto' command for URI processing\n")
                sys.exit(1)
            else:
                # ファイルパスとして処理
                path = Path(item)
                if not path.exists():
                    sys.stderr.write(f"❌ Error: File not found: {path}\n")
                    sys.exit(1)
                file_paths.append(path)

        # BuildRequestの作成
        from .core.ports.build_contracts import BuildRequest
        from .core.domain.build_domain import (
            OutputFormat as BuildOutputFormat,
            DocumentOrder,
            OrderedFile,
        )

        # OutputFormatの変換
        build_format = (
            BuildOutputFormat.MARKDOWN
            if format.name.lower() == "md"
            else BuildOutputFormat.PDF
        )

        # 簡単なDocumentOrderとOrderedFileの作成
        ordered_files = [
            OrderedFile(order=i + 1, path=path, title=path.stem, level=1)
            for i, path in enumerate(file_paths)
        ]

        doc_order = DocumentOrder(
            ordered_files=ordered_files, total_files=len(ordered_files)
        )

        build_request = BuildRequest(
            cache_directory=file_paths[0].parent if file_paths else Path.cwd(),
            main_selector="body",  # デフォルトセレクタ
            ordered_files=ordered_files,
            doc_order=doc_order,
            format=build_format,
            output_path=None,  # stdoutに出力するためNone
            options={},
        )

        # ビルド実行
        build_result = build_service.build(build_request)

        # 標準出力への出力
        if isinstance(build_result.content, str):
            # Markdownの場合
            sys.stdout.write(build_result.content)
        else:
            # PDFの場合
            sys.stdout.buffer.write(build_result.content)

        # 統計情報の出力（stderr）
        stats = build_result.statistics
        console.print(
            f"✅ Built {build_format.value}: {stats.get('total_files', 0)} files, "
            f"{stats.get('total_text_length', 0)} characters"
        )

    except Exception as e:
        sys.stderr.write(f"❌ Error: {str(e)}\n")
        sys.exit(1)


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
