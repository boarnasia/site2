"""
ファイルユーティリティ

安全なファイル操作、ハッシュ計算、アトミック操作に関する共通機能
"""

from pathlib import Path
from typing import Union, Optional
import tempfile
import shutil
import hashlib
import json
from datetime import datetime


def ensure_directory(path: Path) -> Path:
    """
    ディレクトリを作成（既存の場合は何もしない）

    Args:
        path: 作成するディレクトリのパス

    Returns:
        作成されたディレクトリのパス

    Examples:
        >>> ensure_directory(Path("/tmp/test"))
        PosixPath('/tmp/test')
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_write(path: Path, content: Union[str, bytes], encoding: str = "utf-8") -> None:
    """
    安全にファイルを書き込み（アトミック操作）

    Args:
        path: 書き込み先のパス
        content: 書き込む内容
        encoding: テキストファイルの場合のエンコーディング

    Raises:
        PermissionError: 書き込み権限がない場合
        OSError: ディスク容量不足など
    """
    ensure_directory(path.parent)

    # 一時ファイルに書き込み
    with tempfile.NamedTemporaryFile(
        dir=path.parent,
        delete=False,
        mode="wb" if isinstance(content, bytes) else "w",
        encoding=encoding if isinstance(content, str) else None,
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    # アトミックに移動
    tmp_path.replace(path)


def safe_read(
    path: Path, encoding: str = "utf-8", binary: bool = False
) -> Union[str, bytes]:
    """
    安全にファイルを読み込み

    Args:
        path: 読み込み対象のパス
        encoding: テキストファイルの場合のエンコーディング
        binary: バイナリモードで読み込むかどうか

    Returns:
        ファイル内容

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        PermissionError: 読み込み権限がない場合
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if binary:
        with open(path, "rb") as f:
            return f.read()
    else:
        # バイナリファイルの判定（簡易版）
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # バイナリファイルの場合
            with open(path, "rb") as f:
                return f.read()


def calculate_file_hash(path: Path, algorithm: str = "md5") -> str:
    """
    ファイルのハッシュ値を計算

    Args:
        path: 対象ファイルのパス
        algorithm: ハッシュアルゴリズム（md5, sha1, sha256など）

    Returns:
        ハッシュ値（16進数文字列）

    Examples:
        >>> calculate_file_hash(Path("test.txt"))
        'a1b2c3d4e5f6...'
    """
    hasher = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def copy_file_atomic(src: Path, dst: Path) -> None:
    """
    ファイルをアトミックにコピー

    Args:
        src: コピー元のパス
        dst: コピー先のパス

    Raises:
        FileNotFoundError: コピー元ファイルが存在しない場合
        PermissionError: 権限がない場合
    """
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    ensure_directory(dst.parent)

    # 一時ファイルにコピー
    with tempfile.NamedTemporaryFile(dir=dst.parent, delete=False) as tmp:
        shutil.copy2(src, tmp.name)
        tmp_path = Path(tmp.name)

    # アトミックに移動
    tmp_path.replace(dst)


def get_file_size(path: Path) -> int:
    """
    ファイルサイズを取得

    Args:
        path: 対象ファイルのパス

    Returns:
        ファイルサイズ（バイト）

    Raises:
        FileNotFoundError: ファイルが存在しない場合
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    return path.stat().st_size


def get_file_mtime(path: Path) -> datetime:
    """
    ファイルの最終更新時刻を取得

    Args:
        path: 対象ファイルのパス

    Returns:
        最終更新時刻

    Raises:
        FileNotFoundError: ファイルが存在しない場合
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    return datetime.fromtimestamp(path.stat().st_mtime)


def is_file_older_than(path: Path, hours: int) -> bool:
    """
    ファイルが指定時間より古いかチェック

    Args:
        path: 対象ファイルのパス
        hours: 比較する時間（時間単位）

    Returns:
        指定時間より古い場合True

    Examples:
        >>> is_file_older_than(Path("old_file.txt"), 24)
        True
    """
    if not path.exists():
        return True

    mtime = get_file_mtime(path)
    now = datetime.now()
    age_hours = (now - mtime).total_seconds() / 3600

    return age_hours > hours


def safe_json_write(path: Path, data: dict, indent: int = 2) -> None:
    """
    JSONファイルを安全に書き込み

    Args:
        path: 書き込み先のパス
        data: 書き込むデータ
        indent: インデント幅
    """
    content = json.dumps(data, indent=indent, ensure_ascii=False)
    safe_write(path, content)


def safe_json_read(path: Path) -> dict:
    """
    JSONファイルを安全に読み込み

    Args:
        path: 読み込み対象のパス

    Returns:
        パース済みデータ

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        json.JSONDecodeError: JSONパースエラーの場合
    """
    content = safe_read(path)
    return json.loads(content)


def cleanup_old_files(directory: Path, hours: int, pattern: str = "*") -> int:
    """
    古いファイルを削除

    Args:
        directory: 対象ディレクトリ
        hours: この時間より古いファイルを削除（時間単位）
        pattern: ファイル名パターン

    Returns:
        削除したファイル数
    """
    if not directory.exists():
        return 0

    deleted_count = 0
    for file_path in directory.glob(pattern):
        if file_path.is_file() and is_file_older_than(file_path, hours):
            try:
                file_path.unlink()
                deleted_count += 1
            except OSError:
                # 削除に失敗した場合は無視
                pass

    return deleted_count


def create_backup(path: Path, backup_dir: Optional[Path] = None) -> Path:
    """
    ファイルのバックアップを作成

    Args:
        path: バックアップ対象のパス
        backup_dir: バックアップディレクトリ（Noneの場合は同ディレクトリ）

    Returns:
        バックアップファイルのパス

    Raises:
        FileNotFoundError: 対象ファイルが存在しない場合
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if backup_dir is None:
        backup_dir = path.parent

    ensure_directory(backup_dir)

    # タイムスタンプ付きバックアップファイル名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{path.stem}_{timestamp}{path.suffix}"
    backup_path = backup_dir / backup_name

    copy_file_atomic(path, backup_path)
    return backup_path
