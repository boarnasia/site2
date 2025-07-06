# タスク18 実行プロンプト（ドメインイベントテスト）

以下の内容をAIエージェントにコピー＆ペーストして実行を開始してください。

---

# タスク実行指示

## 役割設定
あなたはCommander（統括者）として、以下のタスクを管理してください。
必要に応じてWorker（作業者）の役割に切り替えて実装を行ってください。

## 実行するタスク
タスク18: ドメインイベントのテスト実装
ai-agents/todos/20250706-18-implement-domain-events-tests.md

## プロジェクト情報
- リポジトリ: https://github.com/boarnasia/site2
- ブランチ: 20250706-01-initial-work
- 対象ファイル: tests/unit/core/domain/test_fetch_domain.py

## 実行手順
1. タスクファイルを読み込んで内容を理解
2. 既存のテストファイルを確認
3. ドメインイベントの実装を確認（fetch_domain.py）
4. テストケースの設計
5. Worker役としてテストを実装
6. 完了報告

## 実装するテストクラス

```python
class TestDomainEvents:
    """ドメインイベントのテスト"""

    def test_page_fetched_event_creation()
    def test_page_fetched_event_validation()
    def test_cache_created_event_creation()
    def test_cache_created_event_validation()
    def test_cache_updated_event_creation()
    def test_cache_updated_event_validation()
    def test_event_timestamp_auto_generation()
    def test_event_immutability()
```

## テストケースの内容

### PageFetchedイベント
- 正常な作成
- website_cache_idの空文字チェック
- page_urlの形式チェック
- size_bytesの負の値チェック
- タイムスタンプの自動生成

### CacheCreatedイベント
- 正常な作成
- website_cache_idの空文字チェック
- root_urlの形式チェック
- タイムスタンプの自動生成

### CacheUpdatedイベント
- 正常な作成
- website_cache_idの空文字チェック
- updated_pagesの負の値チェック
- タイムスタンプの自動生成

## 制約事項
- Pydanticのバリデーションを活用
- 既存のテストスタイルに合わせる
- pytest.raisesでValidationErrorをキャッチ
- わかりやすいテスト名とコメント

## 品質チェックリスト
- [ ] すべてのドメインイベントがテストされている
- [ ] 正常系と異常系の両方をカバー
- [ ] タイムスタンプの自動生成を確認
- [ ] Pydanticのバリデーションが機能している
- [ ] テストが独立して実行可能

開始してください。まず、Commanderとして現在のテストカバレッジを分析してください。
