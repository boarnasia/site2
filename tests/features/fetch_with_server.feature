Feature: ローカルWebサーバーを使ったフェッチ機能
  安定したテスト環境のため
  ローカルの静的ファイルサーバーを使用してテストする

  Background:
    Given ローカルWebサーバーが起動している
    And キャッシュディレクトリが空である

  Scenario: ローカルサーバーからのフェッチ
    When ローカルサーバーのURLをフェッチする
    Then フェッチが成功する
    And 4 ページがキャッシュされる
    And 以下のファイルがキャッシュされる:
      | file       |
      | index.html |
      | about.html |
      | guide.html |
      | style.css  |

  Scenario: 深さ制限付きフェッチ
    When 深さ 0 でローカルサーバーをフェッチする
    Then フェッチが成功する
    And ルートページのみがキャッシュされる

  Scenario: pytest-bddドキュメントのフェッチ
    Given pytest-bddドキュメントサーバーが起動している
    When ドキュメントサーバーをフェッチする
    Then フェッチが成功する
    And 複数のドキュメントページがキャッシュされる
