# Todo 17: ドメインモデルのPydantic移行

## 目的

fetch_domainで実装されたPydanticベースのドメインモデルに合わせて、他のドメインモデルもPydanticに移行する。

## 背景

現在、fetch_domain.pyはPydantic BaseModelを使用しているが、detect_domain.pyとbuild_domain.pyはまだdataclassを使用している。統一性とバリデーション機能の向上のため、すべてPydanticに移行する。

## 成果物

1. **detect_domain.pyのPydantic化**
   - dataclassからBaseModelへ
   - 適切なバリデーション追加
   - frozen設定の適用

2. **build_domain.pyのPydantic化**
   - dataclassからBaseModelへ
   - Enum対応
   - 適切なバリデーション追加

3. **テストの更新**
   - ValidationError対応
   - Pydantic特有の動作確認

## 実装詳細

### detect_domain.pyの変更点

```python
# Before (dataclass)
@dataclass(frozen=True)
class SelectorCandidate:
    selector: str
    score: float

# After (Pydantic)
class SelectorCandidate(BaseModel):
    selector: str = Field(..., min_length=1)
    score: float = Field(..., ge=0.0, le=1.0)

    model_config = ConfigDict(frozen=True)
```

### build_domain.pyの変更点

```python
# Before (dataclass)
@dataclass(frozen=True)
class ContentFragment:
    content_type: ContentType
    raw_content: str

# After (Pydantic)
class ContentFragment(BaseModel):
    content_type: ContentType
    raw_content: str = Field(..., min_length=1)

    model_config = ConfigDict(frozen=True)
```

## 移行のポイント

1. **バリデーション強化**
   - Field制約の追加
   - カスタムバリデータの実装

2. **互換性維持**
   - __post_init__ → model_post_init
   - field(default_factory=list) → Field(default_factory=list)

3. **型の厳密化**
   - Optional型の明示
   - Union型の適切な使用

## テスト要件

- [x] ValidationErrorの適切なハンドリング
- [x] 既存テストの互換性確認
- [x] 新規バリデーションのテスト追加

## 推定工数

2-3時間

## 依存関係

なし（独立したリファクタリング）
