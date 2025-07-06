# タスク17 実行プロンプト（Pydantic移行）

以下の内容をAIエージェントにコピー＆ペーストして実行を開始してください。

---

# タスク実行指示

## 役割設定
あなたはCommander（統括者）として、以下のタスクを管理してください。
必要に応じてWorker（作業者）の役割に切り替えて実装を行ってください。

## 実行するタスク
タスク17: ドメインモデルのPydantic移行
ai-agents/todos/20250706-17-migrate-to-pydantic.md

## プロジェクト情報
- リポジトリ: https://github.com/boarnasia/site2
- ブランチ: 20250706-01-initial-work
- 参考実装: src/site2/core/domain/fetch_domain.py（Pydantic実装済み）

## 実行手順
1. タスクファイルを読み込んで内容を理解
2. 既存ファイルの確認：
   - src/site2/core/domain/fetch_domain.py（参考）
   - src/site2/core/domain/detect_domain.py（移行対象）
   - src/site2/core/domain/build_domain.py（移行対象）
3. Pydantic移行の計画立案
4. Worker役として各ファイルを更新
5. テストの互換性確認
6. 完了報告

## 具体的な変更内容

### detect_domain.py
1. pydanticからBaseModel, Field, ConfigDictをインポート
2. @dataclassデコレータを削除
3. BaseModelを継承
4. Field制約を追加（min_length, ge, le等）
5. ConfigDict(frozen=True)を設定
6. __post_init__をvalidatorまたはmodel_validatorに変更

### build_domain.py
1. 同様の変更を適用
2. Enumは変更不要（Pydanticと互換）
3. field(default_factory=list) → Field(default_factory=list)
4. Optional型の明確化

## 制約事項
- fetch_domain.pyのスタイルに合わせる
- 既存のインターフェースは変更しない
- バリデーションは強化するが、既存の動作は維持
- テストが全てパスすること

## 品質チェックリスト
- [ ] すべてのdataclassがBaseModelに変換されている
- [ ] 適切なField制約が追加されている
- [ ] frozen設定が維持されている
- [ ] 既存テストがパスする
- [ ] インポートが整理されている

開始してください。まず、Commanderとして移行計画を分析してください。
