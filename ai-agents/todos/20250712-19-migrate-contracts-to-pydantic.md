# Task: 契約定義（Contracts）のPydantic移行

## タスク概要

site2プロジェクトの契約定義（src/site2/core/ports/）で使用されているIO-Interfaceの@dataclassをPydanticのBaseModelに移行する。

## 背景

- site2プロジェクトはdataclassからPydanticへの移行を進行中
- fetchドメインは移行完了済み
- detect/buildドメインは移行中
- 契約定義（contracts）のIO-Interfaceも移行が必要

## 対象ファイル

以下のファイルの@dataclass定義をPydanticに移行：

1. `src/site2/core/ports/fetch_contracts.py` - ✅ **移行完了確認済み**
2. `src/site2/core/ports/detect_contracts.py` - 🔄 **移行対象**
3. `src/site2/core/ports/build_contracts.py` - 🔄 **移行対象**
4. `src/site2/core/ports/parser_contracts.py` - 🔄 **移行対象**
5. `src/site2/core/ports/pipeline_contracts.py` - 🔄 **移行対象**

## 移行対象クラス詳細

### detect_contracts.py
- `DetectMainRequest`
- `SelectorCandidate`
- `DetectMainResult`
- `DetectNavRequest`
- `NavLink`
- `DetectNavResult`
- `DetectOrderRequest`
- `OrderedFile`
- `DetectOrderResult`

### build_contracts.py
- `BuildRequest`
- `ExtractedContent`
- `BuildResult`
- `ConvertRequest`
- `MarkdownConvertRequest`
- `PDFConvertRequest`
- `ConvertResult`

### parser_contracts.py
- 確認必要（ファイル内容を調査）

### pipeline_contracts.py
- 確認必要（ファイル内容を調査）

## 作業方針

### 段階的実装
1. **Phase 1**: detect_contracts.pyの移行
2. **Phase 2**: build_contracts.pyの移行
3. **Phase 3**: parser_contracts.py、pipeline_contracts.pyの移行
4. **Phase 4**: テスト修正とドキュメント更新

### Commander/Worker分担
- **Commander**: 移行方針策定、設計レビュー、統合テスト
- **Worker**: 実装作業、単体テスト作成、ドキュメント更新

## 技術要件

### Pydantic移行パターン
```python
# Before (dataclass)
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class DetectMainRequest:
    file_path: Path

    def validate(self) -> None:
        assert self.file_path.exists(), f"File must exist: {self.file_path}"

# After (Pydantic)
from pydantic import BaseModel, field_validator, ConfigDict
from typing import List, Optional

class DetectMainRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: Path

    @field_validator('file_path')
    @classmethod
    def validate_file_exists(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"File must exist: {v}")
        return v
```

### 重要な変更点
1. **import変更**: `from dataclasses import dataclass` → `from pydantic import BaseModel`
2. **クラス定義**: `@dataclass` → `class ClassName(BaseModel):`
3. **設定追加**: `model_config = ConfigDict(arbitrary_types_allowed=True)` (Pathなど使用時)
4. **バリデーション**: `validate()`メソッド → `@field_validator`デコレータ
5. **デフォルト値**: `field(default_factory=list)` → `Field(default_factory=list)` または単純に `= []`

### 型安全性の向上
- Enumの活用（OutputFormatなど）
- Union型の適切な使用
- Optional型の明確化
- 制約付きバリデーション（範囲チェックなど）

## 品質要件

### テスト要件
- 既存テストの継続動作
- Pydanticバリデーションのテスト追加
- エラーケースのテスト強化

### 互換性要件
- 既存のProtocol定義との互換性維持
- ドメインモデルとの連携保持
- CLI契約との整合性確保

### パフォーマンス要件
- バリデーション性能の最適化
- メモリ使用量の監視

## 成果物

### 修正ファイル
- `src/site2/core/ports/detect_contracts.py`
- `src/site2/core/ports/build_contracts.py`
- `src/site2/core/ports/parser_contracts.py`
- `src/site2/core/ports/pipeline_contracts.py`

### テストファイル
- 既存テストの修正
- 新規バリデーションテストの追加

### ドキュメント
- 移行ログ（変更点の記録）
- アップデートされたcontract仕様

## 検証基準

### 機能検証
- [ ] すべてのIO-Interfaceクラスがpydantic.BaseModelを継承
- [ ] バリデーション機能が正常動作
- [ ] 既存のProtocolとの互換性維持
- [ ] エラーハンドリングの改善

### 品質検証
- [ ] 型チェック（mypy）エラーなし
- [ ] 既存テストがすべてパス
- [ ] 新規バリデーションテストの追加
- [ ] コードカバレッジの維持・向上

### 設計検証
- [ ] Clean Architectureの原則維持
- [ ] Contract-First Developmentの方針継続
- [ ] ドメインモデルとの整合性確保

## 優先度・スケジュール

### Priority: **High**
- detect/buildドメインの実装に影響するため

### 推定工数: **3-4日**
- Phase 1 (detect): 1日
- Phase 2 (build): 1日
- Phase 3 (parser/pipeline): 1日
- Phase 4 (test/doc): 1日

### 前提条件
- Pydanticライブラリの追加済み
- ドメインモデルのPydantic移行完了

### 依存関係
- 後続タスク: 各サービス実装（detect, build等）
- 並行可能: ドメインイベントテスト追加

## 実行手順

### Step 1: 事前調査
1. parser_contracts.py、pipeline_contracts.pyの内容確認
2. 現在のテスト状況調査
3. 依存関係の洗い出し

### Step 2: detect_contracts.py移行
1. @dataclassをBaseModelに変更
2. バリデーションロジックの移行
3. テストの修正・追加
4. 動作確認

### Step 3: build_contracts.py移行
1. 同様の移行作業
2. Enum (OutputFormat) の確認
3. 複雑なバリデーションの実装
4. テスト修正

### Step 4: 残りファイルの移行
1. parser_contracts.py移行
2. pipeline_contracts.py移行
3. 統合テスト実行

### Step 5: 完了確認
1. 全テスト実行
2. 型チェック実行
3. ドキュメント更新
4. レビュー・承認

## 参考資料

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [既存のfetch_domain.py実装](src/site2/core/domain/fetch_domain.py)
- [プロジェクト移行方針](AI_CODING_CONTEXT.md)
- [BDD開発ガイド](docs/testing/bdd-guide.md)

## 注意事項

### 重要な制約
- 既存のProtocol定義は変更しない
- CLI契約(contracts/cli-contract.yaml)との整合性維持
- 段階的移行でテストを継続実行

### リスク要因
- バリデーションロジックの複雑化
- 既存テストの大幅修正が必要な可能性
- 型推論の変更による影響

### 対策
- 小さな変更での段階的コミット
- 各段階でのテスト実行
- バックアップとしてブランチ作成
