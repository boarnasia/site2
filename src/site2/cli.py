from enum import Enum
from typing import List

import typer


class OutputFormat(str, Enum):
    """Output format for the CLI commands."""

    md = "md"
    pdf = "pdf"


app_plops = {
    "rich_markup_mode": None,
    "help": "site2 - Convert websites to single markdown or PDF files",
}

app = typer.Typer(**app_plops)


@app.command("auto")
def auto(
    uri: str = typer.Argument(..., help="The URI to fetch and process."),
    format: OutputFormat = typer.Option(
        "md", "--format", "-f", help="Output format (md or pdf)."
    ),
):
    """Convert website to single markdown or PDF file and output to stdout."""
    """
    <query>
    このサブコマンド名でいいのだろうか？
    </query>
    """
    typer.echo(f"Fetching {uri} and outputting as {format.name}.")


@app.command("fetch")
def fetch(
    uri: str = typer.Argument(..., help="The URI to fetch and cache."),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force fetching even if already cached."
    ),
):
    """Fetch and cache website content recursively."""
    typer.echo(f"Pull Urls from: {uri}, force: {force}")


@app.command("fetch:list")
def fetch_list():
    """List all cached sites."""
    """
    <query>
    このサブコマンド名でいいのだろうか？
    </query>
    """
    typer.echo("List cached URIs.")


@app.command("detect:main")
def detect_main(
    uri: str = typer.Argument(..., help="The URI to detect main block."),
):
    """Detect CSS selector for main content block."""
    typer.echo(f"Detectting main block from: {uri}")


@app.command("detect:nav")
def detect_nav(
    uri: str = typer.Argument(..., help="The URI to detect navication block."),
):
    """Detect CSS selector for navigation block."""
    typer.echo(f"Detecting navication block from: {uri}")


@app.command("detect:order")
def detect_order(
    uri: str = typer.Argument(..., help="The URI to detect order of URIs."),
):
    """Detect and output document order to stdout."""
    typer.echo(f"Detectting URIs order from: {uri}")


@app.command("build")
def build(
    files_or_uris: List[str] = typer.Argument(..., help="Files or URIs to build."),
    format: OutputFormat = typer.Option(
        "md", "--format", "-f", help="Output format (md or pdf)."
    ),
):
    """Build and merge files/URIs to specified format and output to stdout."""
    typer.echo(f"Build {format.name} from: {', '.join(files_or_uris)}")


if __name__ == "__main__":
    app()
