# タスク実行指示: 共通インフラストラクチャの実装 (dependency-injector版)

## 役割設定
あなたはCommander（統括者）として、以下のタスクを管理してください。
必要に応じてWorker（作業者）の役割に切り替えて実装を行ってください。

## 実行するタスク
**タスク02**: 共通インフラストラクチャの実装 (dependency-injector版)
**タスクファイル**: `ai-agents/todos/20250706-02-common-infrastructure.md` (修正版適用)

## プロジェクト情報
- **リポジトリ**: https://github.com/boarnasia/site2
- **メインブランチ**: main
- **作業ブランチ**: 20250713-work (ローカル作業用)

## 実行手順

### Phase 1: 事前調査・準備（Commander役）
1. **依存関係の確認**: 現在のpyproject.tomlを確認し、必要な依存関係を特定
2. **プロジェクト構造調査**: src/site2/の現在の構造を把握
3. **task19完了状況確認**: contractsのPydantic移行状況を確認
4. **設計方針策定**: dependency-injectorを使用したDI設計の詳細化

### Phase 2: 依存関係とプロジェクト構造準備（Worker役）
5. **pyproject.toml更新**:
   - `dependency-injector>=4.40.0`
   - `pydantic-settings>=2.0.0`
   - `loguru>=0.7.0`
   の追加
6. **ディレクトリ構造作成**:
   - `src/site2/config/`
   - `src/site2/core/utils/`
   等の必要なディレクトリを作成

### Phase 3: 設定管理システム実装（Worker役）
7. **設定クラス実装**: `src/site2/config/settings.py`
   - pydantic-settingsベースのSettings実装
   - 環境変数サポート
   - バリデーション付きの設定項目定義
8. **設定テスト作成**: `tests/unit/config/test_settings.py`

### Phase 4: DIコンテナ実装（Worker役）
9. **メインコンテナ実装**: `src/site2/core/containers.py`
   - dependency-injectorベースのContainer実装
   - プレースホルダーでのサービス定義
   - TestContainerの実装
10. **アプリケーション初期化**: `src/site2/app.py`
    - create_app関数の実装
    - ワイヤリング設定

### Phase 5: ログシステム実装（Worker役）
11. **ログ設定実装**: `src/site2/core/logging.py`
    - loguru使用のセットアップ関数
    - ファイル出力対応
    - デバッグモード対応

### Phase 6: 共通ユーティリティ実装（Worker役）
12. **URLユーティリティ**: `src/site2/core/utils/url_utils.py`
    - URL解決、ファイル名変換、ドメイン判定
13. **ファイルユーティリティ**: `src/site2/core/utils/file_utils.py`
    - アトミックファイル操作、ハッシュ計算、安全なコピー
14. **ユーティリティテスト**: 各ユーティリティの単体テスト作成

### Phase 7: 統合テストと検証（Commander役）
15. **統合テスト実行**: DIコンテナの完全な動作確認
16. **設定システムテスト**: 環境変数での設定上書き確認
17. **ログシステムテスト**: ログ出力の動作確認
18. **完了報告**: 実装内容とテスト結果の総括

## 技術的制約・注意事項

### 必須要件
- **dependency-injector v4.40.0以上を使用**
- **段階的実装でプレースホルダーを活用**
- **テスト用コンテナで本番用から分離**
- **Clean Architectureの原則維持**

### 実装パターン（重要）
```python
# DIコンテナの基本パターン
class Container(containers.DeclarativeContainer):
    # 設定
    settings = providers.Singleton(Settings)

    # プレースホルダー（実装完了時に置き換え）
    fetch_service = providers.Factory(
        providers.Object("placeholder"),  # 一時的
        # FetchService,  # 将来実装時に有効化
    )

# 依存性注入の使用パターン
@inject
def some_function(
    service: Protocol = Provide[Container.service],
) -> None:
    pass
```

### 段階的実装の方針
1. **骨組み優先**: 基本構造を先に完成
2. **プレースホルダー活用**: 後続実装への準備
3. **テスト駆動**: 各実装に対応するテスト作成
4. **設定外部化**: 環境による動作変更を可能に

## 品質チェックリスト

### 機能要件
- [ ] dependency-injectorが正しく設定されている
- [ ] 環境変数で設定を上書きできる
- [ ] DIコンテナが適切にワイヤリングされる
- [ ] ログシステムが正常動作する
- [ ] ユーティリティ関数が堅牢である

### 品質要件
- [ ] 型チェック（mypy）エラーなし
- [ ] すべてのテストがパス
- [ ] コードカバレッジ80%以上
- [ ] アトミックなファイル操作が実装されている

### 設計要件
- [ ] テスト用コンテナが本番用から独立している
- [ ] 設定の階層化が適切である
- [ ] 依存関係の循環がない
- [ ] 後続実装への拡張性がある

### セキュリティ要件
- [ ] ファイル操作が安全（アトミック）
- [ ] 機密情報の適切な管理
- [ ] パストラバーサル対策

## 成果物要件

### 実装ファイル
- `src/site2/config/settings.py` - 設定管理
- `src/site2/core/containers.py` - DIコンテナ
- `src/site2/app.py` - アプリケーション初期化
- `src/site2/core/logging.py` - ログシステム
- `src/site2/core/utils/url_utils.py` - URLユーティリティ
- `src/site2/core/utils/file_utils.py` - ファイルユーティリティ

### テストファイル
- `tests/unit/config/test_settings.py`
- `tests/unit/core/test_containers.py`
- `tests/unit/core/utils/test_url_utils.py`
- `tests/unit/core/utils/test_file_utils.py`
- `tests/integration/test_app_initialization.py`

### 設定ファイル
- `pyproject.toml` (依存関係更新)
- `.env.example` (設定例)

## 検証方法

### 単体テスト実行
```bash
pytest tests/unit/config/ -v
pytest tests/unit/core/utils/ -v
pytest tests/unit/core/test_containers.py -v
```

### 統合テスト実行
```bash
pytest tests/integration/test_app_initialization.py -v
```

### 型チェック実行
```bash
mypy src/site2/config/ src/site2/core/ src/site2/app.py
```

## リスク対策

### 技術的リスク
- **dependency-injectorバージョン互換性**: 最新安定版使用
- **循環依存**: 設計段階での依存関係図作成
- **テスト分離**: TestContainerでの完全分離

### 実装リスク
- **段階的コミット**: 機能単位での細かいコミット
- **後方互換性**: 既存コードへの影響最小化
- **ドキュメント**: 設定項目の詳細記録

---

**実行前確認事項:**
- [ ] task19（契約定義のPydantic移行）が完了している
- [ ] main branchが最新状態である
- [ ] 作業ブランチ(20250713-work)が準備されている

**開始してください。**
