# Todo 03: Fetchサービスの実装

## 目的

Webサイトを取得してキャッシュするFetchサービスを実装する。

## 背景

FetchServiceは、site2の最初のステップとして、URLからWebサイトのコンテンツを取得し、ローカルにキャッシュする責務を持つ。

## 成果物

1. **FetchService実装**
   - `src/site2/core/use_cases/fetch_service.py`
   - FetchServiceProtocolの実装

2. **WgetCrawler実装**
   - `src/site2/adapters/crawlers/wget_crawler.py`
   - WebCrawlerProtocolの実装

3. **FileRepository実装**
   - `src/site2/adapters/storage/file_repository.py`
   - WebsiteCacheRepositoryProtocolの実装（読み取り専用）

## 実装詳細

### 1. FetchService

```python
# src/site2/core/use_cases/fetch_service.py

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

        注意: FetchServiceProtocolは同期メソッドとして定義されている

        1. URLの検証
        2. 既存キャッシュの確認（force_refreshでない場合）
        3. クローリング実行
        4. キャッシュ保存（内部で実行）
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

        注意: CachedPageにはread_text()メソッドがある
        """
```

### 3. FileRepository（読み取り専用）

```python
# src/site2/adapters/storage/file_repository.py

class FileRepository:
    # saveメソッドは実装しない（FetchServiceが内部で保存）

    def find_by_url(self, url: WebsiteURL) -> Optional[WebsiteCache]:
        """URLでキャッシュを検索"""

    def find_all(self) -> List[WebsiteCache]:
        """すべてのキャッシュを取得"""
```

## テスト要件

### 単体テスト

- [ ] FetchServiceのテスト
  - [ ] 新規サイトのフェッチ
  - [ ] キャッシュ済みサイトの確認（force_refresh=False）
  - [ ] 強制更新（force_refresh=True）
  - [ ] エラーハンドリング（NetworkError, InvalidURLError）

- [ ] WgetCrawlerのテスト
  - [ ] wgetコマンドの構築
  - [ ] 出力の解析
  - [ ] CachedPageの生成（read_text()メソッド含む）
  - [ ] エラー処理

- [ ] FileRepositoryのテスト
  - [ ] find_by_urlでの検索
  - [ ] find_allでの一覧取得
  - [ ] メタデータの読み込み

### 統合テスト

- [ ] パイプライン統合テストとの整合性確認
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
       ├── cache.json      # メタデータ（WebsiteCache）
       ├── index.html
       ├── about.html
       └── assets/
           └── style.css
   ```

3. **CachedPageの実装**
   - `read_text()`メソッドをサポート
   - `is_root`フラグでメインページを識別

4. **エラーハンドリング**
   - `NetworkError`: ネットワーク接続エラー
   - `InvalidURLError`: 無効なURL
   - `CachePermissionError`: ファイルシステム権限エラー

## 契約準拠のチェックリスト

- [ ] `FetchServiceProtocol.fetch()`は同期メソッド
- [ ] `WebsiteCacheRepositoryProtocol`にsaveメソッドはない
- [ ] `CachedPage.read_text()`メソッドが実装されている
- [ ] DTOベース（FetchRequest → FetchResult）
- [ ] エラーは`fetch_contracts.py`で定義されたものを使用

## 受け入れ基準

- [ ] すべてのテストがパス
- [ ] 契約（Protocol）に準拠
- [ ] Task 23の統合テストで使用可能
- [ ] エラーハンドリングが適切
- [ ] ログ出力が適切

## 推定工数

4-6時間

## 依存関係

- [01. 設計ドキュメントの完成](20250706-01-complete-design-docs.md)
- [02. 共通インフラストラクチャの実装](20250706-02-common-infrastructure.md)
- [Task 23. パイプライン統合テストの再実装](20250714-23_reimplement_pipeline_tests.md)

## 次のタスク

→ [04. HTMLパーサーの実装](20250706-04-implement-html-parser.md)

## AIへの実装依頼例

```
以下の契約に基づいてFetchServiceを実装してください：

契約定義:
- src/site2/core/ports/fetch_contracts.py

重要な変更点:
1. WebsiteCacheRepositoryProtocolにsaveメソッドはありません（読み取り専用）
2. FetchServiceは内部でキャッシュを保存します
3. CachedPageにはread_text()メソッドがあります
4. FetchServiceProtocolのfetchメソッドは同期です（asyncではない）

要件:
1. FetchServiceProtocolを実装
2. 依存性注入を使用
3. 適切なエラーハンドリング（NetworkError, InvalidURLError, CachePermissionError）
4. ログ出力（loguru使用）

テストケース:
- tests/unit/core/use_cases/test_fetch_service.py

制約:
- wgetは必ずsubprocessで呼び出す
- キャッシュディレクトリは設定可能
- 並行ダウンロードは3接続まで
```
