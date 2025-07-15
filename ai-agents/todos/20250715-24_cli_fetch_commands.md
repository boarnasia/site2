# Task 24: CLIのfetch/fetch:listコマンド実装

## 背景
Task 03でFetchServiceの実装が完了した。実際に動作を確認しながら開発を進めるため、CLIコマンドを実装する。これにより：
- 実装したサービスの動作確認が可能
- ユーザー視点での機能検証
- 後続タスクのテストデータ準備

## 目的
`src/site2/cli.py`に以下のコマンドを実装する：
1. `site2 fetch <uri>` - Webサイトをフェッチしてキャッシュ
2. `site2 fetch:list` - キャッシュ済みサイトの一覧表示

## 実装内容

### 1. CLIコマンドの実装
```python
# src/site2/cli.py

import typer
from dependency_injector.wiring import inject, Provide
from rich.console import Console
from rich.table import Table
from rich import print

from .core.containers import Container
from .core.ports import FetchRequest, FetchServiceProtocol, WebsiteCacheRepositoryProtocol

app = typer.Typer(help="site2 - Convert websites to Markdown/PDF")
console = Console()

@app.command("fetch")
@inject
def fetch_command(
    uri: str = typer.Argument(..., help="WebサイトのURL"),
    force: bool = typer.Option(False, "--force", "-f", help="キャッシュを無視して強制的に再取得"),
    fetch_service: FetchServiceProtocol = Provide[Container.fetch_service],
) -> None:
    """Webサイトをフェッチしてキャッシュする"""
    try:
        with console.status(f"[bold green]Fetching {uri}..."):
            request = FetchRequest(url=uri, force_refresh=force)
            result = fetch_service.fetch(request)

        # 結果の表示
        print(f"[green]✓[/green] Fetch completed successfully!")
        print(f"  Cache ID: {result.cache_id}")
        print(f"  Pages fetched: {result.pages_fetched}")
        print(f"  Total size: {result.total_size:,} bytes")
        print(f"  Cache directory: {result.cache_directory}")

        if result.errors:
            print("[yellow]Warnings:[/yellow]")
            for error in result.errors:
                print(f"  - {error.get('message', 'Unknown error')}")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command("fetch:list")
@inject
def fetch_list_command(
    repository: WebsiteCacheRepositoryProtocol = Provide[Container.website_cache_repository],
) -> None:
    """キャッシュ済みサイトの一覧を表示"""
    try:
        caches = repository.find_all()

        if not caches:
            console.print("[yellow]No cached websites found.[/yellow]")
            return

        # テーブルで表示
        table = Table(title="Cached Websites")
        table.add_column("URL", style="cyan")
        table.add_column("Cache ID", style="green")
        table.add_column("Pages", justify="right")
        table.add_column("Size", justify="right")
        table.add_column("Last Updated")

        for cache in caches:
            table.add_row(
                str(cache.url),
                cache.id[:8] + "...",  # IDを短縮表示
                str(len(cache.pages)),
                f"{cache.total_size:,}",
                cache.last_updated.strftime("%Y-%m-%d %H:%M")
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)
```

### 2. DIコンテナの設定
```python
# src/site2/cli.py の main() 関数

def main():
    """メインエントリーポイント"""
    # コンテナの初期化と設定
    container = Container()
    container.config.from_dict({
        "cache_dir": str(Path.home() / ".cache" / "site2"),
        "log_level": "INFO",
    })

    # 依存性注入の設定
    container.wire(modules=[__name__])

    # CLIアプリケーションの実行
    app()
```

### 3. 実装時の注意点
- FetchServiceは同期的（非async）
- エラーハンドリングを適切に実装
- Rich libraryを使った見やすい出力
- 依存性注入によるサービスの取得

## テスト要件

### 1. 単体テスト
- [ ] `fetch`コマンドのテスト
  - [ ] 正常なフェッチ
  - [ ] force オプション
  - [ ] エラーケース
- [ ] `fetch:list`コマンドのテスト
  - [ ] キャッシュがある場合
  - [ ] キャッシュが空の場合

### 2. 統合テスト
- [ ] 実際のFetchServiceとの連携
- [ ] DIコンテナの動作確認

### 3. 手動テスト
```bash
# 基本的なフェッチ
site2 fetch https://example.com

# 強制更新
site2 fetch --force https://example.com

# キャッシュ一覧
site2 fetch:list
```

## 成功基準
- [ ] `site2 fetch <url>`でWebサイトがキャッシュされる
- [ ] `site2 fetch:list`でキャッシュ一覧が表示される
- [ ] エラー時に適切なメッセージが表示される
- [ ] Rich libraryによる見やすい出力
- [ ] DIコンテナが正しく動作する

## 期待される成果物
1. 更新された`src/site2/cli.py`
2. CLIコマンドのテスト
3. 動作確認のスクリーンショット（オプション）

## 依存関係
- Task 03: FetchService実装（完了）
- Task 02: 共通インフラストラクチャ（DIコンテナ）

## 推定工数
2-3時間

## 次のステップ
CLI実装により動作確認が可能になった後：
- Task 04: HTMLパーサーの実装
- 順次、detect系のCLIコマンドも追加実装
