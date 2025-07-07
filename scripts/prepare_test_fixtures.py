#!/usr/bin/env python3
"""テスト用のWebサイトデータを準備するスクリプト"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures" / "websites"

# ダウンロード対象のURL一覧
DOWNLOAD_URLS = {
    "pytest-bdd-docs": "https://pytest-bdd.readthedocs.io/en/stable/",
    "claude-code-docs": "https://docs.anthropic.com/en/docs/claude-code/overview",
}


def slugify(url: str) -> str:
    """URLをファイル名に適したスラッグに変換"""
    parsed = urlparse(url)
    slug = f"{parsed.netloc}{parsed.path}".strip("/")
    for ch in "/:?&=#%":
        slug = slug.replace(ch, "_")
    return slug or "root"


def download_docs(site_name: str, url: str) -> bool:
    """ドキュメントをダウンロードする"""
    dir_name = FIXTURE_DIR / site_name

    if dir_name.exists():
        print(f"⚠️  {site_name} already exists. Skipping download.")
        print(f"   To re-download, remove: {dir_name}")
        return True

    print(f"📥 Downloading {site_name} documentation...")

    parsed = urlparse(url)
    domain = parsed.netloc

    # wgetコマンドを実行
    cmd = [
        "wget",
        "-r",
        "-l",
        "2",
        "-np",
        "-k",
        "-E",
        "-H",
        f"-D{domain}",
        "--convert-links",
        "--adjust-extension",
        "--page-requisites",
        "--no-parent",
        "--wait=0.5",
        "--random-wait",
        "-P",
        str(dir_name),
        url,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # wgetは404エラーなどがあっても部分的に成功することがある
        # ディレクトリが作成され、何らかのファイルがダウンロードされていれば成功とみなす
        if dir_name.exists() and any(dir_name.rglob("*.html")):
            print(f"✅ {site_name} docs downloaded successfully")

            # メタデータファイルを作成
            metadata = {
                "url": url,
                "downloaded_at": datetime.now(timezone.utc).isoformat(),
                "description": f"{site_name} documentation for testing",
            }

            with open(dir_name / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)

            return True
        else:
            print(f"❌ Failed to download {site_name}: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"❌ Download timeout for {site_name}")
        return False
    except Exception as e:
        print(f"❌ Error downloading {site_name}: {e}")
        return False


def create_simple_site():
    """簡単なテストサイトを作成"""
    simple_site_dir = FIXTURE_DIR / "simple-site"

    if simple_site_dir.exists():
        print("⚠️  simple-site already exists. Skipping creation.")
        print(f"   To re-create, remove: {simple_site_dir}")
        return

    simple_site_dir.mkdir(parents=True, exist_ok=True)

    # index.html
    (simple_site_dir / "index.html").write_text("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test Site</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <nav class="navigation">
        <ul>
            <li><a href="index.html">Home</a></li>
            <li><a href="about.html">About</a></li>
            <li><a href="docs/guide.html">Guide</a></li>
        </ul>
    </nav>
    <main class="content">
        <h1>Welcome to Test Site</h1>
        <p>This is a simple test site for site2 testing.</p>
    </main>
</body>
</html>""")

    # about.html
    (simple_site_dir / "about.html").write_text("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>About - Test Site</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <nav class="navigation">
        <ul>
            <li><a href="index.html">Home</a></li>
            <li><a href="about.html">About</a></li>
            <li><a href="docs/guide.html">Guide</a></li>
        </ul>
    </nav>
    <main class="content">
        <h1>About This Site</h1>
        <p>This is the about page.</p>
    </main>
</body>
</html>""")

    # docs/guide.html
    docs_dir = simple_site_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    (docs_dir / "guide.html").write_text("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Guide - Test Site</title>
    <link rel="stylesheet" href="../style.css">
</head>
<body>
    <nav class="navigation">
        <ul>
            <li><a href="../index.html">Home</a></li>
            <li><a href="../about.html">About</a></li>
            <li><a href="guide.html">Guide</a></li>
        </ul>
    </nav>
    <main class="content">
        <h1>User Guide</h1>
        <p>This is the guide page.</p>
    </main>
</body>
</html>""")

    # style.css
    (simple_site_dir / "style.css").write_text("""body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
}

.navigation {
    background-color: #333;
    color: white;
    padding: 1rem;
}

.navigation ul {
    list-style: none;
    margin: 0;
    padding: 0;
}

.navigation li {
    display: inline-block;
    margin-right: 1rem;
}

.navigation a {
    color: white;
    text-decoration: none;
}

.content {
    padding: 2rem;
}""")

    print("✅ simple-site created successfully")


def show_fixtures():
    """利用可能なフィクスチャを表示"""
    print("📁 Available test fixtures:")
    if not FIXTURE_DIR.exists():
        print("   No fixtures found")
        return

    for dir_path in FIXTURE_DIR.iterdir():
        if dir_path.is_dir():
            dir_name = dir_path.name
            metadata_file = dir_path / "metadata.json"

            if metadata_file.exists():
                try:
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                    url = metadata.get("url", "unknown")
                    downloaded_at = metadata.get("downloaded_at", "unknown")
                    print(f"   📄 {dir_name} ({url}) - {downloaded_at}")
                except Exception:
                    print(f"   📄 {dir_name} (metadata error)")
            else:
                print(f"   📄 {dir_name} (local test site)")


def main():
    """メイン処理"""
    print("📦 Preparing test fixtures...")

    # ディレクトリ作成
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    # 各サイトをダウンロード
    for site_name, url in DOWNLOAD_URLS.items():
        download_docs(site_name, url)

    # 簡単なテストサイトを作成
    create_simple_site()

    # 結果を表示
    show_fixtures()

    print("✅ Test fixtures prepared successfully!")


if __name__ == "__main__":
    main()
