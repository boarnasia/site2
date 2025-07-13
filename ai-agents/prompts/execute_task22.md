# Execute Task 22: インターフェース定義の統合と整理

## Commander Role: タスク分析と実装計画

### 現状分析
1. **重複している定義**：
   - `services.py`: `IFetchService`, `IDetectService`, `IBuildService`
   - `*_contracts.py`: `FetchServiceProtocol`, `DetectServiceProtocol`, `BuildServiceProtocol`

2. **統合方針**：
   - `*_contracts.py`を採用（より完成度が高い）
   - Protocol名を`I`プレフィックスに統一
   - Task 21の変更を反映

### 実装手順
1. 各`*_contracts.py`のProtocol名を変更
2. Task 21の変更（パラメータ追加）を反映
3. `services.py`を削除
4. `__init__.py`を整備
5. テストのimportを更新

## Worker Role: 実装

### Step 1: fetch_contracts.pyの更新

```python
# src/site2/core/ports/fetch_contracts.py の該当部分を修正

# 変更前:
class FetchServiceProtocol(Protocol):

# 変更後:
class IFetchService(Protocol):

# リポジトリとクローラーも統一
class IWebsiteCacheRepository(Protocol):  # 変更前: WebsiteCacheRepositoryProtocol
class IWebCrawler(Protocol):  # 変更前: WebCrawlerProtocol
```

### Step 2: detect_contracts.pyの更新

```python
# src/site2/core/ports/detect_contracts.py の該当部分を修正

# 変更前:
class DetectServiceProtocol(Protocol):
    # ...
    def detect_order(
        self,
        cache_dir: Path,
        options: Optional[DetectOrderOptions] = None,
    ) -> DocumentOrder:

# 変更後:
class IDetectService(Protocol):
    # ...
    def detect_order(
        self,
        cache_dir: Path,
        navigation: Navigation,  # Task 21で追加
        options: Optional[DetectOrderOptions] = None,
    ) -> DocumentOrder:
```

### Step 3: build_contracts.pyの更新

```python
# src/site2/core/ports/build_contracts.py の該当部分を修正

# 変更前:
class BuildServiceProtocol(Protocol):
    # ...
    def build_markdown(
        self,
        request: BuildMarkdownRequest,
    ) -> BuildMarkdownResult:

# 変更後:
class IBuildService(Protocol):
    # ...
    def build_markdown(
        self,
        request: BuildMarkdownRequest,
        doc_order: DocumentOrder,  # Task 21で追加
    ) -> BuildMarkdownResult:
```

注意: build_contracts.pyはDTOベースのインターフェースなので、DocumentOrderは`BuildMarkdownRequest`に含めるべきかもしれません。

### Step 4: pipeline_contracts.pyの確認と更新

```python
# src/site2/core/ports/pipeline_contracts.py

# 変更前:
class PipelineServiceProtocol(Protocol):

# 変更後:
class IPipelineService(Protocol):
```

### Step 5: parser_contracts.pyの確認

parser_contracts.pyにもProtocolがあれば、同様に`I`プレフィックスに統一。

### Step 6: __init__.pyの整備

```python
# src/site2/core/ports/__init__.py

"""
site2 ポート定義

Clean Architectureのポート（インターフェース）を定義
"""

# Fetch
from .fetch_contracts import (
    IFetchService,
    IWebCrawler,
    IWebsiteCacheRepository,
    FetchRequest,
    FetchResult,
    FetchError,
    NetworkError,
    InvalidURLError,
    CachePermissionError,
)

# Detect
from .detect_contracts import (
    IDetectService,
    DetectMainContentRequest,
    DetectMainContentResult,
    DetectNavigationRequest,
    DetectNavigationResult,
    DetectOrderRequest,
    DetectOrderResult,
    DetectError,
)

# Build
from .build_contracts import (
    IBuildService,
    BuildMarkdownRequest,
    BuildMarkdownResult,
    BuildPdfRequest,
    BuildPdfResult,
    BuildError,
)

# Pipeline
from .pipeline_contracts import (
    IPipelineService,
    PipelineRequest,
    PipelineResult,
    PipelineError,
)

__all__ = [
    # Services
    "IFetchService",
    "IDetectService",
    "IBuildService",
    "IPipelineService",
    # Repositories & External
    "IWebCrawler",
    "IWebsiteCacheRepository",
    # DTOs
    "FetchRequest",
    "FetchResult",
    "DetectMainContentRequest",
    "DetectMainContentResult",
    "DetectNavigationRequest",
    "DetectNavigationResult",
    "DetectOrderRequest",
    "DetectOrderResult",
    "BuildMarkdownRequest",
    "BuildMarkdownResult",
    "BuildPdfRequest",
    "BuildPdfResult",
    "PipelineRequest",
    "PipelineResult",
    # Errors
    "FetchError",
    "NetworkError",
    "InvalidURLError",
    "CachePermissionError",
    "DetectError",
    "BuildError",
    "PipelineError",
]
```

### Step 7: services.pyの削除

```bash
rm src/site2/core/ports/services.py
```

### Step 8: テストファイルの更新

```python
# tests/mocks/services.py のimportを更新

# 変更前:
from site2.core.ports.services import IFetchService, IDetectService, IBuildService

# 変更後:
from site2.core.ports import IFetchService, IDetectService, IBuildService
```

### Step 9: 統合テストの更新

detect_orderとbuild_markdownの呼び出し部分が、新しいシグネチャに対応しているか確認。

## 実装時の注意事項

1. **DTOベースのインターフェース**：
   - build_contracts.pyなど、一部はDTOベースの設計
   - パラメータ追加はDTOに含めるか、メソッドシグネチャに追加するか検討が必要

2. **非同期メソッド**：
   - 一部のProtocolでasyncが抜けている可能性
   - 統一的にasync/awaitを使用

3. **エラーハンドリング**：
   - 各contractsのエラー定義は保持
   - 統一的なエラー階層を維持

4. **後方互換性**：
   - 既存のテストが動作することを確認
   - 段階的な移行を心がける

これらの変更により、インターフェース定義が統一され、保守性が向上します。
