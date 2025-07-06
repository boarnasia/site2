# fetch.feature
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

  Scenario: キャッシュ一覧の表示（コロン記法）
    Given 以下のサイトがキャッシュされている:
      | url                    | pages | size    | last_updated        |
      | https://example.com    | 15    | 1.2 MB  | 2025-01-05 10:00:00 |
      | https://docs.python.org| 250   | 45.3 MB | 2025-01-04 15:30:00 |
    When コマンド "site2 fetch:list" を実行する
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

  Scenario: メインコンテンツの検出（コロン記法）
    Given ファイル "test.html" が存在する
    When コマンド "site2 detect:main test.html" を実行する
    Then 終了コード 0 で正常終了する
    And 標準出力に以下を含む:
      """
      main.content, article.post, div#main-content
      """

  Scenario: ナビゲーションの検出（コロン記法）
    Given "https://example.com" がキャッシュされている
    When コマンド "site2 detect:nav https://example.com" を実行する
    Then 終了コード 0 で正常終了する
    And 標準出力に以下を含む:
      """
      nav.primary, div.navigation, ul.menu
      """

  Scenario: ドキュメント順序の検出（コロン記法）
    Given ディレクトリ "docs/" に複数のHTMLファイルが存在する
    When コマンド "site2 detect:order docs/" を実行する
    Then 終了コード 0 で正常終了する
    And 標準出力に順序付けられたファイルリストが出力される:
      """
      docs/index.html
      docs/getting-started.html
      docs/installation.html
      docs/configuration.html
      docs/advanced.html
      """

  Scenario: 自動変換（Markdown出力）
    Given "https://example.com" はまだキャッシュされていない
    When コマンド "site2 auto https://example.com" を実行する
    Then 終了コード 0 で正常終了する
    And 標準出力にMarkdown形式のコンテンツが出力される
    And 出力の最初の行は "# " で始まる

  Scenario: 自動変換（PDF出力）
    Given "https://example.com" はまだキャッシュされていない
    When コマンド "site2 auto --format pdf https://example.com" を実行する
    Then 終了コード 0 で正常終了する
    And 標準出力にPDFバイナリが出力される
    And 出力の最初の4バイトは "%PDF" である
