"""
URLユーティリティ

URL操作、変換、検証に関する共通機能
"""

from urllib.parse import urljoin, urlparse
from pathlib import Path
import hashlib


def resolve_relative_url(base_url: str, relative_url: str) -> str:
    """
    相対URLを絶対URLに変換

    Args:
        base_url: ベースURL
        relative_url: 相対URL

    Returns:
        絶対URL

    Examples:
        >>> resolve_relative_url("https://example.com/docs/", "../api/index.html")
        'https://example.com/api/index.html'
    """
    return urljoin(base_url, relative_url)


def url_to_filename(url: str, max_length: int = 255) -> str:
    """
    URLをファイル名に変換（ハッシュベース）

    Args:
        url: 変換対象のURL
        max_length: ファイル名の最大長

    Returns:
        安全なファイル名

    Examples:
        >>> url_to_filename("https://example.com/docs/api.html")
        'docs_api.html'
    """
    parsed = urlparse(url)

    # パスからファイル名を生成
    path = parsed.path.strip("/") or "index"
    if not path.endswith((".html", ".htm")):
        path += ".html"

    # 安全なファイル名に変換
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in path)

    # 長すぎる場合はハッシュを使用
    if len(safe_name) > max_length - 15:  # ハッシュ+拡張子分の余裕
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        base_length = max_length - 15  # _ハッシュ.html の分を差し引く
        safe_name = f"{safe_name[:base_length]}_{url_hash}.html"

    return safe_name


def is_same_domain(url1: str, url2: str) -> bool:
    """
    2つのURLが同じドメインかチェック

    Args:
        url1: 比較対象URL1
        url2: 比較対象URL2

    Returns:
        同じドメインの場合True

    Examples:
        >>> is_same_domain("https://example.com/page1", "https://example.com/page2")
        True
        >>> is_same_domain("https://example.com", "https://other.com")
        False
    """
    domain1 = urlparse(url1).netloc.lower()
    domain2 = urlparse(url2).netloc.lower()
    return domain1 == domain2


def normalize_url(url: str) -> str:
    """
    URLを正規化（末尾スラッシュの統一、クエリパラメータのソートなど）

    Args:
        url: 正規化対象のURL

    Returns:
        正規化されたURL

    Examples:
        >>> normalize_url("https://example.com/path/")
        'https://example.com/path'
    """
    parsed = urlparse(url)

    # パスの正規化（末尾スラッシュを除去、ただしルートは除く）
    path = parsed.path
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    # クエリパラメータのソート
    query = parsed.query
    if query:
        params = sorted(query.split("&"))
        query = "&".join(params)

    # URLを再構築
    normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
    if query:
        normalized += f"?{query}"
    if parsed.fragment:
        normalized += f"#{parsed.fragment}"

    return normalized


def extract_domain(url: str) -> str:
    """
    URLからドメイン名を抽出

    Args:
        url: 抽出対象のURL

    Returns:
        ドメイン名

    Examples:
        >>> extract_domain("https://example.com/path")
        'example.com'
    """
    return urlparse(url).netloc.lower()


def is_valid_url(url: str) -> bool:
    """
    URLの有効性をチェック

    Args:
        url: チェック対象のURL

    Returns:
        有効なURLの場合True

    Examples:
        >>> is_valid_url("https://example.com")
        True
        >>> is_valid_url("not-a-url")
        False
    """
    try:
        parsed = urlparse(url)
        return all([parsed.scheme, parsed.netloc]) and parsed.scheme in [
            "http",
            "https",
        ]
    except Exception:
        return False


def get_url_extension(url: str) -> str:
    """
    URLから拡張子を取得

    Args:
        url: 対象URL

    Returns:
        拡張子（ドット含む）、なければ空文字

    Examples:
        >>> get_url_extension("https://example.com/image.jpg")
        '.jpg'
    """
    parsed = urlparse(url)
    path = Path(parsed.path)
    return path.suffix.lower()


def build_cache_key(url: str) -> str:
    """
    URLからキャッシュキーを生成

    Args:
        url: 対象URL

    Returns:
        ハッシュ化されたキャッシュキー

    Examples:
        >>> build_cache_key("https://example.com/page")
        'a1b2c3d4e5f6...'
    """
    normalized = normalize_url(url)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]
