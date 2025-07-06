"""
ローカルWebサーバーを使ったFetch機能のテスト
"""

import pytest
from pytest_bdd import scenario, given, when, then, parsers
from pathlib import Path
from typer.testing import CliRunner
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from site2.cli import app

# fixtures/test_server.pyからインポート


@scenario("fetch_with_server.feature", "ローカルサーバーからのフェッチ")
def test_fetch_from_local_server():
    """ローカルサーバーからのフェッチテスト"""
    pass


@scenario("fetch_with_server.feature", "深さ制限付きフェッチ")
def test_fetch_with_depth_limit():
    """深さ制限付きフェッチテスト"""
    pass


# Fixtures
@pytest.fixture
def runner():
    """CLIランナー"""
    return CliRunner()


@pytest.fixture
def cache_dir(tmp_path):
    """テスト用キャッシュディレクトリ"""
    cache_dir = tmp_path / ".cache" / "site2"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


@pytest.fixture
def simple_site_server(static_web_server):
    """シンプルなテストサイトのサーバー"""
    fixture_dir = Path(__file__).parent.parent / "fixtures" / "websites" / "simple-site"

    if not fixture_dir.exists():
        # fixtureがない場合は作成をスキップ
        pytest.skip("Run 'scripts/prepare_test_fixtures.sh' first")

    server = static_web_server(fixture_dir)
    return server


@pytest.fixture
def context():
    """ステップ間で状態を共有"""
    return {"server": None, "result": None, "cache_dir": None}


# Given steps
@given("ローカルWebサーバーが起動している")
def local_server_running(context, simple_site_server):
    """ローカルサーバーを起動"""
    context["server"] = simple_site_server
    context["base_url"] = simple_site_server.url
    print(f"Test server running at: {context['base_url']}")


@given("キャッシュディレクトリが空である")
def empty_cache_dir(context, cache_dir):
    """キャッシュディレクトリを空にする"""
    context["cache_dir"] = cache_dir
    # 既存のファイルを削除
    for item in cache_dir.iterdir():
        if item.is_dir():
            import shutil

            shutil.rmtree(item)
        else:
            item.unlink()


# When steps
@when("ローカルサーバーのURLをフェッチする")
def fetch_local_server(context, runner):
    """ローカルサーバーからフェッチ"""
    url = context["base_url"]

    # 環境変数でキャッシュディレクトリを指定
    import os

    env = os.environ.copy()
    env["SITE2_CACHE_DIR"] = str(context["cache_dir"])

    # fetchコマンドを実行
    result = runner.invoke(app, ["fetch", url], env=env)
    context["result"] = result

    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.stdout}")
    if result.stderr:
        print(f"Error: {result.stderr}")


@when(parsers.parse("深さ {depth:d} でローカルサーバーをフェッチする"))
def fetch_with_depth(context, runner, depth):
    """深さ制限付きでフェッチ"""
    url = context["base_url"]

    import os

    env = os.environ.copy()
    env["SITE2_CACHE_DIR"] = str(context["cache_dir"])

    # --depth オプション付きでfetch
    result = runner.invoke(app, ["fetch", url, "--depth", str(depth)], env=env)
    context["result"] = result


# Then steps
@then("フェッチが成功する")
def fetch_succeeds(context):
    """フェッチの成功を確認"""
    assert context["result"].exit_code == 0
    assert (
        "Fetched" in context["result"].stdout or "fetched" in context["result"].stdout
    )


@then(parsers.parse("{count:d} ページがキャッシュされる"))
def pages_cached(context, count):
    """キャッシュされたページ数を確認"""
    # キャッシュディレクトリ内のHTMLファイルを数える
    cache_dir = context["cache_dir"]
    html_files = list(cache_dir.rglob("*.html"))

    assert len(html_files) == count, (
        f"Expected {count} pages, but found {len(html_files)}"
    )


@then("以下のファイルがキャッシュされる:")
def files_are_cached(context, datatable):
    """特定のファイルがキャッシュされていることを確認"""
    cache_dir = context["cache_dir"]

    for row in datatable:
        file_path = row["file"]
        # キャッシュ内でファイルを探す
        found = False
        for cached_file in cache_dir.rglob("*"):
            if cached_file.name == file_path:
                found = True
                break

        assert found, f"File {file_path} not found in cache"


@then("ルートページのみがキャッシュされる")
def only_root_cached(context):
    """ルートページのみがキャッシュされていることを確認"""
    cache_dir = context["cache_dir"]
    html_files = list(cache_dir.rglob("*.html"))

    # index.htmlのみが存在することを確認
    assert len(html_files) == 1
    assert html_files[0].name == "index.html"
