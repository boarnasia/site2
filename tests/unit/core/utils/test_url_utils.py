"""
URLユーティリティのテスト
"""

from site2.core.utils.url_utils import (
    resolve_relative_url,
    url_to_filename,
    is_same_domain,
    normalize_url,
    extract_domain,
    is_valid_url,
    get_url_extension,
    build_cache_key,
)


class TestResolveRelativeUrl:
    """resolve_relative_url のテスト"""

    def test_relative_path(self):
        """相対パスの解決テスト"""
        base = "https://example.com/docs/"
        relative = "../api/index.html"
        result = resolve_relative_url(base, relative)
        assert result == "https://example.com/api/index.html"

    def test_absolute_url(self):
        """絶対URLが渡された場合のテスト"""
        base = "https://example.com/docs/"
        absolute = "https://other.com/page.html"
        result = resolve_relative_url(base, absolute)
        assert result == "https://other.com/page.html"

    def test_same_directory(self):
        """同一ディレクトリ内の相対パステスト"""
        base = "https://example.com/docs/"
        relative = "page.html"
        result = resolve_relative_url(base, relative)
        assert result == "https://example.com/docs/page.html"

    def test_query_parameters(self):
        """クエリパラメータを含む相対URLのテスト"""
        base = "https://example.com/docs/"
        relative = "search.html?q=test"
        result = resolve_relative_url(base, relative)
        assert result == "https://example.com/docs/search.html?q=test"


class TestUrlToFilename:
    """url_to_filename のテスト"""

    def test_simple_url(self):
        """シンプルなURLのテスト"""
        url = "https://example.com/docs/api.html"
        filename = url_to_filename(url)
        assert filename == "docs_api.html"

    def test_url_without_extension(self):
        """拡張子なしURLのテスト"""
        url = "https://example.com/docs/api"
        filename = url_to_filename(url)
        assert filename == "docs_api.html"

    def test_root_url(self):
        """ルートURLのテスト"""
        url = "https://example.com/"
        filename = url_to_filename(url)
        assert filename == "index.html"

    def test_special_characters(self):
        """特殊文字を含むURLのテスト"""
        url = "https://example.com/docs/api-v2.html"
        filename = url_to_filename(url)
        assert filename == "docs_api-v2.html"

    def test_unsafe_characters(self):
        """安全でない文字を含むURLのテスト"""
        url = "https://example.com/docs/api%20test.html"
        filename = url_to_filename(url)
        # 特殊文字は _ に置換される
        assert "_" in filename
        assert filename.endswith(".html")

    def test_long_url(self):
        """長いURLのテスト（ハッシュが使用される）"""
        long_path = "a" * 300
        url = f"https://example.com/{long_path}.html"
        filename = url_to_filename(url)

        # 最大長制限内に収まっている
        assert len(filename) <= 255
        # ハッシュが含まれている
        assert "_" in filename
        assert filename.endswith(".html")


class TestIsSameDomain:
    """is_same_domain のテスト"""

    def test_same_domain(self):
        """同じドメインのテスト"""
        url1 = "https://example.com/page1"
        url2 = "https://example.com/page2"
        assert is_same_domain(url1, url2) is True

    def test_different_domains(self):
        """異なるドメインのテスト"""
        url1 = "https://example.com/page1"
        url2 = "https://other.com/page2"
        assert is_same_domain(url1, url2) is False

    def test_subdomain_difference(self):
        """サブドメインが異なる場合のテスト"""
        url1 = "https://www.example.com/page1"
        url2 = "https://api.example.com/page2"
        assert is_same_domain(url1, url2) is False

    def test_case_insensitive(self):
        """大文字小文字を無視するテスト"""
        url1 = "https://EXAMPLE.COM/page1"
        url2 = "https://example.com/page2"
        assert is_same_domain(url1, url2) is True

    def test_protocol_difference(self):
        """プロトコルが異なる場合のテスト"""
        url1 = "http://example.com/page1"
        url2 = "https://example.com/page2"
        assert is_same_domain(url1, url2) is True


class TestNormalizeUrl:
    """normalize_url のテスト"""

    def test_trailing_slash_removal(self):
        """末尾スラッシュの除去テスト"""
        url = "https://example.com/path/"
        result = normalize_url(url)
        assert result == "https://example.com/path"

    def test_root_path_preservation(self):
        """ルートパスの保持テスト"""
        url = "https://example.com/"
        result = normalize_url(url)
        assert result == "https://example.com/"

    def test_query_parameter_sorting(self):
        """クエリパラメータのソートテスト"""
        url = "https://example.com/search?c=3&a=1&b=2"
        result = normalize_url(url)
        assert result == "https://example.com/search?a=1&b=2&c=3"

    def test_fragment_preservation(self):
        """フラグメントの保持テスト"""
        url = "https://example.com/page#section"
        result = normalize_url(url)
        assert result == "https://example.com/page#section"

    def test_complex_url(self):
        """複雑なURLの正規化テスト"""
        url = "https://example.com/path/?c=3&a=1#section"
        result = normalize_url(url)
        assert result == "https://example.com/path?a=1&c=3#section"


class TestExtractDomain:
    """extract_domain のテスト"""

    def test_simple_domain(self):
        """シンプルなドメイン抽出テスト"""
        url = "https://example.com/path"
        domain = extract_domain(url)
        assert domain == "example.com"

    def test_subdomain(self):
        """サブドメイン付きのテスト"""
        url = "https://www.example.com/path"
        domain = extract_domain(url)
        assert domain == "www.example.com"

    def test_port_number(self):
        """ポート番号付きのテスト"""
        url = "https://example.com:8080/path"
        domain = extract_domain(url)
        assert domain == "example.com:8080"

    def test_case_normalization(self):
        """大文字小文字の正規化テスト"""
        url = "https://EXAMPLE.COM/path"
        domain = extract_domain(url)
        assert domain == "example.com"


class TestIsValidUrl:
    """is_valid_url のテスト"""

    def test_valid_http_url(self):
        """有効なHTTP URLのテスト"""
        url = "http://example.com"
        assert is_valid_url(url) is True

    def test_valid_https_url(self):
        """有効なHTTPS URLのテスト"""
        url = "https://example.com"
        assert is_valid_url(url) is True

    def test_invalid_scheme(self):
        """無効なスキームのテスト"""
        url = "ftp://example.com"
        assert is_valid_url(url) is False

    def test_no_scheme(self):
        """スキームなしのテスト"""
        url = "example.com"
        assert is_valid_url(url) is False

    def test_no_netloc(self):
        """ネットワークロケーションなしのテスト"""
        url = "https://"
        assert is_valid_url(url) is False

    def test_malformed_url(self):
        """形式不正なURLのテスト"""
        url = "not-a-url"
        assert is_valid_url(url) is False


class TestGetUrlExtension:
    """get_url_extension のテスト"""

    def test_html_extension(self):
        """HTML拡張子のテスト"""
        url = "https://example.com/page.html"
        ext = get_url_extension(url)
        assert ext == ".html"

    def test_no_extension(self):
        """拡張子なしのテスト"""
        url = "https://example.com/page"
        ext = get_url_extension(url)
        assert ext == ""

    def test_multiple_dots(self):
        """複数ドットを含むテスト"""
        url = "https://example.com/archive.tar.gz"
        ext = get_url_extension(url)
        assert ext == ".gz"

    def test_case_normalization(self):
        """大文字小文字の正規化テスト"""
        url = "https://example.com/image.JPG"
        ext = get_url_extension(url)
        assert ext == ".jpg"

    def test_query_parameters(self):
        """クエリパラメータを含むテスト"""
        url = "https://example.com/image.jpg?size=large"
        ext = get_url_extension(url)
        assert ext == ".jpg"


class TestBuildCacheKey:
    """build_cache_key のテスト"""

    def test_consistent_key(self):
        """一貫性のあるキー生成テスト"""
        url = "https://example.com/page"
        key1 = build_cache_key(url)
        key2 = build_cache_key(url)
        assert key1 == key2

    def test_different_urls_different_keys(self):
        """異なるURLでは異なるキーが生成されるテスト"""
        url1 = "https://example.com/page1"
        url2 = "https://example.com/page2"
        key1 = build_cache_key(url1)
        key2 = build_cache_key(url2)
        assert key1 != key2

    def test_normalized_urls_same_key(self):
        """正規化されたURLでは同じキーが生成されるテスト"""
        url1 = "https://example.com/page/"
        url2 = "https://example.com/page"
        key1 = build_cache_key(url1)
        key2 = build_cache_key(url2)
        assert key1 == key2

    def test_key_length(self):
        """キーの長さのテスト"""
        url = "https://example.com/page"
        key = build_cache_key(url)
        assert len(key) == 16  # SHA256の最初の16文字
