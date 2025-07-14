"""
WgetCrawlerの単体テスト
"""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime

from site2.adapters.crawlers.wget_crawler import WgetCrawler
from site2.core.domain.fetch_domain import (
    WebsiteURL,
    CrawlDepth,
    WebsiteCache,
    CachedPage,
)
from site2.core.ports.fetch_contracts import NetworkError


class TestWgetCrawler:
    """WgetCrawlerのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される"""
        self.crawler = WgetCrawler()
        self.test_url = WebsiteURL(value="https://example.com/")
        self.test_depth = CrawlDepth(value=2)
        self.cache_dir = Path("/tmp/test_cache/example.com_abc123")

    @patch("subprocess.run")
    @patch("pathlib.Path.glob")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.mkdir")
    def test_crawl_success(self, mock_mkdir, mock_exists, mock_glob, mock_run):
        """正常なクロールが成功すること"""
        # Arrange
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # globで見つかるファイルをモック
        mock_html_files = [
            MagicMock(
                spec=Path,
                __str__=lambda self: f"{self.cache_dir}/index.html",
                relative_to=lambda x: Path("index.html"),
                stat=lambda: MagicMock(st_size=1024),
            ),
            MagicMock(
                spec=Path,
                __str__=lambda self: f"{self.cache_dir}/about.html",
                relative_to=lambda x: Path("about.html"),
                stat=lambda: MagicMock(st_size=2048),
            ),
        ]
        # .htmlと.htmで異なる結果を返す
        mock_glob.side_effect = [mock_html_files, []]  # .html files, then no .htm files

        # Act
        result = self.crawler.crawl(self.test_url, self.test_depth)

        # Assert
        assert len(result) == 2
        assert all(isinstance(page, CachedPage) for page in result)
        assert result[0].size_bytes == 1024
        assert result[1].size_bytes == 2048

        # wgetコマンドが正しく呼ばれたことを確認
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "wget" in args
        assert "-r" in args  # 再帰的
        assert "-l" in args  # 深さ制限
        assert str(self.test_depth.value) in args
        assert str(self.test_url.value) in args

    @patch("subprocess.run")
    def test_crawl_with_depth_parameter(self, mock_run):
        """深度パラメータが正しく設定されること"""
        # Arrange
        mock_run.return_value = MagicMock(returncode=0)
        custom_depth = CrawlDepth(value=5)

        # Act
        with patch("pathlib.Path.glob", return_value=[]):
            self.crawler.crawl(self.test_url, custom_depth)

        # Assert
        args = mock_run.call_args[0][0]
        assert "-l" in args
        depth_index = args.index("-l") + 1
        assert args[depth_index] == "5"

    @patch("subprocess.run")
    def test_crawl_network_error(self, mock_run):
        """ネットワークエラーが適切に処理されること"""
        # Arrange
        mock_run.return_value = MagicMock(returncode=1, stderr="Network unreachable")

        # Act & Assert
        with pytest.raises(NetworkError, match="Wget failed"):
            self.crawler.crawl(self.test_url, self.test_depth)

    @patch("subprocess.run")
    def test_crawl_timeout(self, mock_run):
        """タイムアウトが適切に処理されること"""
        # Arrange
        mock_run.side_effect = subprocess.TimeoutExpired("wget", 300)

        # Act & Assert
        with pytest.raises(NetworkError, match="Wget timeout"):
            self.crawler.crawl(self.test_url, self.test_depth)

    @patch("subprocess.run")
    @patch("pathlib.Path.glob")
    @patch("pathlib.Path.exists")
    def test_crawl_with_existing_cache(self, mock_exists, mock_glob, mock_run):
        """既存キャッシュがある場合の差分更新"""
        # Arrange
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        # 既存のキャッシュ
        existing_page = CachedPage(
            page_url=self.test_url,
            local_path=Path("/tmp/old_cache/index.html"),
            content_type="text/html",
            size_bytes=512,
            fetched_at=datetime.now(),
        )
        existing_cache = WebsiteCache(
            root_url=self.test_url,
            cache_directory=Path("/tmp/old_cache"),
            pages=[existing_page],
            created_at=datetime.now(),
        )

        mock_glob.return_value = [
            MagicMock(
                spec=Path,
                relative_to=lambda x: Path("index.html"),
                stat=lambda: MagicMock(st_size=1024),
            )
        ]

        # Act
        result = self.crawler.crawl(self.test_url, self.test_depth, existing_cache)

        # Assert
        assert len(result) > 0
        # wgetに--timestampingオプションが含まれることを確認
        args = mock_run.call_args[0][0]
        assert "-N" in args or "--timestamping" in args

    @patch("subprocess.run")
    @patch("pathlib.Path.glob")
    def test_crawl_creates_cached_pages_with_read_text(self, mock_glob, mock_run):
        """CachedPageにread_text()メソッドが実装されていること"""
        # Arrange
        mock_run.return_value = MagicMock(returncode=0)

        # テスト用のHTMLファイル
        test_html_content = "<html><body>Test Content</body></html>"
        mock_file = MagicMock(spec=Path)
        mock_file.relative_to.return_value = Path("test.html")
        mock_file.stat.return_value = MagicMock(st_size=len(test_html_content))
        mock_file.read_text.return_value = test_html_content

        # .htmlと.htmで異なる結果を返す
        mock_glob.side_effect = [[mock_file], []]  # .html files, then no .htm files

        # Act
        result = self.crawler.crawl(self.test_url, self.test_depth)

        # Assert
        assert len(result) == 1
        page = result[0]
        assert hasattr(page, "read_text")
        # read_textメソッドが呼び出し可能であることを確認
        assert callable(getattr(page, "read_text", None))

    @patch("subprocess.run")
    def test_crawl_wget_options(self, mock_run):
        """wgetオプションが正しく設定されること"""
        # Arrange
        mock_run.return_value = MagicMock(returncode=0)

        # Act
        with patch("pathlib.Path.glob", return_value=[]):
            self.crawler.crawl(self.test_url, self.test_depth)

        # Assert
        args = mock_run.call_args[0][0]

        # 必須オプションの確認
        assert "-r" in args or "--recursive" in args  # 再帰的
        assert "-l" in args or "--level=" in args[0]  # 深さ制限
        assert "-k" in args or "--convert-links" in args  # リンク変換
        assert "-E" in args or "--adjust-extension" in args  # 拡張子調整
        assert "-np" in args or "--no-parent" in args  # 親ディレクトリを辿らない
        assert "-H" in args  # ホストをまたぐダウンロードを許可
        assert "-D" in args  # ドメイン制限
        # ドメイン制限が正しく設定されていることを確認
        domain_index = args.index("-D") + 1
        assert args[domain_index] == "example.com"

    @patch("subprocess.run")
    @patch("pathlib.Path.glob")
    def test_crawl_empty_result(self, mock_glob, mock_run):
        """ページが取得できなかった場合の処理"""
        # Arrange
        mock_run.return_value = MagicMock(returncode=0)
        mock_glob.return_value = []  # ファイルが見つからない

        # Act
        result = self.crawler.crawl(self.test_url, self.test_depth)

        # Assert
        assert result == []

    @patch("subprocess.run")
    def test_crawl_directory_creation(self, mock_run):
        """出力ディレクトリが作成されること"""
        # Arrange
        mock_run.return_value = MagicMock(returncode=0)

        # tempfile.mkdtempをモック
        with patch("tempfile.mkdtemp") as mock_mkdtemp:
            mock_mkdtemp.return_value = "/tmp/test_dir"
            with patch("pathlib.Path.glob", side_effect=[[], []]):  # .html and .htm
                # Act
                self.crawler.crawl(self.test_url, self.test_depth)

                # Assert
                # 一時ディレクトリ作成が呼ばれたことを確認
                mock_mkdtemp.assert_called_once()

    @patch("subprocess.run")
    def test_domain_restriction(self, mock_run):
        """異なるドメインのURLでドメイン制限が正しく設定されること"""
        # Arrange
        mock_run.return_value = MagicMock(returncode=0)

        # 異なるドメインでテスト
        test_urls = [
            WebsiteURL(value="https://example.com/page"),
            WebsiteURL(value="https://subdomain.example.com/"),
            WebsiteURL(value="https://another-site.org/"),
        ]

        with patch("pathlib.Path.glob", return_value=[]):
            for test_url in test_urls:
                # Act
                self.crawler.crawl(test_url, self.test_depth)

                # Assert
                args = mock_run.call_args[0][0]
                domain_index = args.index("-D") + 1
                # 各URLの正しいドメインが設定されていることを確認
                assert args[domain_index] == test_url.domain

    def test_parse_content_type(self):
        """Content-Typeの判定が正しく動作すること"""
        # HTMLファイル
        assert self.crawler._get_content_type(Path("index.html")) == "text/html"
        assert self.crawler._get_content_type(Path("page.htm")) == "text/html"

        # CSSファイル
        assert self.crawler._get_content_type(Path("style.css")) == "text/css"

        # JavaScriptファイル
        assert (
            self.crawler._get_content_type(Path("script.js"))
            == "application/javascript"
        )

        # 画像ファイル
        assert self.crawler._get_content_type(Path("image.png")) == "image/png"
        assert self.crawler._get_content_type(Path("photo.jpg")) == "image/jpeg"

        # その他
        assert (
            self.crawler._get_content_type(Path("unknown.xyz"))
            == "application/octet-stream"
        )
