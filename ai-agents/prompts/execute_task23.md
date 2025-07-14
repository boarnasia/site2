# Execute Task 23: パイプライン統合テストの再実装

## Commander Role: 問題分析と設計

### Task 20の問題点
1. **インターフェース違反**: `fetch_result._html_content`という非公式属性を使用
2. **データフローの誤り**: FetchResult → HTML取得の経路が不適切
3. **リポジトリ未使用**: WebsiteCacheRepositoryを経由していない

### 正しいデータフロー
```
FetchService.execute() → FetchResult
                          ↓
                    cache_directory
                          ↓
WebsiteCacheRepository.find_by_url() → WebsiteCache
                                         ↓
                                    cache.pages
                                         ↓
                               CachedPage.read_text() → HTML
                                                         ↓
                                              DetectService.detect_*()
```

## Worker Role: 実装手順

### Step 1: ドメインモデルの改善

#### CachedPageにread_text()メソッドを追加
```python
# src/site2/core/domain/fetch_domain.py

class CachedPage(BaseModel):
    """キャッシュされたページ"""

    relative_url: str = Field(..., description="相対URL")
    local_path: str = Field(..., description="ローカルファイルパス")
    size_bytes: int = Field(..., ge=0, description="ファイルサイズ")
    content_hash: str = Field(..., description="コンテンツハッシュ")
    last_fetched: datetime = Field(..., description="最終取得日時")
    is_root: bool = Field(default=False, description="ルートページかどうか")

    def read_text(self, encoding: str = "utf-8") -> str:
        """キャッシュされたHTMLコンテンツを読み込む

        Args:
            encoding: 文字エンコーディング（デフォルト: utf-8）

        Returns:
            HTMLコンテンツ

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            UnicodeDecodeError: エンコーディングエラー
        """
        return Path(self.local_path).read_text(encoding=encoding)
```

### Step 2: Protocol定義の修正

#### WebsiteCacheRepositoryProtocolからsaveメソッドを削除
```python
# src/site2/core/ports/fetch_contracts.py

class WebsiteCacheRepositoryProtocol(Protocol):
    """キャッシュリポジトリの契約（読み取り専用）"""

    # def save(self, cache: WebsiteCache) -> None:  # 削除

    def find_by_url(self, url: WebsiteURL) -> Optional[WebsiteCache]:
        """URLでキャッシュを検索"""
        ...

    def find_all(self) -> List[WebsiteCache]:
        """すべてのキャッシュを取得"""
        ...
```

### Step 3: モックサービスの修正

#### MockRepositoryの改善
```python
# tests/mocks/services.py

class MockRepository(WebsiteCacheRepositoryProtocol):
    """メモリ内でキャッシュを管理するモックリポジトリ"""

    def __init__(self):
        self._cache = {}
        self._setup_test_data()

    def _setup_test_data(self):
        """テスト用のデータを準備"""
        # simple-siteのHTMLコンテンツを準備
        test_html = Path("tests/fixtures/websites/simple-site/index.html").read_text()

        # テスト用のWebsiteCacheを作成
        test_cache = WebsiteCache(
            id="test-cache-001",
            url=WebsiteURL("http://test-site/"),
            pages=[
                CachedPage(
                    relative_url="/",
                    local_path="tests/fixtures/websites/simple-site/index.html",
                    size_bytes=len(test_html.encode()),
                    content_hash="test-hash",
                    last_fetched=datetime.now(),
                    is_root=True,
                ),
                # 他のページも追加...
            ],
            total_size=len(test_html.encode()),
            last_updated=datetime.now(),
        )
        self._cache["http://test-site/"] = test_cache

    async def find_by_url(self, url: WebsiteURL) -> Optional[WebsiteCache]:
        return self._cache.get(str(url))

    async def find_all(self) -> List[WebsiteCache]:
        return list(self._cache.values())
```

#### MockFetchServiceの修正
```python
class MockFetchService(FetchServiceProtocol):
    """テスト用のフェッチサービス"""

    def __init__(self, repository: WebsiteCacheRepositoryProtocol):
        self.repository = repository

    async def execute(self, url: str) -> FetchResult:
        # リポジトリにキャッシュが存在することを前提
        return FetchResult(
            cache_id="test-cache-001",
            root_url=HttpUrl(url + "/" if not url.endswith("/") else url),
            pages_fetched=3,
            pages_updated=0,
            total_size=1024,
            cache_directory="tests/fixtures/websites/simple-site",
            errors=[],
        )
```

### Step 4: 統合テストの修正

```python
# tests/integration/test_pipeline_integration.py

async def test_full_pipeline(self):
    """パイプライン全体の動作確認（正しいインターフェース使用）"""

    # Step 1: Fetch
    fetch_service = self.container.fetch_service()
    fetch_result = await fetch_service.execute("http://test-site")

    # Step 2: リポジトリからキャッシュを取得
    repository = self.container.website_cache_repository()
    cache = await repository.find_by_url(
        WebsiteURL(str(fetch_result.root_url))
    )
    assert cache is not None, "Cache should exist"

    # Step 3: メインページのHTMLを読み込み
    main_page = next((p for p in cache.pages if p.is_root), None)
    assert main_page is not None, "Main page should exist"

    html_content = main_page.read_text()

    # Step 4: Detect
    detect_service = self.container.detect_service()
    main_content = await detect_service.detect_main_content(html_content)
    navigation = await detect_service.detect_navigation(html_content)
    doc_order = await detect_service.detect_order(
        Path(fetch_result.cache_directory),
        navigation
    )

    # Step 5: Build
    build_service = self.container.build_service()
    markdown = await build_service.build_markdown(
        [main_content],
        doc_order
    )

    # 検証
    assert "Welcome to Test Site" in markdown.content
    assert markdown.metadata.source_url == "http://test-site"
```

### Step 5: ヘルパー関数の追加

```python
# tests/integration/helpers.py

async def get_html_from_fetch_result(
    fetch_result: FetchResult,
    repository: WebsiteCacheRepositoryProtocol,
    page_filter: Optional[Callable[[CachedPage], bool]] = None
) -> str:
    """FetchResultからHTMLコンテンツを取得するヘルパー関数

    Args:
        fetch_result: Fetch結果
        repository: キャッシュリポジトリ
        page_filter: ページフィルター関数（デフォルト: is_root=True）

    Returns:
        HTMLコンテンツ

    Raises:
        ValueError: キャッシュまたはページが見つからない場合
    """
    if page_filter is None:
        page_filter = lambda p: p.is_root

    cache = await repository.find_by_url(WebsiteURL(str(fetch_result.root_url)))
    if not cache:
        raise ValueError(f"Cache not found for URL: {fetch_result.root_url}")

    page = next((p for p in cache.pages if page_filter(p)), None)
    if not page:
        raise ValueError("No matching page found in cache")

    return page.read_text()
```

## 実装時の注意事項

1. **Protocol準拠の徹底**
   - 非公式な属性やメソッドを使用しない
   - 定義されたインターフェースのみを使用

2. **エラーハンドリング**
   - キャッシュが見つからない場合
   - ファイルが読めない場合
   - エンコーディングエラー

3. **テストデータの管理**
   - `tests/fixtures/websites/simple-site/`のファイルを活用
   - モックでも実際のファイルを読み込む

4. **非同期処理の一貫性**
   - async/awaitを適切に使用
   - 同期メソッド（read_text）と非同期メソッドの使い分け

これにより、実際のサービス実装でも使える正しいデータフローでテストが実装されます。
