from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.parse import urlparse

# from loguru import logger

CACHE_ROOT = Path(".cache")


def slugify(url: str) -> str:
    parsed = urlparse(url)
    slug = f"{parsed.netloc}{parsed.path}".strip("/")
    for ch in "/:?&=#%":
        slug = slug.replace(ch, "_")
    return slug or "root"


def run_wget(url: str, slug: str, depth: int) -> bool:
    target = CACHE_ROOT / slug
    parsed = urlparse(url)
    cmd = [
        "wget",
        "--recursive",
        f"--level={depth}",
        "--no-clobber",
        "--timestamping",
        "--page-requisites",
        "--html-extension",
        "--convert-links",
        "--restrict-file-names=windows",
        "--domains",
        parsed.netloc,
        "--no-parent",
        "-P",
        str(target),
        url,
    ]
    result = subprocess.run(cmd)
    return result.returncode == 0


def main() -> None:
    url = "https://pytest-bdd.readthedocs.io/en/stable/"
    slug = slugify(url)

    CACHE_ROOT.mkdir(parents=True, exist_ok=True)

    if run_wget(url, slug, 5):
        print(f"Downloaded {url} to {CACHE_ROOT / slug}")
    else:
        print(f"Failed to download {url}")


if __name__ == "__main__":
    main()
