# Task 23: パイプライン統合テストの再実装（インターフェース準拠）

## 背景
Task 20で実装した統合テストには以下の問題があった：
1. `fetch_result._html_content`という非公式な属性を使用
2. FetchResultからDetectServiceへのデータフローが不適切
3. インターフェース（Protocol）に準拠していない実装

Task 20を閉じ、正しいインターフェースに基づいた実装を行う。

## 目的
- Protocolに厳密に準拠したパイプライン統合テストの実装
- 実際のデータフローに沿った動作確認
- 各サービス間の正しい連携の検証

## 事前準備（インターフェース改善）

### 1. WebsiteCacheRepositoryProtocolの修正
```python
# saveメソッドを削除（FetchServiceが内部で保存するため）
class WebsiteCacheRepositoryProtocol(Protocol):
    # def save(self, cache: WebsiteCache) -> None:  # 削除

    def find_by_url(self, url: WebsiteURL) -> Optional[WebsiteCache]:
        ...

    def find_all(self) -> List[WebsiteCache]:
        ...
```

### 2. CachedPageにread_text()メソッドを追加
```python
# src/site2/core/domain/fetch_domain.py
class CachedPage(BaseModel):
    # 既存のフィールド...

    def read_text(self, encoding: str = "utf-8") -> str:
        """キャッシュされたHTMLコンテンツを読み込む"""
        return Path(self.local_path).read_text(encoding=encoding)
```

## 実装内容

### 1. 正しいデータフローの実装
```python
# パイプラインの正しいフロー
1. Fetch → FetchResult（cache_directoryを含む）
2. Repository経由でWebsiteCacheを取得
3. CachedPageからHTMLコンテンツを読み込み
4. DetectServiceでコンテンツを解析
5. BuildServiceでMarkdownを生成
```

### 2. モックサービスの修正
- MockRepositoryが実際のWebsiteCacheを返すように実装
- MockFetchServiceがリポジトリと連携
- CachedPageのread_text()をモックで実装

### 3. 統合テストの修正
```python
async def test_full_pipeline(self):
    # Step 1: Fetch
    fetch_service = self.container.fetch_service()
    fetch_result = await fetch_service.execute("http://test-site")

    # Step 2: リポジトリからキャッシュを取得
    repository = self.container.website_cache_repository()
    cache = await repository.find_by_url(
        WebsiteURL(str(fetch_result.root_url))
    )

    # Step 3: メインページのHTMLを読み込み
    main_page = next((p for p in cache.pages if p.is_root), None)
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
```

### 4. ヘルパーメソッドの追加
```python
def get_main_page_html(fetch_result: FetchResult, repository: WebsiteCacheRepositoryProtocol) -> str:
    """FetchResultからメインページのHTMLを取得するヘルパー"""
    cache = repository.find_by_url(WebsiteURL(str(fetch_result.root_url)))
    if not cache:
        raise ValueError("Cache not found")

    main_page = next((p for p in cache.pages if p.is_root), None)
    if not main_page:
        raise ValueError("Main page not found")

    return main_page.read_text()
```

## 成功基準
- [ ] インターフェース（Protocol）に厳密に準拠
- [ ] `_html_content`のような非公式属性を使用しない
- [ ] リポジトリ経由での正しいデータ取得
- [ ] 全テストがPASSする
- [ ] 実際のサービス実装でも同じフローが使える

## 注意事項
- Protocolの契約を厳守する
- モックでも実際の実装と同じインターフェースを使用
- エラーケースも適切にテスト
- ドキュメントとコメントを充実させる

## 期待される成果物
1. 修正されたドメインモデル（CachedPage.read_text()）
2. 修正されたProtocol定義（WebsiteCacheRepositoryProtocol）
3. 更新されたモックサービス
4. 正しいインターフェースに基づく統合テスト
5. Task 23実行レポート
