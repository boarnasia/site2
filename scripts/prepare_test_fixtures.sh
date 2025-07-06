#!/bin/bash
# テスト用のWebサイトデータを準備するスクリプト

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FIXTURE_DIR="$PROJECT_ROOT/tests/fixtures/websites"

echo "📦 Preparing test fixtures..."

# ディレクトリ作成
mkdir -p "$FIXTURE_DIR"

# pytest-bddドキュメントをダウンロード
PYTEST_BDD_DIR="$FIXTURE_DIR/pytest-bdd-docs"

if [ -d "$PYTEST_BDD_DIR" ]; then
    echo "⚠️  pytest-bdd docs already exist. Skipping download."
    echo "   To re-download, remove: $PYTEST_BDD_DIR"
else
    echo "📥 Downloading pytest-bdd documentation..."

    # wgetで再帰的にダウンロード
    # オプション説明:
    # -r: 再帰的ダウンロード
    # -l 2: 深さ2まで
    # -np: 親ディレクトリを辿らない
    # -k: リンクをローカル用に変換
    # -E: 適切な拡張子を付ける
    # -H: 外部ホストも許可（CDNなど）
    # -D: ドメインリスト
    # -P: 保存先ディレクトリ
    # --convert-links: ダウンロード後にリンクを変換

    wget -r -l 2 -np -k -E \
        -H -Dpytest-bdd.readthedocs.io,readthedocs.org \
        --convert-links \
        --adjust-extension \
        --page-requisites \
        --no-parent \
        --wait=0.5 \
        --random-wait \
        -P "$PYTEST_BDD_DIR" \
        "https://pytest-bdd.readthedocs.io/en/stable/"

    # ディレクトリ構造を整理
    if [ -d "$FIXTURE_DIR/pytest-bdd-docs/pytest-bdd.readthedocs.io" ]; then
        mv "$FIXTURE_DIR/pytest-bdd-docs/pytest-bdd.readthedocs.io/en/stable/"* "$FIXTURE_DIR/pytest-bdd-docs/" 2>/dev/null || true
        rm -rf "$FIXTURE_DIR/pytest-bdd-docs/pytest-bdd.readthedocs.io"
    fi

    echo "✅ pytest-bdd docs downloaded successfully"
fi

# メタデータファイルを作成
cat > "$PYTEST_BDD_DIR/metadata.json" << EOF
{
    "url": "https://pytest-bdd.readthedocs.io/en/stable/",
    "downloaded_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "description": "pytest-bdd documentation for testing"
}
EOF

# 簡単なテストサイトも作成
SIMPLE_SITE_DIR="$FIXTURE_DIR/simple-site"
mkdir -p "$SIMPLE_SITE_DIR"

# index.html
cat > "$SIMPLE_SITE_DIR/index.html" << 'EOF'
<!DOCTYPE html>
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
</html>
EOF

# about.html
cat > "$SIMPLE_SITE_DIR/about.html" << 'EOF'
<!DOCTYPE html>
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
</html>
EOF

# docs/guide.html
mkdir -p "$SIMPLE_SITE_DIR/docs"
cat > "$SIMPLE_SITE_DIR/docs/guide.html" << 'EOF'
<!DOCTYPE html>
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
</html>
EOF

# style.css
cat > "$SIMPLE_SITE_DIR/style.css" << 'EOF'
body {
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
}
EOF

echo "📁 Created fixture structure:"
echo "   $FIXTURE_DIR/"
echo "   ├── pytest-bdd-docs/"
echo "   │   ├── index.html"
echo "   │   ├── ..."
echo "   │   └── metadata.json"
echo "   └── simple-site/"
echo "       ├── index.html"
echo "       ├── about.html"
echo "       ├── style.css"
echo "       └── docs/"
echo "           └── guide.html"

echo "✅ Test fixtures prepared successfully!"
