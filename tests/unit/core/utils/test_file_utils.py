"""
ファイルユーティリティのテスト
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from datetime import datetime
import time

from site2.core.utils.file_utils import (
    ensure_directory,
    safe_write,
    safe_read,
    calculate_file_hash,
    copy_file_atomic,
    get_file_size,
    get_file_mtime,
    is_file_older_than,
    safe_json_write,
    safe_json_read,
    cleanup_old_files,
    create_backup,
)


class TestEnsureDirectory:
    """ensure_directory のテスト"""

    def test_create_new_directory(self):
        """新しいディレクトリの作成テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = Path(temp_dir) / "new_directory"
            result = ensure_directory(new_dir)

            assert new_dir.exists()
            assert new_dir.is_dir()
            assert result == new_dir

    def test_existing_directory(self):
        """既存ディレクトリの場合のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            existing_dir = Path(temp_dir)
            result = ensure_directory(existing_dir)

            assert existing_dir.exists()
            assert result == existing_dir

    def test_nested_directory_creation(self):
        """ネストしたディレクトリの作成テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_dir = Path(temp_dir) / "level1" / "level2" / "level3"
            result = ensure_directory(nested_dir)

            assert nested_dir.exists()
            assert nested_dir.is_dir()
            assert result == nested_dir


class TestSafeWrite:
    """safe_write のテスト"""

    def test_write_text_file(self):
        """テキストファイルの書き込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            content = "Hello, World!"

            safe_write(file_path, content)

            assert file_path.exists()
            assert file_path.read_text(encoding="utf-8") == content

    def test_write_binary_file(self):
        """バイナリファイルの書き込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.bin"
            content = b"Binary content"

            safe_write(file_path, content)

            assert file_path.exists()
            assert file_path.read_bytes() == content

    def test_create_parent_directory(self):
        """親ディレクトリの自動作成テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "subdir" / "test.txt"
            content = "Test content"

            safe_write(file_path, content)

            assert file_path.exists()
            assert file_path.parent.exists()
            assert file_path.read_text(encoding="utf-8") == content

    def test_overwrite_existing_file(self):
        """既存ファイルの上書きテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"

            # 初回書き込み
            safe_write(file_path, "Original content")
            assert file_path.read_text(encoding="utf-8") == "Original content"

            # 上書き
            safe_write(file_path, "New content")
            assert file_path.read_text(encoding="utf-8") == "New content"


class TestSafeRead:
    """safe_read のテスト"""

    def test_read_text_file(self):
        """テキストファイルの読み込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            content = "Hello, World!"
            file_path.write_text(content, encoding="utf-8")

            result = safe_read(file_path)
            assert result == content

    def test_read_binary_file(self):
        """バイナリファイルの読み込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.bin"
            content = b"Binary content"
            file_path.write_bytes(content)

            result = safe_read(file_path, binary=True)
            assert result == content

    def test_read_nonexistent_file(self):
        """存在しないファイルの読み込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nonexistent.txt"

            with pytest.raises(FileNotFoundError):
                safe_read(file_path)


class TestCalculateFileHash:
    """calculate_file_hash のテスト"""

    def test_md5_hash(self):
        """MD5ハッシュのテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            content = "Hello, World!"
            file_path.write_text(content, encoding="utf-8")

            hash_value = calculate_file_hash(file_path, "md5")
            assert len(hash_value) == 32  # MD5は32文字
            assert hash_value.isalnum()

    def test_sha256_hash(self):
        """SHA256ハッシュのテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            content = "Hello, World!"
            file_path.write_text(content, encoding="utf-8")

            hash_value = calculate_file_hash(file_path, "sha256")
            assert len(hash_value) == 64  # SHA256は64文字
            assert hash_value.isalnum()

    def test_consistent_hash(self):
        """一貫性のあるハッシュ値のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            content = "Hello, World!"
            file_path.write_text(content, encoding="utf-8")

            hash1 = calculate_file_hash(file_path)
            hash2 = calculate_file_hash(file_path)
            assert hash1 == hash2

    def test_different_content_different_hash(self):
        """異なる内容では異なるハッシュのテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "test1.txt"
            file2 = Path(temp_dir) / "test2.txt"

            file1.write_text("Content 1", encoding="utf-8")
            file2.write_text("Content 2", encoding="utf-8")

            hash1 = calculate_file_hash(file1)
            hash2 = calculate_file_hash(file2)
            assert hash1 != hash2


class TestCopyFileAtomic:
    """copy_file_atomic のテスト"""

    def test_copy_file(self):
        """ファイルのコピーテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_path = Path(temp_dir) / "source.txt"
            dst_path = Path(temp_dir) / "destination.txt"
            content = "Test content"

            src_path.write_text(content, encoding="utf-8")
            copy_file_atomic(src_path, dst_path)

            assert dst_path.exists()
            assert dst_path.read_text(encoding="utf-8") == content
            assert src_path.exists()  # 元ファイルは残る

    def test_copy_with_directory_creation(self):
        """ディレクトリ作成を伴うコピーテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_path = Path(temp_dir) / "source.txt"
            dst_path = Path(temp_dir) / "subdir" / "destination.txt"
            content = "Test content"

            src_path.write_text(content, encoding="utf-8")
            copy_file_atomic(src_path, dst_path)

            assert dst_path.exists()
            assert dst_path.parent.exists()
            assert dst_path.read_text(encoding="utf-8") == content

    def test_copy_nonexistent_source(self):
        """存在しないソースファイルのコピーテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_path = Path(temp_dir) / "nonexistent.txt"
            dst_path = Path(temp_dir) / "destination.txt"

            with pytest.raises(FileNotFoundError):
                copy_file_atomic(src_path, dst_path)


class TestGetFileSize:
    """get_file_size のテスト"""

    def test_file_size(self):
        """ファイルサイズの取得テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            content = "Hello, World!"  # 13 bytes
            file_path.write_text(content, encoding="utf-8")

            size = get_file_size(file_path)
            assert size == len(content.encode("utf-8"))

    def test_empty_file_size(self):
        """空ファイルのサイズテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "empty.txt"
            file_path.write_text("", encoding="utf-8")

            size = get_file_size(file_path)
            assert size == 0

    def test_nonexistent_file_size(self):
        """存在しないファイルのサイズテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nonexistent.txt"

            with pytest.raises(FileNotFoundError):
                get_file_size(file_path)


class TestGetFileMtime:
    """get_file_mtime のテスト"""

    def test_file_mtime(self):
        """ファイル更新時刻の取得テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            file_path.write_text("Test content", encoding="utf-8")

            mtime = get_file_mtime(file_path)
            assert isinstance(mtime, datetime)

            # 現在時刻に近いことを確認（1分以内）
            now = datetime.now()
            assert abs((now - mtime).total_seconds()) < 60

    def test_nonexistent_file_mtime(self):
        """存在しないファイルの更新時刻テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nonexistent.txt"

            with pytest.raises(FileNotFoundError):
                get_file_mtime(file_path)


class TestIsFileOlderThan:
    """is_file_older_than のテスト"""

    def test_new_file(self):
        """新しいファイルのテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            file_path.write_text("Test content", encoding="utf-8")

            # 作成直後なので、1時間より古くない
            assert is_file_older_than(file_path, 1) is False

    def test_old_file(self):
        """古いファイルのテスト（人工的に時刻を変更）"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            file_path.write_text("Test content", encoding="utf-8")

            # 2時間前の時刻に変更
            old_time = time.time() - (2 * 3600)
            os.utime(file_path, (old_time, old_time))

            # 1時間より古い
            assert is_file_older_than(file_path, 1) is True

    def test_nonexistent_file(self):
        """存在しないファイルのテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nonexistent.txt"

            # 存在しないファイルは「古い」と判定される
            assert is_file_older_than(file_path, 1) is True


class TestSafeJsonWrite:
    """safe_json_write のテスト"""

    def test_write_json(self):
        """JSONファイルの書き込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            data = {"key": "value", "number": 42}

            safe_json_write(file_path, data)

            assert file_path.exists()
            with open(file_path, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
            assert loaded_data == data

    def test_json_formatting(self):
        """JSONフォーマットのテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            data = {"key": "value"}

            safe_json_write(file_path, data, indent=4)

            content = file_path.read_text(encoding="utf-8")
            assert "    " in content  # 4スペースのインデントが含まれる


class TestSafeJsonRead:
    """safe_json_read のテスト"""

    def test_read_json(self):
        """JSONファイルの読み込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            data = {"key": "value", "number": 42}

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f)

            loaded_data = safe_json_read(file_path)
            assert loaded_data == data

    def test_read_invalid_json(self):
        """無効なJSONの読み込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "invalid.json"
            file_path.write_text("invalid json content", encoding="utf-8")

            with pytest.raises(json.JSONDecodeError):
                safe_json_read(file_path)

    def test_read_nonexistent_json(self):
        """存在しないJSONファイルの読み込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nonexistent.json"

            with pytest.raises(FileNotFoundError):
                safe_json_read(file_path)


class TestCleanupOldFiles:
    """cleanup_old_files のテスト"""

    def test_cleanup_old_files(self):
        """古いファイルのクリーンアップテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)

            # 新しいファイルを作成
            new_file = directory / "new.txt"
            new_file.write_text("new content", encoding="utf-8")

            # 古いファイルを作成（人工的に時刻を変更）
            old_file = directory / "old.txt"
            old_file.write_text("old content", encoding="utf-8")
            old_time = time.time() - (2 * 3600)  # 2時間前
            os.utime(old_file, (old_time, old_time))

            # 1時間より古いファイルを削除
            deleted_count = cleanup_old_files(directory, 1)

            assert deleted_count == 1
            assert new_file.exists()
            assert not old_file.exists()

    def test_cleanup_with_pattern(self):
        """パターン指定でのクリーンアップテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)

            # 古いファイルを複数作成
            txt_file = directory / "old.txt"
            log_file = directory / "old.log"

            old_time = time.time() - (2 * 3600)  # 2時間前
            for file_path in [txt_file, log_file]:
                file_path.write_text("content", encoding="utf-8")
                os.utime(file_path, (old_time, old_time))

            # .txtファイルのみ削除
            deleted_count = cleanup_old_files(directory, 1, "*.txt")

            assert deleted_count == 1
            assert not txt_file.exists()
            assert log_file.exists()

    def test_cleanup_nonexistent_directory(self):
        """存在しないディレクトリのクリーンアップテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_dir = Path(temp_dir) / "nonexistent"

            deleted_count = cleanup_old_files(nonexistent_dir, 1)
            assert deleted_count == 0


class TestCreateBackup:
    """create_backup のテスト"""

    def test_create_backup(self):
        """バックアップ作成のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_file = Path(temp_dir) / "original.txt"
            content = "Original content"
            original_file.write_text(content, encoding="utf-8")

            backup_path = create_backup(original_file)

            assert backup_path.exists()
            assert backup_path.read_text(encoding="utf-8") == content
            assert original_file.exists()  # 元ファイルは残る
            assert backup_path.name.startswith("original_")
            assert backup_path.suffix == ".txt"

    def test_create_backup_custom_directory(self):
        """カスタムディレクトリでのバックアップテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_file = Path(temp_dir) / "original.txt"
            backup_dir = Path(temp_dir) / "backups"
            content = "Original content"

            original_file.write_text(content, encoding="utf-8")
            backup_path = create_backup(original_file, backup_dir)

            assert backup_path.parent == backup_dir
            assert backup_path.exists()
            assert backup_path.read_text(encoding="utf-8") == content

    def test_create_backup_nonexistent_file(self):
        """存在しないファイルのバックアップテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_file = Path(temp_dir) / "nonexistent.txt"

            with pytest.raises(FileNotFoundError):
                create_backup(nonexistent_file)
