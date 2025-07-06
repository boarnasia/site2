# Todo 18: ドメインイベントのテスト実装

## 目的

fetch_domain.pyで定義されているドメインイベント（PageFetched, CacheCreated, CacheUpdated）のテストを実装する。

## 背景

タスク01でドメインイベントが実装されたが、対応するテストが未実装のまま残っている。これは実装漏れと判断し、テストを追加する。

## 成果物

1. **test_fetch_domain.pyへの追加テスト**
   - PageFetchedのテスト
   - CacheCreatedのテスト
   - CacheUpdatedのテスト

## 実装詳細

### テストケース

```python
class TestDomainEvents:
    """ドメインイベントのテスト"""

    def test_page_fetched_event():
        """PageFetchedイベントの作成と検証"""
        # 正常系
        # タイムスタンプ自動設定
        # 必須フィールドの検証

    def test_cache_created_event():
        """CacheCreatedイベントの作成と検証"""
        # 正常系
        # タイムスタンプ自動設定
        # URLフォーマット検証

    def test_cache_updated_event():
        """CacheUpdatedイベントの作成と検証"""
        # 正常系
        # updated_pagesの検証（負の値チェック）
```

## テスト内容

1. **基本的な作成テスト**
   - 各イベントが正しく作成できること
   - デフォルト値（timestamp）が設定されること

2. **バリデーションテスト**
   - 不正な値での作成が失敗すること
   - Pydanticのバリデーションが機能すること

3. **イベントの不変性テスト**
   - 作成後に値が変更できないこと（Pydanticのfrozen相当）

## 受け入れ基準

- [ ] すべてのドメインイベントにテストがある
- [ ] 正常系と異常系の両方をカバー
- [ ] カバレッジ100%

## 推定工数

1-2時間

## 依存関係

- fetch_domain.pyのドメインイベント実装が完了していること
