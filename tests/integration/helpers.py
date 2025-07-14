"""
統合テスト用のヘルパー関数
"""

from typing import Optional, Callable

from site2.core.domain.fetch_domain import WebsiteURL, CachedPage
from site2.core.ports.fetch_contracts import FetchResult, WebsiteCacheRepositoryProtocol


async def get_html_from_fetch_result(
    fetch_result: FetchResult,
    repository: WebsiteCacheRepositoryProtocol,
    page_filter: Optional[Callable[[CachedPage], bool]] = None,
) -> str:
    """FetchResultからHTMLコンテンツを取得するヘルパー関数

    Args:
        fetch_result: Fetch結果
        repository: キャッシュリポジトリ
        page_filter: ページフィルター関数（デフォルト: root_urlと一致するページ）

    Returns:
        HTMLコンテンツ

    Raises:
        ValueError: キャッシュまたはページが見つからない場合
    """
    cache = repository.find_by_url(WebsiteURL(value=str(fetch_result.root_url)))
    if not cache:
        raise ValueError(f"Cache not found for URL: {fetch_result.root_url}")

    if page_filter is None:
        # デフォルト: FetchResult.root_urlと一致するページを取得
        page = next(
            (
                page
                for page in cache.pages
                if str(page.page_url.value) == str(fetch_result.root_url)
            ),
            None,
        )
    else:
        page = next((p for p in cache.pages if page_filter(p)), None)

    if not page:
        raise ValueError("No matching page found in cache")

    return page.read_text()


def get_main_page_html(
    fetch_result: FetchResult, repository: WebsiteCacheRepositoryProtocol
) -> str:
    """FetchResultからメインページのHTMLを取得するヘルパー（シンプル版）

    Args:
        fetch_result: Fetch結果
        repository: キャッシュリポジトリ

    Returns:
        HTMLコンテンツ

    Raises:
        ValueError: キャッシュまたはページが見つからない場合
    """
    cache = repository.find_by_url(WebsiteURL(value=str(fetch_result.root_url)))
    if not cache:
        raise ValueError(f"Cache not found for URL: {fetch_result.root_url}")

    # シンプルな実装: FetchResult.root_urlと完全一致するページを探す
    root_page = next(
        (
            page
            for page in cache.pages
            if str(page.page_url.value) == str(fetch_result.root_url)
        ),
        None,
    )

    if not root_page:
        raise ValueError(f"Root page not found for URL: {fetch_result.root_url}")

    return root_page.read_text()
