# language: ja
機能: Webサイトのフェッチとキャッシュ
  ユーザーとして
  Webサイトのコンテンツをローカルにキャッシュしたい
  オフラインでも参照できるようにするため

  背景:
    前提 キャッシュディレクトリ "~/.cache/site2" が存在する
    かつ ネットワーク接続が利用可能である

  シナリオ: 新規サイトのフェッチ
    前提 "https://example.com" はまだキャッシュされていない
    もし コマンド "site2 fetch https://example.com" を実行する
    ならば 終了コード 0 で正常終了する
    かつ 標準出力に以下を含む:
      """
      ✅ Fetched: https://example.com
      Pages: 15
      Total size: 1.2 MB
      Cache: ~/.cache/site2/example.com_a1b2c3d4
      """
    かつ キャッシュディレクトリ "~/.cache/site2/example.com_a1b2c3d4" が作成される
    かつ メタデータファイル "cache.json" が存在する

  シナリオ: キャッシュ一覧の表示（コロン記法）
    前提 以下のサイトがキャッシュされている:
      | url                    | pages | size    | last_updated        |
      | https://example.com    | 15    | 1.2 MB  | 2025-01-05 10:00:00 |
      | https://docs.python.org| 250   | 45.3 MB | 2025-01-04 15:30:00 |
    もし コマンド "site2 fetch:list" を実行する
    ならば 終了コード 0 で正常終了する
    かつ 標準出力に以下を含む:
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

  シナリオ: メインコンテンツの検出（コロン記法）
    前提 ファイル "test.html" が存在する
    もし コマンド "site2 detect:main test.html" を実行する
    ならば 終了コード 0 で正常終了する
    かつ 標準出力に以下を含む:
      """
      main.content, article.post, div#main-content
      """

  シナリオ: ナビゲーションの検出（コロン記法）
    前提 "https://example.com" がキャッシュされている
    もし コマンド "site2 detect:nav https://example.com" を実行する
    ならば 終了コード 0 で正常終了する
    かつ 標準出力に以下を含む:
      """
      nav.primary, div.navigation, ul.menu
      """

  シナリオ: ドキュメント順序の検出（コロン記法）
    前提 ディレクトリ "docs/" に複数のHTMLファイルが存在する
    もし コマンド "site2 detect:order docs/" を実行する
    ならば 終了コード 0 で正常終了する
    かつ 標準出力に順序付けられたファイルリストが出力される:
      """
      docs/index.html
      docs/getting-started.html
      docs/installation.html
      docs/configuration.html
      docs/advanced.html
      """

  シナリオ: 自動変換（Markdown出力）
    前提 "https://example.com" はまだキャッシュされていない
    もし コマンド "site2 auto https://example.com" を実行する
    ならば 終了コード 0 で正常終了する
    かつ 標準出力にMarkdown形式のコンテンツが出力される
    かつ 出力の最初の行は "# " で始まる

  シナリオ: 自動変換（PDF出力）
    前提 "https://example.com" はまだキャッシュされていない
    もし コマンド "site2 auto --format pdf https://example.com" を実行する
    ならば 終了コード 0 で正常終了する
    かつ 標準出力にPDFバイナリが出力される
    かつ 出力の最初の4バイトは "%PDF" である
