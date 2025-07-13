# Task 22: インターフェース定義の統合と整理

## 背景
現在、インターフェース定義が以下の2箇所に分散している：
1. `src/site2/core/ports/services.py` - シンプルなProtocol定義
2. `src/site2/core/ports/*_contracts.py` - 詳細な契約定義（DTO、エラー含む）

クリーンアーキテクチャの統合型アプローチを採用し、`*_contracts.py`に統一する。

## 目的
- インターフェース定義の重複を解消
- Contract-First開発の原則に従った統一的な契約管理
- 保守性と可読性の向上

## 実装内容

### 1. services.pyの削除と移行
- `src/site2/core/ports/services.py`を削除
- Task 21で追加した以下の変更を各contracts.pyに反映：
  - `DetectServiceProtocol.detect_order`にNavigationパラメータ追加
  - `BuildServiceProtocol.build_markdown`にDocumentOrderパラメータ追加

### 2. Protocol命名規則の統一
以下のいずれかに統一（チーム決定待ち）：
- 案A: `IFetchService`（Iプレフィックス）
- 案B: `FetchServiceProtocol`（現状維持）

**決定**: `IFetchService`（Iプレフィックス）を採用

### 3. contracts.pyファイルの更新

#### fetch_contracts.py
```python
# 変更前: class FetchServiceProtocol(Protocol):
# 変更後: class IFetchService(Protocol):
```

#### detect_contracts.py
```python
# 変更前: class DetectServiceProtocol(Protocol):
# 変更後: class IDetectService(Protocol):

# detect_orderメソッドの更新
async def detect_order(
    self,
    cache_dir: Path,
    navigation: Navigation  # Task 21で追加
) -> DocumentOrder:
```

#### build_contracts.py
```python
# 変更前: class BuildServiceProtocol(Protocol):
# 変更後: class IBuildService(Protocol):

# build_markdownメソッドの更新
async def build_markdown(
    self,
    contents: List[MainContent],
    doc_order: DocumentOrder  # Task 21で追加
) -> MarkdownDocument:
```

### 4. 影響範囲の確認と修正
- テストコードのimport文を更新
- モックサービスのimport文を更新
- 将来の実装で参照する箇所の確認

### 5. __init__.pyの整備
`src/site2/core/ports/__init__.py`に主要なインターフェースをexport：
```python
from .fetch_contracts import IFetchService, IWebCrawler, IWebsiteCacheRepository
from .detect_contracts import IDetectService
from .build_contracts import IBuildService
from .pipeline_contracts import IPipelineService

__all__ = [
    "IFetchService",
    "IWebCrawler",
    "IWebsiteCacheRepository",
    "IDetectService",
    "IBuildService",
    "IPipelineService",
]
```

## 成功基準
- [ ] services.pyが削除されている
- [ ] 全てのProtocolがIプレフィックスで統一されている
- [ ] Task 21の変更が反映されている
- [ ] テストが全て成功する
- [ ] importが整理されている

## 注意事項
- 既存のテストを壊さないよう慎重に作業
- 各contracts.pyの構造（DTO→Protocol→Error）は維持
- docstringの契約記述は保持

## 期待される成果物
1. 更新された`*_contracts.py`ファイル群
2. 削除された`services.py`
3. 更新された`__init__.py`
4. 必要に応じて更新されたテストファイル
