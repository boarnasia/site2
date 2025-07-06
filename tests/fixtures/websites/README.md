# Test Fixture Websites

このディレクトリには、テスト用の静的Webサイトデータが格納されます。

## ディレクトリ構成

```
websites/
├── simple-site/          # シンプルなテストサイト（Git管理）
│   ├── index.html
│   ├── about.html
│   ├── style.css
│   └── docs/
│       └── guide.html
└── pytest-bdd-docs/      # wgetでダウンロード（Git管理外）
    ├── index.html
    ├── ...
    └── metadata.json
```

## セットアップ

初回セットアップ時に、以下のコマンドを実行してください：

```bash
# プロジェクトルートから実行
./scripts/prepare_test_fixtures.sh
```

これにより、`pytest-bdd-docs/` ディレクトリにpytest-bddのドキュメントがダウンロードされます。

## なぜFixtureが必要か

1. **安定性**: 外部サイトの変更に影響されない
2. **速度**: ローカルサーバーで高速にテスト
3. **オフライン**: インターネット接続なしでテスト可能
4. **再現性**: 全員が同じデータでテスト

## 使い方

テストでは、`test_server.py`のfixtureを使用します：

```python
def test_with_simple_site(simple_site_server):
    url = simple_site_server.url
    # urlを使ってfetchコマンドをテスト

def test_with_pytest_docs(pytest_bdd_docs_server):
    url = pytest_bdd_docs_server.url
    # pytest-bddドキュメントでテスト
```

## 注意事項

- `pytest-bdd-docs/` はGit管理外です（.gitignoreで除外）
- `simple-site/` はGit管理下です（基本的なテスト用）
- ダウンロードしたデータは定期的に更新してください
