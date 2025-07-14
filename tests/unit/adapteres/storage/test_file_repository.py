"""
FileRepositoryの単体テスト
"""

import json
from unittest.mock import patch, MagicMock
from pathlib import Path

from site2.adapters.storage.file_repository import FileRepository
from site2.core.domain.fetch_domain import WebsiteURL, WebsiteCache


class TestFileRepository:
    """FileRepositoryのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される"""
        self.cache_dir = Path("/tmp/test_cache")
        self.repository = FileRepository(cache_dir=self.cache_dir)

    @patch("pathlib.Path.iterdir")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.exists")
    def test_find_all_success(self, mock_exists, mock_is_dir, mock_iterdir):
        """すべてのキャッシュを正常に取得できること"""
        # Arrange
        mock_exists.return_value = True

        # キャッシュディレクトリのモック
        cache_dir1 = MagicMock(spec=Path)
        cache_dir1.name = "example.com_abc123"
        cache_dir1.is_dir.return_value = True
        cache_dir1.__truediv__ = lambda self, x: Path(
            f"/tmp/test_cache/example.com_abc123/{x}"
        )

        cache_dir2 = MagicMock(spec=Path)
        cache_dir2.name = "test.org_def456"
        cache_dir2.is_dir.return_value = True
        cache_dir2.__truediv__ = lambda self, x: Path(
            f"/tmp/test_cache/test.org_def456/{x}"
        )

        mock_iterdir.return_value = [cache_dir1, cache_dir2]
        mock_is_dir.return_value = True

        # cache.jsonの内容
        cache_json1 = {
            "root_url": "https://example.com/",
            "created_at": "2024-01-01T00:00:00",
            "pages": [
                {
                    "url": "https://example.com/",
                    "local_path": "index.html",
                    "content_type": "text/html",
                    "size_bytes": 1024,
                    "fetched_at": "2024-01-01T00:00:00",
                }
            ],
        }

        cache_json2 = {
            "root_url": "https://test.org/",
            "created_at": "2024-01-02T00:00:00",
            "pages": [
                {
                    "url": "https://test.org/",
                    "local_path": "index.html",
                    "content_type": "text/html",
                    "size_bytes": 2048,
                    "fetched_at": "2024-01-02T00:00:00",
                }
            ],
        }

        with patch("builtins.open", create=True) as mock_open:
            # ファイルハンドルのモック
            mock_file1 = MagicMock()
            mock_file1.__enter__.return_value.read.return_value = json.dumps(
                cache_json1
            )

            mock_file2 = MagicMock()
            mock_file2.__enter__.return_value.read.return_value = json.dumps(
                cache_json2
            )

            # 各cache.jsonファイルの読み込みをモック
            mock_open.side_effect = [mock_file1, mock_file2]

            # cache.jsonの存在確認をモック
            with patch("pathlib.Path.exists", return_value=True):
                # Act
                result = self.repository.find_all()

        # Assert
        assert len(result) == 2
        assert all(isinstance(cache, WebsiteCache) for cache in result)
        assert str(result[0].root_url.value) == "https://example.com/"
        assert str(result[1].root_url.value) == "https://test.org/"

    @patch("pathlib.Path.iterdir")
    @patch("pathlib.Path.exists")
    def test_find_all_empty_directory(self, mock_exists, mock_iterdir):
        """キャッシュがない場合は空のリストを返すこと"""
        # Arrange
        mock_exists.return_value = True
        mock_iterdir.return_value = []

        # Act
        result = self.repository.find_all()

        # Assert
        assert result == []

    @patch("pathlib.Path.exists")
    def test_find_all_directory_not_exists(self, mock_exists):
        """キャッシュディレクトリが存在しない場合は空のリストを返すこと"""
        # Arrange
        mock_exists.return_value = False

        # Act
        result = self.repository.find_all()

        # Assert
        assert result == []

    @patch("pathlib.Path.iterdir")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.exists")
    def test_find_by_url_success(self, mock_exists, mock_is_dir, mock_iterdir):
        """URLでキャッシュを正常に検索できること"""
        # Arrange
        test_url = WebsiteURL(value="https://example.com/")
        mock_exists.return_value = True

        # キャッシュディレクトリのモック
        cache_dir = MagicMock(spec=Path)
        cache_dir.name = "example.com_abc123"
        cache_dir.is_dir.return_value = True
        cache_dir.__truediv__ = lambda self, x: Path(
            f"/tmp/test_cache/example.com_abc123/{x}"
        )

        mock_iterdir.return_value = [cache_dir]
        mock_is_dir.return_value = True

        cache_json = {
            "root_url": "https://example.com/",
            "created_at": "2024-01-01T00:00:00",
            "pages": [
                {
                    "url": "https://example.com/",
                    "local_path": "index.html",
                    "content_type": "text/html",
                    "size_bytes": 1024,
                    "fetched_at": "2024-01-01T00:00:00",
                }
            ],
        }

        with patch("builtins.open", create=True) as mock_open:
            # ファイルハンドルのモック
            mock_file = MagicMock()
            mock_file.__enter__.return_value.read.return_value = json.dumps(cache_json)
            mock_open.return_value = mock_file

            # cache.jsonの存在確認をモック
            with patch("pathlib.Path.exists", return_value=True):
                # Act
                result = self.repository.find_by_url(test_url)

        # Assert
        assert result is not None
        assert isinstance(result, WebsiteCache)
        assert str(result.root_url.value) == "https://example.com/"

    def test_find_by_url_not_found(self):
        """存在しないURLの場合はNoneを返すこと"""
        # Arrange
        test_url = WebsiteURL(value="https://notfound.com/")

        with patch("pathlib.Path.iterdir", return_value=[]):
            with patch("pathlib.Path.exists", return_value=True):
                # Act
                result = self.repository.find_by_url(test_url)

        # Assert
        assert result is None

    @patch("pathlib.Path.exists")
    @patch("builtins.open", create=True)
    def test_load_cache_with_cached_page_read_text(self, mock_open, mock_exists):
        """CachedPageがread_textメソッドを持つこと"""
        # Arrange
        mock_exists.return_value = True

        cache_json = {
            "root_url": "https://example.com/",
            "created_at": "2024-01-01T00:00:00",
            "pages": [
                {
                    "url": "https://example.com/",
                    "local_path": "index.html",
                    "content_type": "text/html",
                    "size_bytes": 1024,
                    "fetched_at": "2024-01-01T00:00:00",
                }
            ],
        }

        # ファイルハンドルのモック
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = json.dumps(cache_json)
        mock_open.return_value = mock_file

        # HTMLファイルの内容
        html_content = "<html><body>Test</body></html>"

        with patch("pathlib.Path.read_text", return_value=html_content):
            # Act
            cache = self.repository._load_cache_from_directory(
                Path("/tmp/test_cache/example.com_abc123")
            )

        # Assert
        assert cache is not None
        assert len(cache.pages) == 1
        page = cache.pages[0]
        assert hasattr(page, "read_text")
        assert callable(getattr(page, "read_text", None))

    @patch("pathlib.Path.exists")
    @patch("builtins.open", side_effect=IOError("Permission denied"))
    def test_load_cache_permission_error(self, mock_open, mock_exists):
        """cache.jsonの読み込み権限がない場合はNoneを返すこと"""
        # Arrange
        mock_exists.return_value = True

        # Act
        cache = self.repository._load_cache_from_directory(
            Path("/tmp/test_cache/example.com_abc123")
        )

        # Assert
        assert cache is None

    @patch("pathlib.Path.exists")
    @patch("builtins.open", create=True)
    def test_load_cache_invalid_json(self, mock_open, mock_exists):
        """無効なJSONの場合はNoneを返すこと"""
        # Arrange
        mock_exists.return_value = True
        mock_open.return_value.read.return_value = "invalid json"

        # Act
        cache = self.repository._load_cache_from_directory(
            Path("/tmp/test_cache/example.com_abc123")
        )

        # Assert
        assert cache is None

    @patch("pathlib.Path.exists")
    @patch("builtins.open", create=True)
    def test_load_cache_missing_required_fields(self, mock_open, mock_exists):
        """必須フィールドが欠けている場合はNoneを返すこと"""
        # Arrange
        mock_exists.return_value = True

        # root_urlが欠けているJSON
        cache_json = {"created_at": "2024-01-01T00:00:00", "pages": []}

        mock_open.return_value.read.return_value = json.dumps(cache_json)

        # Act
        cache = self.repository._load_cache_from_directory(
            Path("/tmp/test_cache/example.com_abc123")
        )

        # Assert
        assert cache is None

    def test_cache_directory_filtering(self):
        """有効なキャッシュディレクトリのみを処理すること"""
        # Arrange
        with patch("pathlib.Path.iterdir") as mock_iterdir:
            with patch("pathlib.Path.exists", return_value=True):
                # 様々なファイル/ディレクトリ
                file_path = MagicMock(spec=Path)
                file_path.is_dir.return_value = False

                valid_dir = MagicMock(spec=Path)
                valid_dir.name = "example.com_abc123"
                valid_dir.is_dir.return_value = True

                hidden_dir = MagicMock(spec=Path)
                hidden_dir.name = ".hidden"
                hidden_dir.is_dir.return_value = True

                mock_iterdir.return_value = [file_path, valid_dir, hidden_dir]

                # Act
                with patch.object(
                    self.repository, "_load_cache_from_directory", return_value=None
                ) as mock_load:
                    result = self.repository.find_all()  # noqa: F841

                # Assert
                # _load_cache_from_directoryが有効なディレクトリに対してのみ呼ばれることを確認
                assert mock_load.call_count == 1
