# Todo 01: 設計ドキュメントの完成

## 目的

パイプライン全体の設計を完成させ、実装の指針を明確にする。

## 背景

現在、基本的な設計は存在するが、各コンポーネント間のデータフローや詳細な仕様が不足している。

## 成果物

1. **パイプライン設計書** ✓
   - `docs/architecture/pipeline_design.md`
   - 全体のデータフロー
   - 各ステップの入出力仕様

2. **各サービスの契約定義**
   - `src/site2/core/ports/build_contracts.py`
   - `src/site2/core/ports/detect_contracts.py`

3. **ドメインモデルの拡張**
   - `src/site2/core/domain/detect_domain.py`
   - `src/site2/core/domain/build_domain.py`

## タスク詳細

### 1. Detect契約の定義

```python
# src/site2/core/ports/detect_contracts.py

@dataclass
class DetectMainRequest:
    file_path: Path

@dataclass
class DetectMainResult:
    file_path: Path
    selectors: List[str]
    confidence: float
    primary_selector: str

class DetectServiceProtocol(Protocol):
    def detect_main(self, request: DetectMainRequest) -> DetectMainResult:
        """メインコンテンツのセレクタを検出"""

    def detect_nav(self, request: DetectNavRequest) -> DetectNavResult:
        """ナビゲーションのセレクタを検出"""

    def detect_order(self, request: DetectOrderRequest) -> DetectOrderResult:
        """ドキュメントの順序を検出"""
```

### 2. Build契約の定義

```python
# src/site2/core/ports/build_contracts.py

@dataclass
class BuildRequest:
    main_selector: str
    ordered_files: List[OrderedFile]
    format: OutputFormat

@dataclass
class BuildResult:
    content: Union[str, bytes]
    format: OutputFormat
    page_count: int

class BuildServiceProtocol(Protocol):
    def build(self, request: BuildRequest) -> BuildResult:
        """ドキュメントをビルド"""
```

### 3. パイプライン統合契約

```python
# src/site2/core/ports/pipeline_contracts.py

class PipelineServiceProtocol(Protocol):
    """autoコマンドで使用するパイプライン"""

    def execute(self, url: str, format: OutputFormat) -> str:
        """完全なパイプラインを実行"""
```

## 受け入れ基準

- [x] パイプライン設計書が完成している
- [x] すべての契約が定義されている
- [x] 契約にはdocstringで事前条件・事後条件が記載されている
- [x] エラーケースが定義されている
- [x] 型ヒントが完全である

## 実装手順

1. 既存の契約定義を確認
2. 不足している契約を追加
3. ドメインモデルを拡張
4. レビュー用のPRを作成

## 参考資料

- [Contract-First Development](../../docs/development/contract-first.md)
- [Clean Architecture](../../docs/architecture/clean-architecture.md)

## 推定工数

2-3時間

## 依存関係

なし（最初のタスク）

## 次のタスク

→ [02. 共通インフラストラクチャの実装](20250706-02-common-infrastructure.md)
