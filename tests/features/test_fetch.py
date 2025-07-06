"""
Fetch機能のBDDテスト実装（pytest-bdd）
"""

import pytest
from pytest_bdd import scenario, given, when, then, parsers
from typer.testing import CliRunner
from unittest.mock import Mock, patch
import json
from datetime import datetime, timedelta

from site2.cli import app
from site2.core.domain.fetch_domain import WebsiteURL


# シナリオのバインディング
@scenario("fetch.feature", "新規サイトのフェッチ")
def test_fetch_new_site():
    """新規サイトのフェッチシナリオ"""
    pass


@scenario("fetch.feature", "キャッシュ済みサイトの差分更新")
def test_fetch_cached_site():
    """キャッシュ済みサイトの差分更新シナリオ"""
    pass


@scenario("fetch.feature", "キャッシュ一覧の表示")
def test_list_caches():
    """キャッシュ一覧表示シナリオ"""
    pass


@scenario("fetch.feature", "無効なURLのエラー処理")
def test_invalid_url_error():
    """無効なURLエラー処理シナリオ"""
    pass


# フィクスチャ
@pytest.fixture
def runner():
    """CLIテストランナー"""
    return CliRunner()


@pytest.fixture
def cache_dir(tmp_path):
    """テスト用キャッシュディレクトリ"""
    cache_dir = tmp_path / ".cache" / "site2"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


@pytest.fixture
def context():
    """ステップ間で状態を共有するコンテキスト"""
    return {"result": None, "cache_dir": None, "mock_fetch_service": None}


# Given ステップ
@given("キャッシュディレクトリが存在する")
def cache_directory_exists(context, cache_dir):
    """キャッシュディレクトリをセットアップ"""
    context["cache_dir"] = cache_dir
    assert cache_dir.exists()


@given("ネットワーク接続が利用可能である")
def network_is_available(context):
    """ネットワーク接続のモック準備"""
    # 実際の実装では、fetchサービスをモックする
    mock_service = Mock()
    context["mock_fetch_service"] = mock_service


@given(parsers.parse('"{url}" はまだキャッシュされていない'))
def url_not_cached(context, url):
    """URLがキャッシュされていないことを確認"""
    cache_path = context["cache_dir"] / WebsiteURL(url).slug
    assert not cache_path.exists()


@given(parsers.parse('"{url}" は{hours:d}時間前にキャッシュされている'))
def url_cached_hours_ago(context, url, hours):
    """指定時間前にキャッシュされた状態を作成"""
    website_url = WebsiteURL(url)
    cache_path = context["cache_dir"] / website_url.slug
    cache_path.mkdir(parents=True, exist_ok=True)

    # メタデータファイルを作成
    metadata = {
        "url": url,
        "cached_at": (datetime.now() - timedelta(hours=hours)).isoformat(),
        "pages": 10,
        "total_size": 1024000,
    }
    (cache_path / "metadata.json").write_text(json.dumps(metadata))


@given("以下のサイトがキャッシュされている:")
def sites_are_cached(context, table):
    """テーブルデータからキャッシュを作成"""
    for row in table:
        url = row["url"]
        website_url = WebsiteURL(url)
        cache_path = context["cache_dir"] / website_url.slug
        cache_path.mkdir(parents=True, exist_ok=True)

        metadata = {
            "url": url,
            "pages": int(row["pages"]),
            "size": row["size"],
            "last_updated": row["last_updated"],
        }
        (cache_path / "metadata.json").write_text(json.dumps(metadata))


# When ステップ
@when(parsers.parse('コマンド "{command}" を実行する'))
def execute_command(context, runner, command):
    """CLIコマンドを実行"""
    args = command.split()[1:]  # "site2" を除く

    # 環境変数でキャッシュディレクトリを指定
    with patch.dict("os.environ", {"SITE2_CACHE_DIR": str(context["cache_dir"])}):
        # 実際の実装では、FetchServiceをモックする
        with patch("site2.cli.fetch_service", context.get("mock_fetch_service")):
            result = runner.invoke(app, args)

    context["result"] = result


# Then ステップ
@then(parsers.parse("終了コード {code:d} で正常終了する"))
def check_exit_code_success(context, code):
    """終了コードを確認"""
    assert context["result"].exit_code == code


@then(parsers.parse("終了コード {code:d} でエラー終了する"))
def check_exit_code_error(context, code):
    """エラー終了コードを確認"""
    assert context["result"].exit_code == code


@then("標準出力に以下を含む:")
def stdout_contains_text(context, text):
    """標準出力に指定テキストが含まれることを確認"""
    assert text.strip() in context["result"].stdout


@then(parsers.parse('標準出力に "{text}" を含む'))
def stdout_contains(context, text):
    """標準出力に指定文字列が含まれることを確認"""
    assert text in context["result"].stdout


@then(parsers.parse('標準エラー出力に "{text}" を含む'))
def stderr_contains(context, text):
    """標準エラー出力に指定文字列が含まれることを確認"""
    assert text in context["result"].stderr


@then("キャッシュディレクトリが作成される")
def cache_directory_created(context):
    """新しいキャッシュディレクトリが作成されたことを確認"""
    # 実際の実装では、新しく作成されたディレクトリを検証
    cache_dirs = list(context["cache_dir"].iterdir())
    assert len(cache_dirs) > 0
