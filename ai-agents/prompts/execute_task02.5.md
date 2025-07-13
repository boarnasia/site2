# Execute Task 02.5: パイプライン統合テストの実装

## Commander Role: タスクの分析と設計

### 目的の確認
このタスクでは、task 3（詳細設計）に進む前に、基本的なパイプラインが正しく連携することを確認します。
TestContainerとモックサービスを使用して、エンドツーエンドの動作を検証します。

### 実装方針
1. **モックファースト**: 最小限の実装で動作確認
2. **インターフェース重視**: 契約（Protocol）の整合性を検証
3. **段階的検証**: 個別サービス → 統合 → E2E

### アーキテクチャ設計
```
TestContainer
├── MockFetchService (IFetchService)
├── MockDetectService (IDetectService)
├── MockBuildService (IBuildService)
└── MockRepository (IWebsiteCacheRepository)

統合テスト
├── 個別サービステスト
├── サービス連携テスト
└── パイプライン全体テスト
```

### 期待される動作フロー
1. URLを受け取る（simple-site）
2. MockFetchServiceがHTMLファイルを返す
3. MockDetectServiceがコンテンツ構造を解析
4. MockBuildServiceがMarkdownを生成
5. 期待される出力を検証

## Worker Role: 実装

以下の順序で実装を進めてください：

### Step 1: モックサービスの作成
`tests/mocks/__init__.py` および `tests/mocks/services.py` を作成し、以下を実装：

```python
# tests/mocks/services.py
from typing import List, Optional
from pathlib import Path

from site2.core.domain.fetch import FetchResult, WebsiteCache
from site2.core.domain.detect import MainContent, Navigation, DocumentOrder
from site2.core.domain.build import MarkdownDocument
from site2.core.ports.services import IFetchService, IDetectService, IBuildService
from site2.core.ports.repositories import IWebsiteCacheRepository

class MockRepository(IWebsiteCacheRepository):
    """メモリ内でキャッシュを管理するモックリポジトリ"""
    
    def __init__(self):
        self._cache = {}
    
    async def save(self, cache: WebsiteCache) -> None:
        self._cache[cache.url] = cache
    
    async def find_by_url(self, url: str) -> Optional[WebsiteCache]:
        return self._cache.get(url)
    
    async def list_all(self) -> List[WebsiteCache]:
        return list(self._cache.values())

class MockFetchService(IFetchService):
    """simple-siteのデータを返すモックサービス"""
    
    def __init__(self, repository: IWebsiteCacheRepository):
        self.repository = repository
    
    async def execute(self, url: str) -> FetchResult:
        # simple-siteのHTMLを読み込んで返す
        # tests/fixtures/websites/simple-site/ のデータを使用
        pass

class MockDetectService(IDetectService):
    """固定の検出結果を返すモックサービス"""
    
    async def detect_main_content(self, html: str) -> MainContent:
        # main.content セレクタを返す
        pass
    
    async def detect_navigation(self, html: str) -> Navigation:
        # nav.navigation セレクタを返す
        pass
    
    async def detect_order(self, cache_dir: Path) -> DocumentOrder:
        # 固定の順序を返す
        pass

class MockBuildService(IBuildService):
    """簡単なMarkdownを生成するモックサービス"""
    
    async def build_markdown(self, contents: List[MainContent]) -> MarkdownDocument:
        # シンプルなMarkdownを生成
        pass
```

### Step 2: TestContainerの設定
`tests/integration/test_container.py` を作成：

```python
from dependency_injector import providers
from site2.core.containers import TestContainer
from tests.mocks.services import (
    MockFetchService, MockDetectService, 
    MockBuildService, MockRepository
)

def test_container_setup():
    """TestContainerが正しく設定されることを確認"""
    container = TestContainer()
    
    # モックサービスで上書き
    container.website_cache_repository.override(
        providers.Singleton(MockRepository)
    )
    container.fetch_service.override(
        providers.Factory(
            MockFetchService,
            repository=container.website_cache_repository,
        )
    )
    # 他のサービスも同様に設定
    
    # 各サービスが正しく注入されることを確認
    fetch_service = container.fetch_service()
    assert isinstance(fetch_service, MockFetchService)
```

### Step 3: パイプライン統合テスト
`tests/integration/test_pipeline_integration.py` を作成：

```python
import asyncio
from site2.core.containers import TestContainer

async def test_full_pipeline():
    """パイプライン全体の動作確認"""
    container = TestContainer()
    # モックサービスを設定
    
    # Step 1: Fetch
    fetch_service = container.fetch_service()
    fetch_result = await fetch_service.execute("http://test-site")
    
    # Step 2: Detect
    detect_service = container.detect_service()
    main_content = await detect_service.detect_main_content(
        fetch_result.html_files[0].content
    )
    
    # Step 3: Build
    build_service = container.build_service()
    markdown = await build_service.build_markdown([main_content])
    
    # 検証
    assert "# Welcome to Test Site" in markdown.content
```

### Step 4: 問題点の記録
実装中に発見された問題点を `tests/integration/issues.md` に記録：

```markdown
# 統合テストで発見された問題点

## インターフェースの不整合
- [ ] Protocol定義と実装の不一致
- [ ] 非同期/同期の混在

## データフローの問題
- [ ] サービス間のデータ受け渡し
- [ ] エラーハンドリングの不足

## その他
- [ ] DIコンテナの設定方法
```

## 実装時の注意事項
1. **モックは最小限に**: 動作確認に必要な最小限の実装
2. **エラーは記録**: 問題があれば修正せずに記録
3. **テストファースト**: テストを書いてから実装
4. **非同期を考慮**: async/awaitの適切な使用

## 検証項目
- [ ] 各モックサービスが単体で動作する
- [ ] DIコンテナ経由でサービスが取得できる
- [ ] パイプライン全体が通しで動作する
- [ ] simple-siteの入力で期待される出力が得られる

## 次のステップ
このタスクで発見された問題点を踏まえて、task 3の詳細設計に反映させます。
