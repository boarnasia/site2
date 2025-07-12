"""
テスト用の静的ファイルWebサーバー
wgetで取得したファイルを提供する
"""

import http.server
import socketserver
import threading
import time
from pathlib import Path
import pytest
from urllib.parse import unquote


class StaticFileHandler(http.server.SimpleHTTPRequestHandler):
    """静的ファイルを提供するハンドラー"""

    def __init__(self, *args, **kwargs):
        # ベースディレクトリを設定
        self.base_dir = kwargs.pop("directory", ".")
        super().__init__(*args, directory=self.base_dir, **kwargs)

    def translate_path(self, path):
        """URLパスをファイルパスに変換"""
        # パスをデコード
        path = unquote(path)

        # セキュリティ: 親ディレクトリへのアクセスを防ぐ
        path = path.replace("../", "")

        # 先頭のスラッシュを除去
        if path.startswith("/"):
            path = path[1:]

        # index.htmlへのマッピング
        file_path = Path(self.base_dir) / path
        if file_path.is_dir():
            # ディレクトリの場合はindex.htmlを探す
            index_path = file_path / "index.html"
            if index_path.exists():
                return str(index_path)

        return str(file_path)

    def end_headers(self):
        """CORSヘッダーを追加"""
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, format, *args):
        """ログ出力を抑制（テスト時のノイズを減らす）"""
        pass


class TestWebServer:
    """テスト用Webサーバー"""

    def __init__(self, root_dir: Path, port: int = 0):
        """
        Args:
            root_dir: 静的ファイルのルートディレクトリ
            port: ポート番号（0の場合は自動割り当て）
        """
        self.root_dir = Path(root_dir)
        self.port = port
        self.server = None
        self.thread = None
        self.url = None

    def start(self):
        """サーバーを起動"""

        def handler(*args, **kwargs):
            """ハンドラーのラッパー"""
            return StaticFileHandler(*args, directory=str(self.root_dir), **kwargs)

        # ポート0で作成すると、空いているポートが自動的に割り当てられる
        self.server = socketserver.TCPServer(("localhost", self.port), handler)

        # 実際のポート番号を取得
        self.port = self.server.server_address[1]
        self.url = f"http://localhost:{self.port}"

        # 別スレッドでサーバーを起動
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

        # サーバーが起動するまで待機
        time.sleep(0.1)

        return self.url

    def stop(self):
        """サーバーを停止"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=1.0)


@pytest.fixture
def static_web_server():
    """静的Webサーバーのフィクスチャ"""
    servers = []

    def _create_server(root_dir: Path, port: int = 0) -> TestWebServer:
        """サーバーを作成して起動"""
        server = TestWebServer(root_dir, port)
        server.start()
        servers.append(server)
        return server

    yield _create_server

    # クリーンアップ
    for server in servers:
        server.stop()


@pytest.fixture
def pytest_bdd_docs_server(static_web_server):
    """pytest-bddドキュメントサイトのサーバー"""
    # fixtureディレクトリのパス
    fixture_dir = Path(__file__).parent / "websites" / "pytest-bdd-docs"

    if not fixture_dir.exists():
        pytest.skip(f"Fixture directory not found: {fixture_dir}")

    # サーバーを起動
    server = static_web_server(fixture_dir)
    return server


# 使用例
def test_example_with_static_server(pytest_bdd_docs_server):
    """静的サーバーを使ったテスト例"""
    base_url = pytest_bdd_docs_server.url
    print(f"Test server running at: {base_url}")

    # ここでwgetやfetchコマンドをテスト
    # 例: site2 fetch {base_url}
