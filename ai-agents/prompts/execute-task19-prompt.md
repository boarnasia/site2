# タスク実行指示: Contracts Pydantic移行

## 役割設定
あなたはCommander（統括者）として、以下のタスクを管理してください。
必要に応じてWorker（作業者）の役割に切り替えて実装を行ってください。

## 実行するタスク
**タスク19**: 契約定義（Contracts）のPydantic移行
**タスクファイル**: `ai-agents/todos/20250712-19-migrate-contracts-to-pydantic.md`

## プロジェクト情報
- **リポジトリ**: https://github.com/boarnasia/site2
- **メインブランチ**: main
- **作業ブランチ**: 20250712-work2（ローカル作業用）

## 実行手順

### Phase 1: 事前調査・準備（Commander役）
1. **タスクファイル読み込み**: `ai-agents/todos/20250712-19-migrate-contracts-to-pydantic.md`の内容を理解
2. **現状確認**: `src/site2/core/ports/*contracts.py`の全ファイルを調査し、移行対象を特定
3. **参考実装確認**: `src/site2/core/domain/fetch_domain.py`でPydantic実装パターンを確認
4. **テスト状況調査**: 既存のcontractsテストの有無と場所を確認
5. **移行計画策定**: 段階的移行の優先順位と作業順序を決定

### Phase 2: 実装実行（Worker役）
6. **fetch_contracts.py移行**:
   - @dataclass → pydantic.BaseModel
   - validate()メソッド → @field_validator
   - 型安全性の向上
7. **build_contracts.py移行**: 同様の移行作業
8. **残りファイル移行**: detect_contracts.py, parser_contracts.py、pipeline_contracts.py（必要に応じて）
9. **テスト対応**:
   - 既存テストの動作確認
   - contractsテストの分離・独立化
   - Pydanticバリデーションテストの追加

### Phase 3: 品質確認・完了（Commander役）
10. **統合テスト実行**: 全テストがパスすることを確認
11. **型チェック実行**: mypy等での型安全性確認
12. **完了報告**: 変更内容とテスト結果をまとめて報告

## 技術的制約・注意事項

### 必須要件
- **既存のProtocol定義は変更しない**
- **CLI契約(contracts/cli-contract.yaml)との整合性維持**
- **段階的移行でテストを継続実行**
- **Clean Architectureの原則維持**

### 実装パターン（参考）
```python
# 移行前 (dataclass)
@dataclass
class DetectMainRequest:
    file_path: Path
    def validate(self) -> None:
        assert self.file_path.exists()

# 移行後 (Pydantic)
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

## 品質チェックリスト

### 機能要件
- [ ] すべてのIO-InterfaceクラスがPydantic BaseModelを継承
- [ ] バリデーション機能が正常動作（事前条件・事後条件）
- [ ] 既存のProtocolとの互換性維持
- [ ] エラーハンドリングの改善

### 品質要件
- [ ] tests/unit/core/domain/test_fetch_domain.py がパス
- [ ] 新規バリデーションテストの追加
- [ ] テストの独立実行が可能

### 設計要件
- [ ] Contract-First Developmentの方針継続
- [ ] ドメインモデルとの整合性確保
- [ ] 適切なエラーメッセージの提供

## 成果物要件

### コード修正
- 移行対象の全contractsファイル
- 対応するテストファイル

### ドキュメント
- 移行ログ（主要な変更点の記録）
- 破壊的変更がある場合の移行ガイド

## リスク対策
- **小さな変更での段階的コミット**を心がける
- **各段階でテスト実行**して影響を早期発見
- **バックアップブランチ**で安全性を確保

---

**開始してください。**
