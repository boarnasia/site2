Feature: site2パイプライン全体の動作
  Webサイトを取得して
  構造を解析し
  適切な順序でMarkdown/PDFに変換する

  Background:
    Given テスト用のWebサーバーが起動している
    And キャッシュディレクトリが空である

  Scenario: 完全なパイプラインの実行（auto）
    When "site2 auto http://localhost:8080" を実行する
    Then 終了コード 0 で正常終了する
    And 標準出力にMarkdownが出力される
    And 出力に以下の要素が順番に含まれる:
      | element               |
      | # Welcome to Test Site |
      | ## About This Site    |
      | ## User Guide         |

  Scenario: 個別コマンドによるパイプライン実行
    # Step 1: Fetch
    When "site2 fetch http://localhost:8080" を実行する
    Then 終了コード 0 で正常終了する
    And キャッシュディレクトリにHTMLファイルが保存される

    # Step 2: Detect main content
    When キャッシュされた "index.html" に対して "site2 detect:main" を実行する
    Then 終了コード 0 で正常終了する
    And 標準出力に "main.content" を含む

    # Step 3: Detect navigation
    When キャッシュされた "index.html" に対して "site2 detect:nav" を実行する
    Then 終了コード 0 で正常終了する
    And 標準出力に "nav.navigation" を含む

    # Step 4: Detect order
    When キャッシュディレクトリに対して "site2 detect:order" を実行する
    Then 終了コード 0 で正常終了する
    And 標準出力に順序付きファイルリストが出力される:
      """
      1. index.html
      2. about.html
      3. docs/guide.html
      """

    # Step 5: Build
    When 検出された情報で "site2 build --format md" を実行する
    Then 終了コード 0 で正常終了する
    And 標準出力にMarkdownが出力される

  Scenario: メインコンテンツ検出の詳細
    Given 以下のHTMLファイルが存在する:
      """html
      <body>
        <header>Header</header>
        <nav>Navigation</nav>
        <main class="content">
          <h1>Main Content</h1>
          <p>This is the main content.</p>
        </main>
        <aside>Sidebar</aside>
        <footer>Footer</footer>
      </body>
      """
    When このファイルに対して "site2 detect:main" を実行する
    Then 標準出力に以下のセレクタが含まれる:
      | selector      |
      | main.content  |
      | main          |
      | .content      |

  Scenario: ナビゲーション検出の詳細
    Given ナビゲーション構造を持つHTMLファイルが存在する
    When このファイルに対して "site2 detect:nav" を実行する
    Then 標準出力にナビゲーションセレクタが出力される
    And 検出されたナビゲーションに複数のリンクが含まれる

  Scenario: 順序検出の階層構造対応
    Given 階層的なナビゲーションを持つサイトがキャッシュされている:
      """
      - Home
      - Getting Started
        - Installation
        - Configuration
      - Advanced
        - Plugins
        - API
      """
    When "site2 detect:order" を実行する
    Then 以下の順序でファイルが出力される:
      | order | file                | level |
      | 1     | index.html          | 0     |
      | 2     | getting-started.html| 0     |
      | 3     | installation.html   | 1     |
      | 4     | configuration.html  | 1     |
      | 5     | advanced.html       | 0     |
      | 6     | plugins.html        | 1     |
      | 7     | api.html           | 1     |

  Scenario: PDF出力
    Given Webサイトがキャッシュされている
    When "site2 build --format pdf" を実行する
    Then 終了コード 0 で正常終了する
    And 標準出力にPDFバイナリが出力される
    And PDFヘッダー "%PDF" で始まる

  Scenario Outline: エラーハンドリング
    When "<command>" を実行する
    Then 終了コード 1 でエラー終了する
    And 標準エラー出力に "<error_message>" を含む

    Examples:
      | command                          | error_message           |
      | site2 fetch invalid-url          | Invalid URL            |
      | site2 detect:main /not/found     | File not found         |
      | site2 detect:order /empty/dir    | No HTML files found    |
      | site2 build --format invalid     | Invalid format         |
