# fetch_scenarios.feature
Feature: Webサイトのフェッチとキャッシュ
  ユーザーとして
  Webサイトのコンテンツをローカルにキャッシュしたい
  オフラインでも参照できるようにするため

  Background:
    Given キャッシュディレクトリ "~/.cache/site2" が存在する
    And ネットワーク接続が利用可能である

  Scenario: 新規サイトのフェッチ
    Given "https://example.com" はまだキャッシュされていない
    When コマンド "site2 fetch https://example.com" を実行する
    Then 終了コード 0 で正常終了する
    And 標準出力に以下を含む:
      """
      ✅ Fetched: https://example.com
      Pages: 15
      Total size: 1.2 MB
      Cache: ~/.cache/site2/example.com_a1b2c3d4
      """
    And キャッシュディレクトリ "~/.cache/site2/example.com_a1b2c3d4" が作成される
    And メタデータファイル "cache.json" が存在する

  Scenario: キャッシュ済みサイトの差分更新
    Given "https://example.com" は24時間前にキャッシュされている
    And サイトの "/docs/new-page.html" が追加されている
    When コマンド "site2 fetch https://example.com" を実行する
    Then 終了コード 0 で正常終了する
    And 標準出力に以下を含む:
      """
      🔄 Updating cache: https://example.com
      New pages: 1
      Updated pages: 3
      Total size: 1.3 MB
      """
    And 新しいページ "/docs/new-page.html" がキャッシュされる
    And 更新されたページのタイムスタンプが更新される

  Scenario: 深さ制限付きフェッチ
    Given "https://example.com" はまだキャッシュされていない
    When コマンド "site2 fetch https://example.com --depth 1" を実行する
    Then 終了コード 0 で正常終了する
    And ルートページとその直接リンクのみがキャッシュされる
    And 深さ2以上のページはキャッシュされない

  Scenario: キャッシュ一覧の表示
    Given 以下のサイトがキャッシュされている:
      | url                    | pages | size    | last_updated        |
      | https://example.com    | 15    | 1.2 MB  | 2025-01-05 10:00:00 |
      | https://docs.python.org| 250   | 45.3 MB | 2025-01-04 15:30:00 |
    When コマンド "site2 fetch list" を実行する
    Then 終了コード 0 で正常終了する
    And 標準出力に以下を含む:
      """
      📦 Cached sites:

      1. https://example.com
         Pages: 15 | Size: 1.2 MB | Updated: 2025-01-05 10:00:00
         Cache: ~/.cache/site2/example.com_a1b2c3d4

      2. https://docs.python.org
         Pages: 250 | Size: 45.3 MB | Updated: 2025-01-04 15:30:00
         Cache: ~/.cache/site2/docs.python.org_e5f6g7h8

      Total: 2 sites, 265 pages, 46.5 MB
      """

  Scenario: 無効なURLのエラー処理
    When コマンド "site2 fetch not-a-url" を実行する
    Then 終了コード 1 でエラー終了する
    And 標準エラー出力に以下を含む:
      """
      ❌ Error: Invalid URL format
      URL must start with http:// or https://
      """

  Scenario: ネットワークエラーの処理
    Given "https://unreachable.example.com" はアクセスできない
    When コマンド "site2 fetch https://unreachable.example.com" を実行する
    Then 終了コード 1 でエラー終了する
    And 標準エラー出力に以下を含む:
      """
      ❌ Error: Failed to connect to https://unreachable.example.com
      Network error: Connection refused
      """

  Scenario: 強制リフレッシュ
    Given "https://example.com" は1時間前にキャッシュされている
    When コマンド "site2 fetch https://example.com --force" を実行する
    Then すべてのページが再取得される
    And 標準出力に以下を含む:
      """
      🔄 Force refresh: https://example.com
      All pages will be re-fetched
      """
