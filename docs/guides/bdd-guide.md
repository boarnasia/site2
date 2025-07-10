# BDD (Behavior-Driven Development) ガイド

## 概要

site2プロジェクトでは、pytest-bddを使用してBDD（振る舞い駆動開発）を実践しています。
このガイドでは、pytest-bddの使い方とベストプラクティスを説明します。

## なぜpytest-bddを選んだのか

- **pytestとの完全な統合**: 既存のpytestインフラをそのまま活用
- **明示的なステップ定義**: デコレータベースで曖昧さがない
- **優れたIDEサポート**: 関数ジャンプ、リファクタリングが可能
- **fixtureの共有**: pytestのfixtureシステムをフル活用

## ディレクトリ構造

```
tests/
├── features/              # BDDテスト
│   ├── fetch.feature     # fetchコマンドのシナリオ
│   ├── test_fetch.py     # fetchのステップ定義
│   ├── tutorial.feature  # チュートリアル（参考用）
│   └── test_tutorial.py  # チュートリアルのステップ定義
├── fixtures/             # テストデータ
│   └── websites/         # キャッシュされたWebサイト
├── unit/                 # 単体テスト
├── integration/          # 統合テスト
└── e2e/                  # E2Eテスト
```

## 基本的な使い方

### 1. Featureファイルの作成

`tests/features/example.feature`:
```gherkin
# language: ja
機能: 機能の説明
  ユーザーとして
  〜がしたい
  なぜなら〜だから

  背景:
    Given 共通の前提条件

  シナリオ: シナリオ名
    前提 前提条件
    もし アクション
    ならば 期待結果
```

### 2. ステップ定義の作成

`tests/features/test_example.py`:
```python
import pytest
from pytest_bdd import scenario, given, when, then, parsers

# シナリオをバインド
@scenario("example.feature", "シナリオ名")
def test_scenario():
    pass

# ステップ定義
@given("前提条件")
def setup_condition():
    # セットアップ処理
    pass

@when("アクション")
def perform_action():
    # アクション実行
    pass

@then("期待結果")
def verify_result():
    # 検証
    assert True
```

### 3. パラメータ化されたステップ

```python
@given(parsers.parse('数値 {x:d} と {y:d} を入力する'))
def input_numbers(x, y):
    return x, y

@then(parsers.parse('結果は {expected:d} である'))
def check_result(result, expected):
    assert result == expected
```

### 4. テーブルデータの使用

```gherkin
Given 以下のユーザーが存在する:
  | name  | email           | role  |
  | Alice | alice@test.com  | admin |
  | Bob   | bob@test.com    | user  |
```

```python
@given("以下のユーザーが存在する:")
def create_users(datatable):
    for row in datatable:
        create_user(
            name=row["name"],
            email=row["email"],
            role=row["role"]
        )
```

## Fixtureの活用

### 共有Fixture

`tests/conftest.py`:
```python
@pytest.fixture
def test_server():
    """テスト用HTTPサーバー"""
    # サーバー起動
    yield server
    # クリーンアップ

@pytest.fixture
def cache_dir(tmp_path):
    """テスト用キャッシュディレクトリ"""
    return tmp_path / "cache"
```

### ステップ間での状態共有

```python
@pytest.fixture
def context():
    """ステップ間で状態を共有"""
    return {}

@when("ファイルをダウンロード")
def download_file(context):
    context["file"] = download()

@then("ファイルが存在する")
def check_file(context):
    assert context["file"].exists()
```

## テストの実行

### 基本的な実行

```bash
# すべてのBDDテストを実行
pytest tests/features -v

# 特定のfeatureを実行
pytest tests/features/test_fetch.py -v

# 特定のシナリオを実行
pytest -k "新規サイトのフェッチ" -v
```

### マーカーを使った実行

```python
@pytest.mark.slow
@scenario("fetch.feature", "大規模サイトのフェッチ")
def test_large_site_fetch():
    pass
```

```bash
# slowマーカーを除外
pytest -m "not slow"

# BDDテストのみ実行
pytest -m bdd
```

### カバレッジ付き実行

```bash
pytest tests/features --cov=src/site2 --cov-report=html
```

## ベストプラクティス

### 1. シナリオは具体的に

```gherkin
# ❌ 悪い例：曖昧
Then 正しく動作する

# ✅ 良い例：具体的
Then 終了コード 0 で正常終了する
And 標準出力に "✅ Fetched: https://example.com" を含む
```

### 2. ステップの再利用

共通のステップは`conftest.py`や共通モジュールに定義：

```python
# tests/features/common_steps.py
@given("ネットワーク接続が利用可能である")
def network_available():
    # 共通実装
```

### 3. 独立したテスト

各シナリオは独立して実行可能にする：

```python
@pytest.fixture(autouse=True)
def cleanup():
    yield
    # テスト後のクリーンアップ
```

### 4. 適切なアサーション

```python
# ❌ 悪い例：エラーメッセージなし
assert result == expected

# ✅ 良い例：分かりやすいエラーメッセージ
assert result == expected, f"Expected {expected}, but got {result}"
```

## デバッグのコツ

### 1. ステップのプリント

```python
@when("コマンドを実行")
def execute_command(command):
    print(f"Executing: {command}")  # -s オプションで表示
    result = run_command(command)
    print(f"Result: {result}")
    return result
```

### 2. ブレークポイント

```python
@then("結果を検証")
def verify_result(result):
    import pdb; pdb.set_trace()  # デバッガ起動
    assert result.success
```

### 3. 詳細なエラー出力

```bash
pytest tests/features -vv --tb=long
```

## 高度な使い方

### Scenario Outline

```gherkin
Scenario Outline: 複数のケースをテスト
  When <input> を処理する
  Then 結果は <output> である

  Examples:
    | input | output |
    | 1     | 2      |
    | 2     | 4      |
    | 3     | 6      |
```

### カスタムパーサー

```python
from pytest_bdd import parsers

# カスタム型変換
@parsers.cfparse("{size:FileSize}")
def parse_file_size(text):
    """1.2 MB -> bytes"""
    # 実装
```

### 非同期テスト

```python
import pytest
import asyncio

@pytest.mark.asyncio
@when("非同期処理を実行")
async def async_action():
    result = await async_operation()
    return result
```

## トラブルシューティング

### よくある問題

1. **ステップが見つからない**
   - ステップの文言が完全一致しているか確認
   - parsersを使う場合は正しいパターンか確認

2. **Fixtureが注入されない**
   - Fixtureの名前が正しいか確認
   - conftest.pyの配置場所を確認

3. **日本語の文字化け**
   - ファイルのエンコーディングがUTF-8か確認
   - `# language: ja` をfeatureファイルに追加

## 参考リンク

- [pytest-bdd公式ドキュメント](https://pytest-bdd.readthedocs.io/)
- [Gherkin構文リファレンス](https://cucumber.io/docs/gherkin/)
- [pytestドキュメント](https://docs.pytest.org/)
