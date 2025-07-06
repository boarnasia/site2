from enum import Enum

import typer


class OutputFormat(str, Enum):
    """Output format for the CLI commands."""

    md = "md"
    pdf = "pdf"


app_plops = {
    "rich_markup_mode": None,
}

app = typer.Typer(**app_plops)


@app.command("auto")
def auto(
    uri: str = typer.Argument(..., help="The URI to fetch and process."),
    format: OutputFormat = typer.Option(
        "md", "--format", "-f", help="Output format (md or pdf)."
    ),
):
    """Fetch a URI and output in specified format."""
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
    """Pull a URIs and put to cache."""
    typer.echo(f"Pull Urls from: {uri}, force: {force}")


@app.command("fetch:list")
def fetch_list():
    """List all cached URIs."""
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
    """Detect main block from URI."""
    typer.echo(f"Detectting main block from: {uri}")


@app.command("detect:nav")
def detect_nav(
    uri: str = typer.Argument(..., help="The URI to detect navication block."),
):
    """Detect navication block from URI."""
    typer.echo(f"Detecting navication block from: {uri}")


@app.command("detect:order")
def detect_order(
    uri: str = typer.Argument(..., help="The URI to detect order of URIs."),
):
    """Detectting URIs order from URI."""
    typer.echo(f"Detectting URIs order from: {uri}")


@app.command("build")
def build(
    uri: str = typer.Argument(..., help="The URI to detect order of URIs."),
    format: OutputFormat = typer.Option(
        "md", "--format", "-f", help="Output format (md or pdf)."
    ),
):
    """Build md|pdf from URI."""
    typer.echo(f"Build {format.name} from URI: {uri}")


if __name__ == "__main__":
    app()
