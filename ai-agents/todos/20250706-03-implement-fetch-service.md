# Todo 03: Fetchサービスの実装

## 目的

Webサイトを取得してキャッシュするFetchサービスを実装する。

## 背景

FetchServiceは、site2の最初のステップとして、URLからWebサイトのコンテンツを取得し、ローカルにキャッシュする責務を持つ。

## 成果物

1. **FetchService実装**
   - `src/site2/core/use_cases/fetch_use_case.py`
   - FetchServiceProtocolの実装

2. **WgetCrawler実装**
   - `src/site2/adapters/crawlers/wget_crawler.py`
   - WebCrawlerProtocolの実装

3. **FileRepository実装**
   - `src/site2/adapters/storage/file_repository.py`
   - WebsiteCacheRepositoryProtocolの実装

## 実装詳細

### 1. FetchService

```python
# src/site2/core/use_cases/fetch_use_case.py

class FetchService:
    def __init__(
        self,
        crawler: WebCrawlerProtocol,
        repository: WebsiteCacheRepositoryProtocol,
        cache_dir: Path = Path.home() / ".cache" / "site2"
    ):
        self.crawler = crawler
        self.repository = repository
        self.cache_dir = cache_dir

    def fetch(self, request: FetchRequest) -> FetchResult:
        """
        Webサイトをフェッチしてキャッシュ

        1. URLの検証
        2. 既存キャッシュの確認
        3. クローリング実行
        4. キャッシュ保存
        5. 結果の返却
        """
```

### 2. WgetCrawler

```python
# src/site2/adapters/crawlers/wget_crawler.py

class WgetCrawler:
    def crawl(
        self,
        url: WebsiteURL,
        depth: CrawlDepth,
        existing_cache: Optional[WebsiteCache] = None
    ) -> List[CachedPage]:
        """
        wgetを使用してWebサイトをクロール

        wgetオプション:
        - -r: 再帰的
        - -l: 深さ制限
        - -k: リンクをローカル用に変換
        - -E: 適切な拡張子
        - -np: 親ディレクトリを辿らない
        """
```

### 3. FileRepository

```python
# src/site2/adapters/storage/file_repository.py

class FileRepository:
    def save(self, cache: WebsiteCache) -> None:
        """キャッシュをファイルシステムに保存"""

    def find_by_url(self, url: WebsiteURL) -> Optional[WebsiteCache]:
        """URLでキャッシュを検索"""

    def find_all(self) -> List[WebsiteCache]:
        """すべてのキャッシュを取得"""
```

## テスト要件

### 単体テスト

- [ ] FetchServiceのテスト
  - [ ] 新規サイトのフェッチ
  - [ ] キャッシュ済みサイトの更新
  - [ ] エラーハンドリング

- [ ] WgetCrawlerのテスト
  - [ ] wgetコマンドの構築
  - [ ] 出力の解析
  - [ ] エラー処理

- [ ] FileRepositoryのテスト
  - [ ] 保存と読み込み
  - [ ] メタデータの永続化

### 統合テスト

- [ ] ローカルサーバーでの実際のフェッチ
- [ ] キャッシュの永続性確認

## 実装のポイント

1. **wgetの呼び出し**
   - subprocessを使用
   - 標準出力・エラーの適切な処理
   - タイムアウト設定

2. **キャッシュ構造**
   ```
   ~/.cache/site2/
   └── example.com_a1b2c3d4/
       ├── cache.json      # メタデータ
       ├── index.html
       ├── about.html
       └── assets/
           └── style.css
   ```

3. **差分更新**
   - Last-Modifiedヘッダーの確認
   - ETagの利用
   - 強制更新オプション

## 受け入れ基準

- [ ] すべてのテストがパス
- [ ] 契約（Protocol）に準拠
- [ ] エラーハンドリングが適切
- [ ] ログ出力が適切

## 推定工数

4-6時間

## 依存関係

- [01. 設計ドキュメントの完成](20250706-01-complete-design-docs.md)
- [02. 共通インフラストラクチャの実装](20250706-02-common-infrastructure.md)

## 次のタスク

→ [04. HTMLパーサーの実装](20250706-04-implement-html-parser.md)

## AIへの実装依頼例

```
以下の契約に基づいてFetchServiceを実装してください：

契約定義:
- src/site2/core/ports/fetch_contracts.py

要件:
1. FetchServiceProtocolを実装
2. 依存性注入を使用
3. 適切なエラーハンドリング
4. ログ出力（loguru使用）

テストケース:
- tests/unit/core/use_cases/test_fetch_use_case.py

制約:
- wgetは必ずsubprocessで呼び出す
- キャッシュディレクトリは設定可能
- 並行ダウンロードは3接続まで
```
