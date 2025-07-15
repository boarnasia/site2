# 1: user, 状況説明と今後の方針共有

以下にこれまでの概要とこれからやりたいことを記述します。
まずは内容を理解し、必要な情報を探索し状況を理解してください。

---

## 概要

これから site2 というプロジェクトを開始する
これは CLI ツールです。
指定した url 配下のファイルを取得して1枚の markdown (md) や PDF にまとめることができます。
最終的に出力する形態はオプションで選択できる。 例: site2 -format=md|pdf

プロジェクトレポジトリ
https://github.com/boarnasia/site2



## これまでの経緯

このプロジェクトの前身として以下のプロジェクトがありました。
このプロジェクトは claude code を使用して開発を行いました。
github: https://github.com/boarnasia/site2pdf
branch: main


### 最初のアプローチ

最初は claude code を使用して以下のツールを作成しました。
- cli_fetcher.py: フェッチャー。指定ＵＲＬからhtmlを取得してキャッシュする。
- convert_and_merge.py: コンバーター。キャッシュしたHTMLを変換し1枚のＰＤＦにまとめあげる。

#### このツールの良かった点、悪かった点：

良かった点:

1. 確実にページをPDFにしてくれた
2. シンプルがゆえに堅牢だった
3. playwright を使用した美しいレンダリング結果
4. wget の高速なスクレイピング、SSLの諸問題を自動的に解決、優秀なキャッシュ機能、更新日見て不要なファイルの再取得を避けるなど。

悪かった点:

1. 出力されたPDFに余計なタグなどが残っていた
2. ページのオーダーが間違うケースがあった

そこでそれらの問題を解決するために次のアプローチを開始しました。


### アプローチ 2：機能分割し機能向上を狙う

次に機能を分割し、機能向上を目指した

- site2pdf <url>: fetch, sort, build をまとめて実行する
- site2pdf fetch <url>: ファイルをフェッチする
- site2pdf sort <url>: ファイルのソートオーダーを決定する
- site2pdf buld <url>: ファイルを1枚のPDFにビルドする

良かった点:

1. ソート機能が向上した

悪かった点:

1. 全体を自動で実行させる分には良いが、個別に実行すると奇妙な動作を行うようになった
2. cli アプリケーションの土台にtyper を使用したが、それが正しく動作しているのか検証ができなかった


### アプローチ 3: ai agent の機能を開放して改善を依頼した

github: https://github.com/boarnasia/site2pdf
branch: 20250703-make-think-nav-block

`ai-agents/todos.md` に基づいて ai agent にコードの構築を依頼していました。
claude code には agent tool を使用して、commandar, w_nav_think_nav_block, w_fetcher など役割を持ったagentに、それぞれ自律的、協調的に動作して作業を依頼した。
claude は1セッションの中でroleを切り替えながら、commanderが統括しながら作業を進めてくれた。

ただし、ここから私に混乱が生じた
ai が何を作ったのかが分からなくった。

多くのファイルが作られるのだが、どれがその実装か分からなくなった
それに加えて最終的なフォーマットにmarkdownを加えたくなった。
なのでゼロベースでプロジェクトを仕切りなおすことにした。

## これからのアプローチ

プロジェクトをゼロから作り直すことにした。

github: https://github.com/boarnasia/site2

新しいプロジェクトでは以前の仕様を踏襲しつつ以下の変更を加える

- 出力形式にmarkdownを追加
- 出力形式のデフォルトはmarkdownにする

また、自動コーディングを制御しつつ進めていくために設計フェーズのやり方を変更しようと思う。
設計では以下のものを用意しようと思う。
意図: この設計をもとにAIに自律的に実装を進めさせたい
意図: AIが暴走することを防ぎたい
意図: 成果物の重要店をあらかじめ抑えたい
意図: 重要ポイントに試験を用意し、方向がずれることを防ぎたい

1. 設計
2. モックアップの作成
3. テストの作成
4. AIのロール設計
5. Todoの作成

この設計で１～５を数回ループしながら精度を上げていきたい



# 2: system, 状況の理解を報告

理解しました。site2プロジェクトの概要と経緯を把握しました。まず、関連する情報を探索して状況をより深く理解させていただきます。状況を把握しました。以下に整理します：

## 現状の理解

### 1. **プロジェクトの経緯**
- **前身プロジェクト**: `site2pdf` - URLから複数のHTMLファイルを取得し、1つのPDFにまとめるCLIツール
- **技術スタック**: Python (Rye, Typer, Playwright, BeautifulSoup4)
- **3つのアプローチを試行**:
  - アプローチ1: シンプルな2段階処理（fetch→convert）
  - アプローチ2: 機能分割（fetch→sort→build）
  - アプローチ3: AI agentによる自律的開発

### 2. **現在の課題**
- AI agentによる開発で混乱が生じた（どのファイルが実装か不明）
- 出力形式にMarkdownを追加したい
- 開発プロセスを制御可能にしたい

### 3. **新プロジェクト `site2` の方針**
- ゼロベースでの再構築
- 出力形式: Markdown（デフォルト）とPDF
- 設計駆動開発アプローチ:
  1. 設計
  2. モックアップの作成
  3. テストの作成
  4. AIのロール設計
  5. Todoの作成

### 4. **site2pdfの主要機能**
- **fetch**: wgetを使用してURLからHTMLをキャッシュ
- **sort**: 取得したHTMLファイルの並び順を決定（simple/auto/default/AI mode）
- **build**: HTMLをPDFに変換して結合

### 5. **良い点と改善点**
**良い点**:
- wgetの堅牢性（SSL対応、キャッシュ機能）
- Playwrightによる美しいレンダリング
- ソート機能の柔軟性

**改善点**:
- 余計なタグの残存
- ページ順序の誤り
- Typerの動作検証の困難さ
- Markdown出力未対応

これから、新しい`site2`プロジェクトの設計フェーズを開始しましょう。まず、どの部分から着手しますか？設計ドキュメントの作成から始めるのが良いでしょうか？




# 3: user, 作成すべきドキュメントのリストアップを指示

設計ドキュメントの作成から始めたい。

まずどのような設計ドキュメントが必要かリストアップしてください



# 4: system

新しい`site2`プロジェクトに必要な設計ドキュメントをリストアップします。

## 必要な設計ドキュメント一覧

### 1. **プロジェクト概要設計書**
- プロジェクトの目的と背
- 主要機能の概要
- 技術スタックの選定理由
- 前プロジェクトからの改善点

### 2. **要件定義書**
- 機能要件
  - コマンドライン仕様
  - 入力仕様（URL、オプション）
  - 出力仕様（Markdown/PDF形式）
- 非機能要件
  - パフォーマンス要件
  - エラーハンドリング
  - ログ出力

### 3. **アーキテクチャ設計書**
- システム全体構成図
- モジュール構成と責務
- データフロー図
- ディレクトリ構造

### 4. **詳細設計書**
- 各モジュールの詳細仕様
  - Fetcher（取得機能）
  - Parser（解析機能）
  - Sorter（並び替え機能）
  - Converter（変換機能）
  - Builder（出力生成機能）
- インターフェース定義
- エラーコード体系

### 5. **API/CLI設計書**
- コマンド体系の設計
- オプション仕様
- 設定ファイル仕様
- 使用例集

### 6. **データ設計書**
- キャッシュ構造
- メタデータ形式
- 中間ファイル形式
- 設定ファイル形式

### 7. **テスト設計書**
- テスト戦略
- テストケース一覧
- モックデータ仕様
- E2Eテストシナリオ

### 8. **AI開発ガイドライン**
- AI agentの役割定義
- 各agentの責務範囲
- agent間の連携ルール
- 暴走防止のための制約事項

### 9. **開発プロセス設計書**
- 開発フロー
- コーディング規約
- レビュープロセス
- リリースプロセス

### 10. **運用・保守設計書**
- ログ設計
- エラー監視方法
- トラブルシューティングガイド
- バージョン管理方針

どの設計ドキュメントから作成を始めますか？プロジェクト概要設計書や要件定義書から始めるのが一般的ですが、お考えをお聞かせください。



# 5: user,

Tasks:

- [ ] 1. プロジェクト概要設計書
- [ ] 2. 要件定義書
- [ ] 3. アーキテクチャ設計書
- [ ] 4. 詳細設計書
  - [ ] 各モジュールの詳細仕様
    - [ ] Fetcher（取得機能）
    - [ ] Parser（解析機能）
    - [ ] Sorter（並び替え機能）
    - [ ] Converter（変換機能）
    - [ ] Builder（出力生成機能）
  - [ ] インターフェース定義
  - [ ] エラーコード体系
- [ ] 5. API/CLI設計書
- [ ] 6. データ設計書
- [ ] 7. テスト設計書
- [ ] 8. AI開発ガイドライン
- [ ] 9. 開発プロセス設計書
- [ ] 10. 運用・保守設計書

---

それほど大きなツールではないので書類を多く作る必要はないとは思い
しかしながら、私はすぐに忘れてしまうので、書類の大事さはわかっているつもりだ
必要最小限に収めつつ進めていきましょう。

あなたへの依頼を <query /> タグで示しました。
対応をお願いします。

---

ではプロジェクト概要書設計書を作成しましょう
> 1. プロジェクト概要設計書
>
> プロジェクトの目的と背景
> 主要機能の概要
> 技術スタックの選定理由
> 前プロジェクトからの改善点

## プロジェクト概要設計書

### プロジェクトの目的と背景

<query>
これまでの情報をもとに作成してください
</query>

### 主要機能の概要

```
Usage:
  site2 [--format <md|pdf>] <uri>
      指定された uri からファイルを取得して1枚のファイルにまとめて標準出力に出力する
      リカーシブに動作します

  site2 fetch <uri>
      指定された uri からファイルを取得してキャッシュする
      キャッシュが存在するときは更新されたファイルだけを更新する
      リカーシブに動作します

  site2 fetch list
      既に fetch 済みのキャッシュを一覧表示する

  site2 detect main <file_or_uri>
      ドキュメントのメインの文章ブロックへの CSS セレクタを返す

  site2 detect nav <file_or_uri>
      ドキュメントのナビゲーションブロックへの CSS セレクタを返す

  site2 detect order <path_or_uri>
      ドキュメントの一覧を出力順に標準出力に出力します

  site2 build [--format <md|pdf>] <file_or_uri>...
      指定されたファイルまたは uri を指定されたフォーマットに変換し、指定された順番にマージして標準出力に出力する
```

### 技術スタックの選定理由

<query>
これまでの情報をもとに作成してください
</query>

### 前プロジェクトからの改善点

<query>
これまでの情報をもとに作成してください
</query>

# 6: system

```markdown
# プロジェクト概要設計書

## プロジェクトの目的と背景

### 目的
`site2`は、指定されたWebサイトのコンテンツを取得し、1つのMarkdownファイルまたはPDFファイルに統合するCLIツールです。ドキュメントサイトやマニュアルサイトなどの構造化されたWebコンテンツを、オフラインで参照可能な単一ファイルとして保存することを目的としています。

### 背景
前身プロジェクト`site2pdf`の開発を通じて、以下の課題が明らかになりました：

1. **出力形式の制限**: PDF出力のみで、より汎用的なMarkdown形式への対応が必要
2. **開発プロセスの複雑化**: AI agentによる自律的開発により、成果物の把握が困難に
3. **品質管理の困難さ**: 余計なHTMLタグの残存、ページ順序の誤りなど

これらの課題を解決し、より制御可能で品質の高いツールを開発するため、`site2`プロジェクトを立ち上げました。

## 主要機能の概要

> [!Usage:]
>   site2 [--format <md|pdf>] <uri>
>       指定された uri からファイルを取得して1枚のファイルにまとめて標準出力に出力する
>       リカーシブに動作します
>
>   site2 fetch <uri>
>       指定された uri からファイルを取得してキャッシュする
>       キャッシュが存在するときは更新されたファイルだけを更新する
>       リカーシブに動作します
>
>   site2 fetch list
>       既に fetch 済みのキャッシュを一覧表示する
>
>   site2 detect main <file_or_uri>
>       ドキュメントのメインの文章ブロックへの CSS セレクタを返す
>
>   site2 detect nav <file_or_uri>
>       ドキュメントのナビゲーションブロックへの CSS セレクタを返す
>
>   site2 detect order <path_or_uri>
>       ドキュメントの一覧を出力順に標準出力に出力します
>
>   site2 build [--format <md|pdf>] <file_or_uri>...
>       指定されたファイルまたは uri を指定されたフォーマットに変換し、指定された順番にマージして標準出力に出力する

## 技術スタックの選定理由

### 言語: Python
- **実績**: 前プロジェクトで安定動作を確認
- **エコシステム**: Web スクレイピング、PDF生成、Markdown処理の優れたライブラリが豊富
- **保守性**: 読みやすく、AIとの協調開発に適している

### 主要ライブラリ
- **Rye**: モダンなPythonプロジェクト管理ツール。依存関係管理が容易
- **Typer**: 直感的なCLI構築。型ヒントベースで保守性が高い
- **wget (外部コマンド)**:
  - 堅牢なWebサイト取得機能
  - SSL問題の自動解決
  - 優秀なキャッシュ機能
  - 更新日を考慮した差分取得
- **BeautifulSoup4**: HTML解析の定番。安定性が高い
- **Playwright**: ブラウザベースのレンダリング。JavaScriptで生成されるコンテンツにも対応
- **pypdf**: PDF操作ライブラリ

### 新規追加予定
- **Markdown処理ライブラリ**: MarkdownファイルのパースとHTML変換
- **Jinja2等のテンプレートエンジン**: 出力フォーマットの柔軟な制御

## 前プロジェクトからの改善点

### 1. 出力形式の拡張
- **Markdown出力をデフォルトに**: より汎用的で編集可能な形式
- **PDF出力も継続サポート**: 印刷や配布に適した形式として

### 2. アーキテクチャの改善
- **モジュール分離の明確化**: 各機能の責務を明確に定義
- **インターフェースの標準化**: モジュール間の連携を疎結合に

### 3. 品質向上施策
- **不要タグの確実な除去**: Parser機能の強化
- **ページ順序の正確性向上**: ナビゲーション構造の解析精度向上
- **テスト駆動開発**: 各モジュールに対する単体テスト・統合テストの充実

### 4. 開発プロセスの改善
- **設計先行アプローチ**: AIによる実装前に、人間による設計を完了
- **段階的な実装**: モックアップ→テスト→実装の順序で進行
- **AI活用の制御**: 各AIエージェントの役割を明確に定義し、暴走を防止

### 5. ユーザビリティの向上
- **標準出力への出力**: パイプラインでの利用を容易に
- **検出機能の追加**: メインコンテンツやナビゲーションの自動検出
- **柔軟な入力対応**: ファイルとURIの両方に対応
```



# 7: user, ドメイン駆動開発、テスト駆動開発を相談

相談。今回はドメイン駆動開発、テスト駆動開発などを取り入れて行きたい。
適時アドバイスをください。

現段階で見直すべきことはありますか？




# 8: system

優れた選択です！DDD（ドメイン駆動開発）とTDD（テスト駆動開発）を取り入れることで、より堅牢で保守性の高いツールが作れます。

## 現段階での見直しポイント

### 1. **ドメインモデルの明確化が必要**
現在のCLI設計は機能ベースですが、DDDの観点から以下のドメインモデルを定義すべきです：

```python
# 例：ドメインモデル
- WebDocument (Webドキュメント)
- DocumentCollection (ドキュメントコレクション)
- NavigationStructure (ナビゲーション構造)
- ContentBlock (コンテンツブロック)
- OutputDocument (出力ドキュメント)
```

### 2. **ユビキタス言語の定義**

プロジェクト全体で使う共通言語を定義しましょう：
- "fetch" → "crawl" または "harvest"（収穫する）
- "detect" → "analyze" または "extract"（抽出する）
- "build" → "compose" または "assemble"（組み立てる）

### 3. **境界づけられたコンテキストの設定**

現在の機能を以下のコンテキストに整理：

```
- 収集コンテキスト (Crawling Context)
  - URLからのコンテンツ取得
  - キャッシュ管理

- 解析コンテキスト (Analysis Context)
  - DOM構造の解析
  - ナビゲーション抽出
  - コンテンツ抽出

- 変換コンテキスト (Transformation Context)
  - Markdown/PDF変換
  - 順序付け
  - 統合
```

### 4. **TDDのための準備**

以下を追加で設計すべきです：

```python
# テストファースト開発のための構造
tests/
  unit/           # 単体テスト
    domain/       # ドメインモデルのテスト
    application/  # アプリケーション層のテスト
  integration/    # 統合テスト
  e2e/           # エンドツーエンドテスト
  fixtures/      # テストデータ
```

## 推奨する次のステップ

### 1. **ドメインモデル設計書の作成**
プロジェクト概要設計書の後に、以下を含むドメインモデル設計書を作成：
- エンティティの定義
- 値オブジェクトの定義
- 集約の境界
- ドメインサービス

### 2. **テスト戦略書の作成**
TDDを実践するため、早い段階でテスト戦略を定義：
- テストピラミッド（単体/統合/E2E）の比率
- モックの方針
- テストデータ管理
- CI/CDでのテスト実行

### 3. **インターフェース定義の見直し**
DDDの観点から、以下のレイヤー構造を採用：

```
- プレゼンテーション層（CLI）
- アプリケーション層（ユースケース）
- ドメイン層（ビジネスロジック）
- インフラストラクチャ層（外部システム連携）
```

### 4. **イベント駆動の検討**
処理の流れをイベントで表現することで、疎結合な設計が可能：
- DocumentFetchedEvent
- NavigationExtractedEvent
- DocumentComposedEvent

これらの見直しを行うことで、より保守性が高く、テストしやすい設計になります。どの点から着手しますか？




# 9: user, ほかに取り込むべき手法はありますか？



# 10: system

はい、`site2`プロジェクトの特性を考慮すると、以下の手法も取り込むべきです：

## 追加で推奨する開発手法

### 1. **Clean Architecture / Hexagonal Architecture**
外部依存（wget、Playwright、ファイルシステム）を中心から分離し、テストしやすい構造に：
```python
# ポートとアダプターパターン
core/
  domain/        # ビジネスロジック（外部依存なし）
  ports/         # インターフェース定義
adapters/
  cli/          # CLI実装
  crawlers/     # wget/Playwright実装
  storage/      # ファイルシステム実装
```

### 2. **Contract-First Development（契約優先開発）**
AIとの協調開発において特に重要：
- 各モジュールのインターフェースを先に定義
- AIに実装を依頼する前に、入出力の仕様を明確化
- OpenAPI/JSON Schemaなどでスキーマ定義

### 3. **Behavior-Driven Development (BDD)**
ユーザー視点での振る舞いを明確に：
```gherkin
Feature: Webサイトの変換
  Scenario: MarkdownへのサイトExport
    Given "https://example.com"のサイトが存在する
    When site2コマンドを実行する
    Then Markdownファイルが出力される
```

### 4. **Documentation as Code**
```yaml
# docs/architecture/decisions/001-use-wget.md
status: accepted
date: 2025-01-05
decision: wgetを使用してWebコンテンツを取得する
because:
  - 堅牢性が高い
  - キャッシュ機能が優秀
consequences:
  - 外部コマンド依存
```

### 5. **Observability-Driven Development**
最初からモニタリングを組み込む：
```python
# 構造化ログ
logger.info("crawling_started",
    url=url,
    depth=depth,
    cache_dir=cache_dir
)

# メトリクス
metrics.crawl_duration.observe(duration)
metrics.pages_processed.inc(count)
```

### 6. **Feature Toggle Pattern**
AI機能や実験的機能を安全に管理：
```python
if feature_flags.is_enabled("ai_content_extraction"):
    extractor = AIContentExtractor()
else:
    extractor = RuleBasedExtractor()
```

### 7. **Design by Contract (DbC)**
AIに実装を委ねる際の品質保証：
```python
@requires(lambda url: url.startswith(('http://', 'https://')))
@ensures(lambda result: len(result) > 0)
def crawl_website(url: str) -> List[Document]:
    """URLからドキュメントを取得する"""
```

### 8. **Trunk-Based Development**
- 短命なフィーチャーブランチ（最大1-2日）
- 頻繁なmainへのマージ
- AI実装も小さな単位でマージ

## 特に重要な組み合わせ

**AI協調開発のための3点セット**：
1. **Contract-First** → AIへの仕様伝達
2. **Feature Toggle** → AI実装の段階的有効化
3. **Observability** → AI実装の振る舞い監視

**品質保証のための3点セット**：
1. **TDD** → ロジックの正確性
2. **BDD** → ユーザー要求の充足
3. **DbC** → 契約の遵守

どの手法を優先的に取り入れますか？プロジェクトの規模を考慮すると、すべてを取り入れる必要はないかもしれません。




# 11: user, Contract-First をどのように活用するのか

このツールは cli ですが、Contract-First をどのように開発フローの中で運用しますか？
具体例を示してください




# 12: system

## Contract-First Development の CLI ツールでの運用方法

### 1. **CLIインターフェース契約の定義**

まず、CLIコマンドの契約をYAMLやJSONで定義します：

> ```yaml
> # site2 CLI Contract Definition
> version: 1.0.0
> commands:
>   - name: site2
>     description: "Convert website to single markdown or PDF file"
>     arguments:
>       - name: uri
>         type: string
>         required: true
>         pattern: "^https?://.+"
>         description: "Target website URL"
>     options:
>       - name: format
>         type: enum
>         values: [md, pdf]
>         default: md
>         description: "Output format"
>     output:
>       type: stdout
>       content_type:
>         - "text/markdown"
>         - "application/pdf"
>     errors:
>       - code: E001
>         name: INVALID_URL
>         message: "Invalid URL format"
>       - code: E002
>         name: FETCH_FAILED
>         message: "Failed to fetch website content"
>
>   - name: "site2 fetch"
>     description: "Fetch and cache website content"
>     arguments:
>       - name: uri
>         type: string
>         required: true
>         pattern: "^https?://.+"
>     options:
>       - name: depth
>         type: integer
>         default: 3
>         min: 1
>         max: 10
>         description: "Crawl depth"
>       - name: cache-dir
>         type: path
>         default: "~/.cache/site2"
>         description: "Cache directory path"
>     output:
>       type: json
>       schema:
>         type: object
>         properties:
>           cached_files:
>             type: array
>             items:
>               type: object
>               properties:
>                 url: { type: string }
>                 path: { type: string }
>                 size: { type: integer }
>                 timestamp: { type: string, format: date-time }
>           total_size: { type: integer }
>           cache_dir: { type: string }
>     errors:
>       - code: E101
>         name: CACHE_EXISTS
>         message: "Cache already exists"
>       - code: E102
>         name: CRAWL_TIMEOUT
>         message: "Crawl operation timed out"
>
>   - name: "site2 detect main"
>     description: "Detect main content CSS selector"
>     arguments:
>       - name: file_or_uri
>         type: string
>         required: true
>     output:
>       type: json
>       schema:
>         type: object
>         properties:
>           selector: { type: string }
>           confidence: { type: number, minimum: 0, maximum: 1 }
>           sample_text: { type: string, maxLength: 200 }
>
>   - name: "site2 build"
>     description: "Build output from cached or provided files"
>     arguments:
>       - name: files_or_uris
>         type: array
>         required: true
>         minItems: 1
>     options:
>       - name: format
>         type: enum
>         values: [md, pdf]
>         default: md
>       - name: output
>         type: path
>         description: "Output file path (default: stdout)"
>     input:
>       accept_stdin: true
>       format: "text/plain"  # File paths, one per line
>     output:
>       type:
>         - stdout
>         - file
>       content_type:
>         - "text/markdown"
>         - "application/pdf"
> ```

### 2. **内部モジュール間の契約定義**

各モジュール間のインターフェースを定義：

> ```python
> """
> site2 内部モジュール間の契約定義
> """
> from typing import Protocol, List, Dict, Optional, Union
> from dataclasses import dataclass
> from datetime import datetime
> from pathlib import Path
> from enum import Enum
>
>
> class OutputFormat(Enum):
>     MARKDOWN = "md"
>     PDF = "pdf"
>
>
> # --- Data Transfer Objects (DTOs) ---
> @dataclass
> class CrawlResult:
>     """クローラーの出力契約"""
>     url: str
>     cached_files: List['CachedFile']
>     total_size: int
>     cache_dir: Path
>     crawl_timestamp: datetime
>
>     def validate(self):
>         """契約の事後条件を検証"""
>         assert self.url.startswith(('http://', 'https://')), "URL must be HTTP(S)"
>         assert len(self.cached_files) > 0, "At least one file must be cached"
>         assert self.total_size > 0, "Total size must be positive"
>         assert self.cache_dir.exists(), "Cache directory must exist"
>
>
> @dataclass
> class CachedFile:
>     """キャッシュされたファイルの契約"""
>     url: str
>     local_path: Path
>     size: int
>     content_type: str
>     timestamp: datetime
>
>     def validate(self):
>         assert self.local_path.exists(), f"Cached file must exist: {self.local_path}"
>         assert self.size > 0, "File size must be positive"
>
>
> @dataclass
> class ExtractedContent:
>     """抽出されたコンテンツの契約"""
>     main_selector: str
>     main_content: str
>     nav_selector: Optional[str]
>     nav_links: List[Dict[str, str]]
>     confidence: float
>
>     def validate(self):
>         assert 0 <= self.confidence <= 1, "Confidence must be between 0 and 1"
>         assert len(self.main_content) > 0, "Main content must not be empty"
>
>
> @dataclass
> class DocumentOrder:
>     """ドキュメント順序の契約"""
>     files: List[Path]
>     order_method: str  # "navigation", "filesystem", "ai"
>     confidence: float
>
>     def validate(self):
>         assert len(self.files) > 0, "At least one file required"
>         assert all(f.exists() for f in self.files), "All files must exist"
>         assert 0 <= self.confidence <= 1, "Confidence must be between 0 and 1"
>
>
> @dataclass
> class ConversionResult:
>     """変換結果の契約"""
>     format: OutputFormat
>     content: Union[str, bytes]
>     metadata: Dict[str, any]
>
>     def validate(self):
>         if self.format == OutputFormat.MARKDOWN:
>             assert isinstance(self.content, str), "Markdown must be string"
>         elif self.format == OutputFormat.PDF:
>             assert isinstance(self.content, bytes), "PDF must be bytes"
>
>
> # --- Service Protocols (Interfaces) ---
> class CrawlerProtocol(Protocol):
>     """Webサイトクローラーの契約"""
>
>     def crawl(self, url: str, depth: int = 3, cache_dir: Optional[Path] = None) -> CrawlResult:
>         """
>         URLからWebサイトをクロールしてキャッシュする
>
>         事前条件:
>         - url: HTTP(S)で始まる有効なURL
>         - depth: 1以上10以下の整数
>         - cache_dir: 書き込み可能なディレクトリパス
>
>         事後条件:
>         - 少なくとも1つのファイルがキャッシュされる
>         - CrawlResultが返される
>         - キャッシュディレクトリが存在する
>         """
>         ...
>
>
> class ContentExtractorProtocol(Protocol):
>     """コンテンツ抽出器の契約"""
>
>     def extract_main_content(self, file_path: Path) -> ExtractedContent:
>         """
>         HTMLファイルからメインコンテンツを抽出
>
>         事前条件:
>         - file_path: 存在するHTMLファイル
>
>         事後条件:
>         - ExtractedContentが返される
>         - main_contentが空でない
>         """
>         ...
>
>     def extract_navigation(self, file_path: Path) -> ExtractedContent:
>         """
>         HTMLファイルからナビゲーションを抽出
>
>         事前条件:
>         - file_path: 存在するHTMLファイル
>
>         事後条件:
>         - ExtractedContentが返される
>         - nav_linksが抽出される（空の可能性あり）
>         """
>         ...
>
>
> class DocumentSorterProtocol(Protocol):
>     """ドキュメント順序決定器の契約"""
>
>     def determine_order(self, cached_files: List[CachedFile]) -> DocumentOrder:
>         """
>         キャッシュされたファイルの出力順序を決定
>
>         事前条件:
>         - cached_files: 空でないリスト
>         - すべてのファイルが存在する
>
>         事後条件:
>         - DocumentOrderが返される
>         - すべての入力ファイルが順序に含まれる
>         """
>         ...
>
>
> class DocumentConverterProtocol(Protocol):
>     """ドキュメント変換器の契約"""
>
>     def convert(self, files: List[Path], format: OutputFormat) -> ConversionResult:
>         """
>         ファイルリストを指定フォーマットに変換
>
>         事前条件:
>         - files: 空でないファイルパスのリスト
>         - format: 有効な出力フォーマット
>         - すべてのファイルが存在する
>
>         事後条件:
>         - ConversionResultが返される
>         - contentが空でない
>         """
>         ...
>
>
> # --- 契約検証デコレータ ---
> def validate_contract(func):
>     """契約の事前条件・事後条件を検証するデコレータ"""
>     def wrapper(*args, **kwargs):
>         # 事前条件の検証はdocstringから自動生成も可能
>         result = func(*args, **kwargs)
>
>         # 事後条件の検証
>         if hasattr(result, 'validate'):
>             result.validate()
>
>         return result
>     return wrapper
> ```

### 3. **契約からのテスト生成**

契約定義から自動的にテストケースを生成：

> ```python
> """
> 契約定義から生成されたテストケース
> """
> import pytest
> from pathlib import Path
> from datetime import datetime
> from unittest.mock import Mock, patch
> import json
> import yaml
>
> from contracts import (
>     CrawlResult, CachedFile, ExtractedContent,
>     DocumentOrder, ConversionResult, OutputFormat
> )
>
>
> class TestCLIContract:
>     """CLIコマンドの契約テスト"""
>
>     @pytest.fixture
>     def cli_contract(self):
>         """CLI契約定義をロード"""
>         with open('cli-contract.yaml', 'r') as f:
>             return yaml.safe_load(f)
>
>     def test_site2_command_contract(self, cli_contract):
>         """site2コマンドの引数・オプション契約をテスト"""
>         from site2.cli import main
>
>         # 正常系：契約に従った入力
>         result = main(['https://example.com', '--format', 'md'])
>         assert result.exit_code == 0
>
>         # 異常系：無効なURL（契約違反）
>         result = main(['not-a-url'])
>         assert result.exit_code != 0
>         assert 'E001' in result.output  # INVALID_URL
>
>         # 異常系：無効なフォーマット（契約違反）
>         result = main(['https://example.com', '--format', 'docx'])
>         assert result.exit_code != 0
>
>     def test_fetch_command_output_contract(self, cli_contract):
>         """fetchコマンドの出力契約をテスト"""
>         from site2.cli import fetch
>
>         with patch('site2.crawler.crawl') as mock_crawl:
>             # 契約に従った出力を返すモック
>             mock_crawl.return_value = CrawlResult(
>                 url='https://example.com',
>                 cached_files=[
>                     CachedFile(
>                         url='https://example.com/index.html',
>                         local_path=Path('/tmp/cache/index.html'),
>                         size=1024,
>                         content_type='text/html',
>                         timestamp=datetime.now()
>                     )
>                 ],
>                 total_size=1024,
>                 cache_dir=Path('/tmp/cache'),
>                 crawl_timestamp=datetime.now()
>             )
>
>             result = fetch(['https://example.com'])
>             output = json.loads(result.output)
>
>             # 出力スキーマの検証
>             assert 'cached_files' in output
>             assert isinstance(output['cached_files'], list)
>             assert 'total_size' in output
>             assert isinstance(output['total_size'], int)
>
>
> class TestModuleContracts:
>     """内部モジュール間の契約テスト"""
>
>     def test_crawl_result_contract(self):
>         """CrawlResult契約の検証"""
>         # 正常系
>         result = CrawlResult(
>             url='https://example.com',
>             cached_files=[Mock(spec=CachedFile)],
>             total_size=1024,
>             cache_dir=Path('/tmp/exists'),
>             crawl_timestamp=datetime.now()
>         )
>
>         with patch('pathlib.Path.exists', return_value=True):
>             result.validate()  # 例外が発生しないことを確認
>
>         # 異常系：空のcached_files
>         with pytest.raises(AssertionError, match="At least one file"):
>             invalid_result = CrawlResult(
>                 url='https://example.com',
>                 cached_files=[],
>                 total_size=0,
>                 cache_dir=Path('/tmp'),
>                 crawl_timestamp=datetime.now()
>             )
>             invalid_result.validate()
>
>     def test_extracted_content_contract(self):
>         """ExtractedContent契約の検証"""
>         # 正常系
>         content = ExtractedContent(
>             main_selector='.content',
>             main_content='This is the main content',
>             nav_selector='.nav',
>             nav_links=[{'text': 'Home', 'href': '/'}],
>             confidence=0.95
>         )
>         content.validate()
>
>         # 異常系：無効なconfidence
>         with pytest.raises(AssertionError, match="Confidence must be"):
>             invalid_content = ExtractedContent(
>                 main_selector='.content',
>                 main_content='Content',
>                 nav_selector=None,
>                 nav_links=[],
>                 confidence=1.5  # 契約違反
>             )
>             invalid_content.validate()
>
>     def test_converter_protocol_contract(self):
>         """変換器プロトコルの契約テスト"""
>         from site2.converter import MarkdownConverter
>
>         converter = MarkdownConverter()
>
>         # 事前条件のテスト
>         with pytest.raises(AssertionError):
>             # 空のファイルリスト（契約違反）
>             converter.convert([], OutputFormat.MARKDOWN)
>
>         # 正常系
>         with patch('pathlib.Path.exists', return_value=True):
>             files = [Path('/tmp/1.html'), Path('/tmp/2.html')]
>             result = converter.convert(files, OutputFormat.MARKDOWN)
>
>             # 事後条件の検証
>             assert isinstance(result, ConversionResult)
>             assert isinstance(result.content, str)
>             assert len(result.content) > 0
>
>
> class TestContractIntegration:
>     """契約ベースの統合テスト"""
>
>     def test_full_pipeline_contract(self):
>         """全体パイプラインの契約フロー"""
>         from site2.crawler import WgetCrawler
>         from site2.extractor import AIContentExtractor
>         from site2.sorter import NavigationSorter
>         from site2.converter import MarkdownConverter
>
>         # 各モジュールが契約に従っていることを検証
>         crawler = WgetCrawler()
>         extractor = AIContentExtractor()
>         sorter = NavigationSorter()
>         converter = MarkdownConverter()
>
>         # 1. Crawl契約
>         crawl_result = crawler.crawl('https://example.com')
>         crawl_result.validate()
>
>         # 2. Extract契約
>         for cached_file in crawl_result.cached_files:
>             extracted = extractor.extract_main_content(cached_file.local_path)
>             extracted.validate()
>
>         # 3. Sort契約
>         order = sorter.determine_order(crawl_result.cached_files)
>         order.validate()
>
>         # 4. Convert契約
>         result = converter.convert(order.files, OutputFormat.MARKDOWN)
>         result.validate()
>
>         # 全体の契約：入力URLから有効な出力が生成される
>         assert len(result.content) > 0
> ```

### 4. **開発フローでの運用方法**

> # Contract-First Development ワークフロー
>
> > ## 1. 新機能追加時のフロー
> >
> > ### Step 1: CLI契約の更新
> > ```yaml
> > # cli-contract.yaml に新コマンドを追加
> > - name: "site2 analyze"
> >   description: "Analyze website structure"
> >   arguments:
> >     - name: uri
> >       type: string
> >       required: true
> >   output:
> >     type: json
> >     schema:
> >       type: object
> >       properties:
> >         page_count: { type: integer }
> >         total_size: { type: integer }
> >         link_structure: { type: object }
> > ```
> >
> > ### Step 2: 内部契約の定義
> > ```python
> > # contracts.py に追加
> > @dataclass
> > class AnalysisResult:
> >     """サイト分析結果の契約"""
> >     page_count: int
> >     total_size: int
> >     link_structure: Dict[str, List[str]]
> >
> >     def validate(self):
> >         assert self.page_count > 0
> >         assert self.total_size > 0
> >
> > class AnalyzerProtocol(Protocol):
> >     """サイト分析器の契約"""
> >     def analyze(self, url: str) -> AnalysisResult:
> >         """事前条件: valid URL, 事後条件: valid AnalysisResult"""
> >         ...
> > ```
> >
> > ### Step 3: 契約テストの作成
> > ```python
> > # test_analyze_contract.py
> > def test_analyze_command_contract():
> >     """analyzeコマンドの契約テスト"""
> >     # 契約に基づいたテストを先に書く
> >     result = run_cli(['site2', 'analyze', 'https://example.com'])
> >     output = json.loads(result.stdout)
> >
> >     # 出力契約の検証
> >     assert 'page_count' in output
> >     assert isinstance(output['page_count'], int)
> >     assert output['page_count'] > 0
> > ```
> >
> > ### Step 4: 実装
> > ```python
> > # 契約を満たす実装を作成
> > class WebsiteAnalyzer:
> >     def analyze(self, url: str) -> AnalysisResult:
> >         # 実装...
> >         result = AnalysisResult(...)
> >         result.validate()  # 契約の確認
> >         return result
> > ```
> >
> > ## 2. AI との協調開発フロー
> >
> > ### Step 1: 契約定義を AI に提供
> > ```markdown
> > # AI への指示
> > 以下の契約に従って ContentExtractor を実装してください：
> >
> > 契約定義：
> > - 入力: HTMLファイルのパス
> > - 出力: ExtractedContent オブジェクト
> > - 事前条件: ファイルが存在し、有効なHTML
> > - 事後条件: main_content が空でない、confidence が 0-1
> >
> > 参照: contracts.py の ContentExtractorProtocol
> > ```
> >
> > ### Step 2: AI が生成したコードの契約検証
> > ```python
> > # AI生成コードのテスト
> > def test_ai_generated_extractor():
> >     extractor = AIGeneratedExtractor()
> >
> >     # 契約準拠の確認
> >     result = extractor.extract_main_content(Path('test.html'))
> >     assert isinstance(result, ExtractedContent)
> >     result.validate()  # 契約違反があれば例外
> > ```
> >
> > ## 3. 契約の自動検証
> >
> > ### GitHub Actions での契約検証
> > ```yaml
> > # .github/workflows/contract-validation.yml
> > name: Contract Validation
> > on: [push, pull_request]
> >
> > jobs:
> >   validate:
> >     steps:
> >       - name: Validate CLI contracts
> >         run: |
> >           python scripts/validate_cli_contract.py
> >
> >       - name: Run contract tests
> >         run: |
> >           pytest tests/test_contracts.py -v
> >
> >       - name: Check contract coverage
> >         run: |
> >           # すべての契約にテストがあることを確認
> >           python scripts/check_contract_coverage.py
> > ```
> >
> > ### 契約違反の自動検出
> > ```python
> > # scripts/validate_cli_contract.py
> > import yaml
> > import jsonschema
> >
> > def validate_cli_implementation():
> >     """CLI実装が契約に準拠しているか検証"""
> >     with open('cli-contract.yaml') as f:
> >         contract = yaml.safe_load(f)
> >
> >     for command in contract['commands']:
> >         # 実装が存在するか
> >         assert command_exists(command['name'])
> >
> >         # 引数・オプションが一致するか
> >         assert arguments_match(command)
> >
> >         # エラーコードが定義通りか
> >         assert error_codes_match(command)
> >
> > if __name__ == '__main__':
> >     validate_cli_implementation()
> > ```
> >
> > ## 4. 契約の進化
> >
> > ### 契約のバージョニング
> > ```yaml
> > # cli-contract-v2.yaml
> > version: 2.0.0
> > breaking_changes:
> >   - "Changed output format of fetch command"
> >   - "Removed --recursive option"
> >
> > migrations:
> >   - from: 1.0.0
> >     description: "Output format change"
> >     script: "migrations/v1_to_v2.py"
> > ```
> >
> > ### 後方互換性の維持
> > ```python
> > # 契約バージョンによる分岐
> > def handle_command(version: str):
> >     if version == "1.0.0":
> >         return V1Handler()
> >     elif version == "2.0.0":
> >         return V2Handler()
> >     else:
> >         raise UnsupportedVersionError()
> > ```
> >
> > ## 5. 契約ドキュメントの自動生成
> >
> > ```python
> > # scripts/generate_docs.py
> > def generate_cli_docs():
> >     """契約からCLIドキュメントを自動生成"""
> >     with open('cli-contract.yaml') as f:
> >         contract = yaml.safe_load(f)
> >
> >     docs = []
> >     for cmd in contract['commands']:
> >         docs.append(f"## {cmd['name']}")
> >         docs.append(f"{cmd['description']}")
> >         docs.append(f"### Arguments")
> >         # ... 引数、オプション、エラーコードを文書化
> >
> >     with open('docs/cli-reference.md', 'w') as f:
> >         f.write('\n'.join(docs))
> > ```
> >
> > ## まとめ
> >
> > Contract-First Development により：
> > 1. **仕様の明確化**: 実装前に入出力が確定
> > 2. **テストの自動化**: 契約からテストケースを生成
> > 3. **AI協調の改善**: 明確な仕様でAIへの指示が正確に
> > 4. **品質保証**: 契約違反を自動検出
> > 5. **ドキュメント同期**: 仕様と実装とドキュメントの一致
>
> ## Contract-First Development の具体的な運用例
>
> ### 実際の開発シナリオ
>
> 1. **新機能「サイト分析」を追加する場合**：
>
> ```bash
> # 1. 契約を定義
> vim cli-contract.yaml  # 新しいコマンドの契約を追加
>
> # 2. 契約からテストを生成
> python scripts/generate_contract_tests.py analyze
>
> # 3. テスト実行（当然失敗する）
> pytest tests/test_analyze_contract.py
>
> # 4. AIに契約を渡して実装を依頼
> cat contracts.py | claude "この契約に従ってAnalyzerを実装してください"
>
> # 5. 実装をテスト
> pytest tests/test_analyze_contract.py
>
> # 6. 契約準拠を確認
> python scripts/validate_contracts.py
> ```
>
> ### 最大のメリット
>
> 1. **AIとの協調**: 契約を渡すだけで正確な実装を依頼できる
> 2. **早期エラー検出**: 実装前に仕様の矛盾を発見
> 3. **自動テスト**: 契約からテストが自動生成される
> 4. **ドキュメント同期**: 契約がそのままAPIドキュメントになる
>
> この方法により、CLIツールでも Web API と同様に Contract-First で開発できます。特にAIを活用する際は、契約が「共通言語」として機能し、実装の品質と一貫性を保証できます。




# 13: user

実際に動かしてみないと理解が進まない
なんとなくイメージはつかめているが、地に足がついていないのが本音だ。

現在以下のドキュメント整備が進んでいないと認識している

- [x] 1. プロジェクト概要設計書
- [ ] 2. 要件定義書
- [ ] 3. アーキテクチャ設計書
- [ ] 4. 詳細設計書
  - [ ] 各モジュールの詳細仕様
    - [ ] Fetcher（取得機能）
    - [ ] Parser（解析機能）
    - [ ] Sorter（並び替え機能）
    - [ ] Converter（変換機能）
    - [ ] Builder（出力生成機能）
  - [ ] インターフェース定義
  - [ ] エラーコード体系
- [ ] 5. API/CLI設計書
- [ ] 6. データ設計書
- [ ] 7. テスト設計書
- [ ] 8. AI開発ガイドライン
- [ ] 9. 開発プロセス設計書
- [ ] 10. 運用・保守設計書

まずは単体ファイルのfetch機能の実装の中で、開発プラクティスを落とし込んでいきたい
ここではあくまで抽象度の高いところで進めていき、具象の実装をAIの自動実装に任せていきたい。

以下の主要機能がある
この中のfetchのみに焦点を当てて、各種開発プラクティスを実践していこう
手伝ってほしい

> [!Usage:]
>
>   site2 [--format <md|pdf>] <uri>
>       指定された uri からファイルを取得して1枚のファイルにまとめて標準出力に出力する
>       リカーシブに動作します
>
>   site2 fetch <uri>
>       指定された uri からファイルを取得してキャッシュする
>       キャッシュが存在するときは更新されたファイルだけを更新する
>       リカーシブに動作します
>
>   site2 fetch list
>       既に fetch 済みのキャッシュを一覧表示する
>
>   site2 detect main <file_or_uri>
>       ドキュメントのメインの文章ブロックへの CSS セレクタを返す
>
>   site2 detect nav <file_or_uri>
>       ドキュメントのナビゲーションブロックへの CSS セレクタを返す
>
>   site2 detect order <path_or_uri>
>       ドキュメントの一覧を出力順に標準出力に出力します
>
>   site2 build [--format <md|pdf>] <file_or_uri>...
>       指定されたファイルまたは uri を指定されたフォーマットに変換し、指定された順番にマージして標準出力に出力する




# 14: system

わかりました。実践的に進めましょう。`fetch`機能に焦点を当てて、各種開発プラクティスを段階的に適用していきます。

## Step 1: ドメインモデルの定義（DDD）

まず、`fetch`機能のドメインを理解し、モデル化します：

> ```python
> """
> site2 fetch機能のドメインモデル定義
> """
> from dataclasses import dataclass, field
> from datetime import datetime
> from pathlib import Path
> from typing import List, Optional, Set
> from urllib.parse import urlparse
> import hashlib
>
>
> # 値オブジェクト（Value Objects）
> @dataclass(frozen=True)
> class WebsiteURL:
>     """WebサイトのURL（値オブジェクト）"""
>     value: str
>
>     def __post_init__(self):
>         parsed = urlparse(self.value)
>         if not parsed.scheme in ('http', 'https'):
>             raise ValueError(f"Invalid URL scheme: {parsed.scheme}")
>         if not parsed.netloc:
>             raise ValueError(f"Invalid URL: {self.value}")
>
>     @property
>     def domain(self) -> str:
>         """ドメイン名を取得"""
>         return urlparse(self.value).netloc
>
>     @property
>     def slug(self) -> str:
>         """URL からキャッシュ用のスラッグを生成"""
>         # シンプルな実装: ドメイン名 + パスのハッシュ
>         parsed = urlparse(self.value)
>         path_hash = hashlib.md5(parsed.path.encode()).hexdigest()[:8]
>         return f"{parsed.netloc}_{path_hash}"
>
>
> @dataclass(frozen=True)
> class CrawlDepth:
>     """クロールの深さ（値オブジェクト）"""
>     value: int
>
>     def __post_init__(self):
>         if not 0 <= self.value <= 10:
>             raise ValueError(f"Depth must be between 0 and 10, got {self.value}")
>
>
> # エンティティ（Entities）
> @dataclass
> class CachedPage:
>     """キャッシュされたページ（エンティティ）"""
>     page_url: WebsiteURL
>     local_path: Path
>     content_type: str
>     size_bytes: int
>     fetched_at: datetime
>     last_modified: Optional[datetime] = None
>     etag: Optional[str] = None
>
>     @property
>     def id(self) -> str:
>         """エンティティの識別子"""
>         return str(self.page_url.value)
>
>     def is_stale(self, cache_duration_hours: int = 24) -> bool:
>         """キャッシュが古いかどうか判定"""
>         age = datetime.now() - self.fetched_at
>         return age.total_seconds() > cache_duration_hours * 3600
>
>
> @dataclass
> class WebsiteCache:
>     """Webサイトのキャッシュ（集約ルート）"""
>     root_url: WebsiteURL
>     cache_directory: Path
>     pages: List[CachedPage] = field(default_factory=list)
>     crawl_depth: CrawlDepth = CrawlDepth(3)
>     created_at: datetime = field(default_factory=datetime.now)
>     last_updated: datetime = field(default_factory=datetime.now)
>
>     @property
>     def id(self) -> str:
>         """集約の識別子"""
>         return self.root_url.slug
>
>     @property
>     def total_size(self) -> int:
>         """キャッシュの合計サイズ"""
>         return sum(page.size_bytes for page in self.pages)
>
>     @property
>     def page_count(self) -> int:
>         """キャッシュされたページ数"""
>         return len(self.pages)
>
>     def add_page(self, page: CachedPage) -> None:
>         """ページを追加（ビジネスルール）"""
>         # 同じURLのページは上書き
>         self.pages = [p for p in self.pages if p.id != page.id]
>         self.pages.append(page)
>         self.last_updated = datetime.now()
>
>     def get_stale_pages(self, cache_duration_hours: int = 24) -> List[CachedPage]:
>         """古いページを取得"""
>         return [p for p in self.pages if p.is_stale(cache_duration_hours)]
>
>     def get_page_urls(self) -> Set[str]:
>         """キャッシュ済みページのURL一覧"""
>         return {page.page_url.value for page in self.pages}
>
>
> # ドメインイベント（Domain Events）
> @dataclass
> class PageFetched:
>     """ページ取得完了イベント"""
>     website_cache_id: str
>     page_url: str
>     size_bytes: int
>     timestamp: datetime = field(default_factory=datetime.now)
>
>
> @dataclass
> class CacheCreated:
>     """キャッシュ作成イベント"""
>     website_cache_id: str
>     root_url: str
>     timestamp: datetime = field(default_factory=datetime.now)
>
>
> @dataclass
> class CacheUpdated:
>     """キャッシュ更新イベント"""
>     website_cache_id: str
>     updated_pages: int
>     timestamp: datetime = field(default_factory=datetime.now)
> ```

## Step 2: 契約定義（Contract-First）

fetch機能の契約を定義します：

> ```python
> """
> site2 fetch機能の契約定義（Contract-First Development）
> """
> from typing import Protocol, List, Optional, Dict, Any
> from pathlib import Path
> from dataclasses import dataclass
> from datetime import datetime
>
> from fetch_domain import WebsiteURL, WebsiteCache, CrawlDepth, CachedPage
>
>
> # DTOs (Data Transfer Objects) - 外部とのやり取り用
> @dataclass
> class FetchRequest:
>     """Fetch要求の契約"""
>     url: str
>     depth: int = 3
>     force_refresh: bool = False
>     cache_dir: Optional[str] = None
>
>     def validate(self) -> None:
>         """契約の事前条件を検証"""
>         # URLの検証はWebsiteURLに委譲
>         WebsiteURL(self.url)
>         # 深さの検証はCrawlDepthに委譲
>         CrawlDepth(self.depth)
>
>
> @dataclass
> class FetchResult:
>     """Fetch結果の契約"""
>     cache_id: str
>     root_url: str
>     pages_fetched: int
>     pages_updated: int
>     total_size: int
>     cache_directory: str
>     errors: List[Dict[str, str]] = field(default_factory=list)
>
>     def validate(self) -> None:
>         """契約の事後条件を検証"""
>         assert self.pages_fetched >= 0, "pages_fetched must be non-negative"
>         assert self.pages_updated >= 0, "pages_updated must be non-negative"
>         assert self.total_size >= 0, "total_size must be non-negative"
>         assert Path(self.cache_directory).exists(), f"Cache directory must exist: {self.cache_directory}"
>
>
> @dataclass
> class CacheListResult:
>     """キャッシュ一覧の契約"""
>     caches: List[Dict[str, Any]]
>
>     def validate(self) -> None:
>         """契約の事後条件を検証"""
>         for cache in self.caches:
>             assert 'id' in cache, "Each cache must have an id"
>             assert 'url' in cache, "Each cache must have a url"
>             assert 'page_count' in cache, "Each cache must have page_count"
>             assert 'total_size' in cache, "Each cache must have total_size"
>             assert 'last_updated' in cache, "Each cache must have last_updated"
>
>
> # サービスインターフェース（ポート）
> class FetchServiceProtocol(Protocol):
>     """Fetchサービスの契約"""
>
>     def fetch(self, request: FetchRequest) -> FetchResult:
>         """
>         WebサイトをFetchしてキャッシュする
>
>         事前条件:
>         - request.url は有効なHTTP(S) URL
>         - request.depth は 0-10 の範囲
>         - cache_dir が指定されている場合は書き込み可能
>
>         事後条件:
>         - FetchResultが返される
>         - cache_directoryが存在する
>         - 少なくとも1ページ（ルートページ）がフェッチされる（エラーがない限り）
>
>         例外:
>         - NetworkError: ネットワーク接続に失敗
>         - PermissionError: キャッシュディレクトリへの書き込み権限がない
>         """
>         ...
>
>     def list_caches(self) -> CacheListResult:
>         """
>         キャッシュ済みサイトの一覧を取得
>
>         事前条件:
>         - なし
>
>         事後条件:
>         - CacheListResultが返される
>         - 各キャッシュ情報が完全である
>         """
>         ...
>
>
> # リポジトリインターフェース（ポート）
> class WebsiteCacheRepositoryProtocol(Protocol):
>     """キャッシュリポジトリの契約"""
>
>     def save(self, cache: WebsiteCache) -> None:
>         """
>         キャッシュを保存
>
>         事前条件:
>         - cache は有効なWebsiteCacheインスタンス
>
>         事後条件:
>         - キャッシュがファイルシステムに保存される
>         - メタデータが更新される
>         """
>         ...
>
>     def find_by_url(self, url: WebsiteURL) -> Optional[WebsiteCache]:
>         """
>         URLでキャッシュを検索
>
>         事前条件:
>         - url は有効なWebsiteURL
>
>         事後条件:
>         - 存在する場合はWebsiteCacheを返す
>         - 存在しない場合はNoneを返す
>         """
>         ...
>
>     def find_all(self) -> List[WebsiteCache]:
>         """
>         すべてのキャッシュを取得
>
>         事前条件:
>         - なし
>
>         事後条件:
>         - すべてのキャッシュのリストを返す（空の可能性あり）
>         """
>         ...
>
>
> # クローラーインターフェース（ポート）
> class WebCrawlerProtocol(Protocol):
>     """Webクローラーの契約"""
>
>     def crawl(self, url: WebsiteURL, depth: CrawlDepth,
>               existing_cache: Optional[WebsiteCache] = None) -> List[CachedPage]:
>         """
>         Webサイトをクロール
>
>         事前条件:
>         - url は有効なWebsiteURL
>         - depth は有効なCrawlDepth
>
>         事後条件:
>         - クロールされたページのリストを返す
>         - 各ページは local_path にダウンロードされている
>
>         例外:
>         - NetworkError: ネットワーク接続に失敗
>         - TooManyRequestsError: レート制限に達した
>         """
>         ...
>
>
> # エラー定義
> class FetchError(Exception):
>     """Fetch機能の基底エラー"""
>     code: str = "FETCH_ERROR"
>
>
> class NetworkError(FetchError):
>     """ネットワークエラー"""
>     code: str = "NETWORK_ERROR"
>
>
> class InvalidURLError(FetchError):
>     """無効なURLエラー"""
>     code: str = "INVALID_URL"
>
>
> class CachePermissionError(FetchError):
>     """キャッシュ権限エラー"""
>     code: str = "CACHE_PERMISSION_ERROR"
> ```

## Step 3: BDDシナリオの定義

ユーザー視点での振る舞いを定義：

> ```gherkin
> # fetch_scenarios.feature
> Feature: Webサイトのフェッチとキャッシュ
>   ユーザーとして
>   Webサイトのコンテンツをローカルにキャッシュしたい
>   オフラインでも参照できるようにするため
>
>   Background:
>     Given キャッシュディレクトリ "~/.cache/site2" が存在する
>     And ネットワーク接続が利用可能である
>
>   Scenario: 新規サイトのフェッチ
>     Given "https://example.com" はまだキャッシュされていない
>     When コマンド "site2 fetch https://example.com" を実行する
>     Then 終了コード 0 で正常終了する
>     And 標準出力に以下を含む:
>       """
>       ✅ Fetched: https://example.com
>       Pages: 15
>       Total size: 1.2 MB
>       Cache: ~/.cache/site2/example.com_a1b2c3d4
>       """
>     And キャッシュディレクトリ "~/.cache/site2/example.com_a1b2c3d4" が作成される
>     And メタデータファイル "cache.json" が存在する
>
>   Scenario: キャッシュ済みサイトの差分更新
>     Given "https://example.com" は24時間前にキャッシュされている
>     And サイトの "/docs/new-page.html" が追加されている
>     When コマンド "site2 fetch https://example.com" を実行する
>     Then 終了コード 0 で正常終了する
>     And 標準出力に以下を含む:
>       """
>       🔄 Updating cache: https://example.com
>       New pages: 1
>       Updated pages: 3
>       Total size: 1.3 MB
>       """
>     And 新しいページ "/docs/new-page.html" がキャッシュされる
>     And 更新されたページのタイムスタンプが更新される
>
>   Scenario: 深さ制限付きフェッチ
>     Given "https://example.com" はまだキャッシュされていない
>     When コマンド "site2 fetch https://example.com --depth 1" を実行する
>     Then 終了コード 0 で正常終了する
>     And ルートページとその直接リンクのみがキャッシュされる
>     And 深さ2以上のページはキャッシュされない
>
>   Scenario: キャッシュ一覧の表示
>     Given 以下のサイトがキャッシュされている:
>       | url                    | pages | size    | last_updated        |
>       | https://example.com    | 15    | 1.2 MB  | 2025-01-05 10:00:00 |
>       | https://docs.python.org| 250   | 45.3 MB | 2025-01-04 15:30:00 |
>     When コマンド "site2 fetch list" を実行する
>     Then 終了コード 0 で正常終了する
>     And 標準出力に以下を含む:
>       """
>       📦 Cached sites:
>
>       1. https://example.com
>          Pages: 15 | Size: 1.2 MB | Updated: 2025-01-05 10:00:00
>          Cache: ~/.cache/site2/example.com_a1b2c3d4
>
>       2. https://docs.python.org
>          Pages: 250 | Size: 45.3 MB | Updated: 2025-01-04 15:30:00
>          Cache: ~/.cache/site2/docs.python.org_e5f6g7h8
>
>       Total: 2 sites, 265 pages, 46.5 MB
>       """
>
>   Scenario: 無効なURLのエラー処理
>     When コマンド "site2 fetch not-a-url" を実行する
>     Then 終了コード 1 でエラー終了する
>     And 標準エラー出力に以下を含む:
>       """
>       ❌ Error: Invalid URL format
>       URL must start with http:// or https://
>       """
>
>   Scenario: ネットワークエラーの処理
>     Given "https://unreachable.example.com" はアクセスできない
>     When コマンド "site2 fetch https://unreachable.example.com" を実行する
>     Then 終了コード 1 でエラー終了する
>     And 標準エラー出力に以下を含む:
>       """
>       ❌ Error: Failed to connect to https://unreachable.example.com
>       Network error: Connection refused
>       """
>
>   Scenario: 強制リフレッシュ
>     Given "https://example.com" は1時間前にキャッシュされている
>     When コマンド "site2 fetch https://example.com --force" を実行する
>     Then すべてのページが再取得される
>     And 標準出力に以下を含む:
>       """
>       🔄 Force refresh: https://example.com
>       All pages will be re-fetched
>       """
> ```

## Step 4: TDDテストの作成

契約とBDDシナリオに基づいたテストを先に作成：

> ```python
> """
> site2 fetch機能のテスト（TDD）
> """
> import pytest
> from pathlib import Path
> from datetime import datetime, timedelta
> from unittest.mock import Mock, patch, MagicMock
> import json
>
> from fetch_domain import WebsiteURL, WebsiteCache, CrawlDepth, CachedPage
> from fetch_contracts import (
>     FetchRequest, FetchResult, CacheListResult,
>     FetchServiceProtocol, WebsiteCacheRepositoryProtocol,
>     InvalidURLError, NetworkError
> )
>
>
> class TestDomainModel:
>     """ドメインモデルのテスト"""
>
>     def test_website_url_valid(self):
>         """有効なURLの作成"""
>         url = WebsiteURL("https://example.com")
>         assert url.value == "https://example.com"
>         assert url.domain == "example.com"
>         assert url.slug == "example.com_7d793037"  # MD5ハッシュの一部
>
>     def test_website_url_invalid(self):
>         """無効なURLは例外を発生"""
>         with pytest.raises(ValueError, match="Invalid URL scheme"):
>             WebsiteURL("ftp://example.com")
>
>         with pytest.raises(ValueError, match="Invalid URL"):
>             WebsiteURL("not-a-url")
>
>     def test_crawl_depth_valid(self):
>         """有効な深さの作成"""
>         depth = CrawlDepth(3)
>         assert depth.value == 3
>
>     def test_crawl_depth_invalid(self):
>         """無効な深さは例外を発生"""
>         with pytest.raises(ValueError, match="Depth must be between"):
>             CrawlDepth(11)
>
>     def test_cached_page_staleness(self):
>         """ページの古さ判定"""
>         # 25時間前のページ
>         old_page = CachedPage(
>             page_url=WebsiteURL("https://example.com/page1.html"),
>             local_path=Path("/cache/page1.html"),
>             content_type="text/html",
>             size_bytes=1024,
>             fetched_at=datetime.now() - timedelta(hours=25)
>         )
>         assert old_page.is_stale(cache_duration_hours=24)
>
>         # 1時間前のページ
>         fresh_page = CachedPage(
>             page_url=WebsiteURL("https://example.com/page2.html"),
>             local_path=Path("/cache/page2.html"),
>             content_type="text/html",
>             size_bytes=1024,
>             fetched_at=datetime.now() - timedelta(hours=1)
>         )
>         assert not fresh_page.is_stale(cache_duration_hours=24)
>
>     def test_website_cache_operations(self):
>         """Webサイトキャッシュの操作"""
>         cache = WebsiteCache(
>             root_url=WebsiteURL("https://example.com"),
>             cache_directory=Path("/cache/example.com")
>         )
>
>         # ページ追加
>         page1 = CachedPage(
>             page_url=WebsiteURL("https://example.com/page1.html"),
>             local_path=Path("/cache/page1.html"),
>             content_type="text/html",
>             size_bytes=1024,
>             fetched_at=datetime.now()
>         )
>         cache.add_page(page1)
>
>         assert cache.page_count == 1
>         assert cache.total_size == 1024
>
>         # 同じURLのページを追加（上書き）
>         page1_updated = CachedPage(
>             page_url=WebsiteURL("https://example.com/page1.html"),
>             local_path=Path("/cache/page1.html"),
>             content_type="text/html",
>             size_bytes=2048,
>             fetched_at=datetime.now()
>         )
>         cache.add_page(page1_updated)
>
>         assert cache.page_count == 1  # 上書きされたので1のまま
>         assert cache.total_size == 2048  # サイズは更新
>
>
> class TestFetchContracts:
>     """契約のテスト"""
>
>     def test_fetch_request_validation(self):
>         """FetchRequest の契約検証"""
>         # 正常系
>         request = FetchRequest(url="https://example.com", depth=3)
>         request.validate()  # 例外が発生しないこと
>
>         # 異常系：無効なURL
>         with pytest.raises(ValueError):
>             request = FetchRequest(url="invalid-url")
>             request.validate()
>
>         # 異常系：無効な深さ
>         with pytest.raises(ValueError):
>             request = FetchRequest(url="https://example.com", depth=11)
>             request.validate()
>
>     def test_fetch_result_validation(self):
>         """FetchResult の契約検証"""
>         with patch('pathlib.Path.exists', return_value=True):
>             # 正常系
>             result = FetchResult(
>                 cache_id="example.com_12345678",
>                 root_url="https://example.com",
>                 pages_fetched=10,
>                 pages_updated=2,
>                 total_size=1024000,
>                 cache_directory="/cache/example.com"
>             )
>             result.validate()
>
>         # 異常系：負の値
>         with pytest.raises(AssertionError):
>             result = FetchResult(
>                 cache_id="example.com_12345678",
>                 root_url="https://example.com",
>                 pages_fetched=-1,  # 負の値
>                 pages_updated=0,
>                 total_size=0,
>                 cache_directory="/cache/example.com"
>             )
>             result.validate()
>
>
> class TestFetchService:
>     """Fetchサービスのテスト（モックを使用）"""
>
>     @pytest.fixture
>     def mock_repository(self):
>         """モックリポジトリ"""
>         return Mock(spec=WebsiteCacheRepositoryProtocol)
>
>     @pytest.fixture
>     def mock_crawler(self):
>         """モッククローラー"""
>         return Mock(spec=WebCrawlerProtocol)
>
>     @pytest.fixture
>     def fetch_service(self, mock_repository, mock_crawler):
>         """テスト対象のサービス（実装はまだない）"""
>         # 実装クラスはまだ存在しないので、ここではモックを返す
>         service = Mock(spec=FetchServiceProtocol)
>
>         # fetch メソッドの振る舞いを定義
>         def fetch_impl(request):
>             # 契約に従った振る舞いをモック
>             request.validate()
>
>             url = WebsiteURL(request.url)
>             depth = CrawlDepth(request.depth)
>
>             # キャッシュ作成
>             cache = WebsiteCache(
>                 root_url=url,
>                 cache_directory=Path(f"/cache/{url.slug}")
>             )
>
>             # ページ追加
>             pages = [
>                 CachedPage(
>                     page_url=url,
>                     local_path=Path(f"/cache/{url.slug}/index.html"),
>                     content_type="text/html",
>                     size_bytes=1024,
>                     fetched_at=datetime.now()
>                 )
>             ]
>             for page in pages:
>                 cache.add_page(page)
>
>             return FetchResult(
>                 cache_id=cache.id,
>                 root_url=request.url,
>                 pages_fetched=1,
>                 pages_updated=0,
>                 total_size=cache.total_size,
>                 cache_directory=str(cache.cache_directory)
>             )
>
>         service.fetch.side_effect = fetch_impl
>         return service
>
>     def test_fetch_new_site(self, fetch_service):
>         """新規サイトのフェッチ"""
>         # Arrange
>         request = FetchRequest(url="https://example.com")
>
>         # Act
>         with patch('pathlib.Path.exists', return_value=True):
>             result = fetch_service.fetch(request)
>
>         # Assert
>         assert result.pages_fetched >= 1
>         assert result.pages_updated == 0
>         assert result.total_size > 0
>         result.validate()  # 契約の確認
>
>     def test_fetch_invalid_url(self, fetch_service):
>         """無効なURLでのフェッチ"""
>         # Arrange
>         request = FetchRequest(url="not-a-url")
>
>         # Act & Assert
>         with pytest.raises(ValueError):
>             fetch_service.fetch(request)
>
>     def test_list_caches(self, fetch_service):
>         """キャッシュ一覧の取得"""
>         # Arrange
>         def list_caches_impl():
>             return CacheListResult(
>                 caches=[
>                     {
>                         'id': 'example.com_12345678',
>                         'url': 'https://example.com',
>                         'page_count': 15,
>                         'total_size': 1234567,
>                         'last_updated': '2025-01-05T10:00:00'
>                     }
>                 ]
>             )
>
>         fetch_service.list_caches.side_effect = list_caches_impl
>
>         # Act
>         result = fetch_service.list_caches()
>
>         # Assert
>         assert len(result.caches) == 1
>         result.validate()  # 契約の確認
>
>
> class TestCLIIntegration:
>     """CLIとの統合テスト（E2E風）"""
>
>     def test_cli_fetch_command(self):
>         """CLI fetch コマンドのテスト"""
>         # この段階では CLI 実装がないので、期待する振る舞いを定義
>         from click.testing import CliRunner
>
>         # 期待する CLI の振る舞い
>         expected_cli = Mock()
>         expected_cli.return_value = 0  # 終了コード
>
>         runner = CliRunner()
>         with patch('site2.cli.fetch_command', expected_cli):
>             result = runner.invoke(expected_cli, ['https://example.com'])
>
>             assert result.exit_code == 0
>             expected_cli.assert_called_once()
>
>     def test_cli_list_command(self):
>         """CLI list コマンドのテスト"""
>         from click.testing import CliRunner
>
>         expected_cli = Mock()
>         expected_cli.return_value = 0
>
>         runner = CliRunner()
>         with patch('site2.cli.list_command', expected_cli):
>             result = runner.invoke(expected_cli, [])
>
>             assert result.exit_code == 0
> ```

## Step 5: プロジェクト構造の定義

Clean Architecture に基づいた構造：

> # site2 プロジェクト構造
>
> ```
> site2/
> ├── pyproject.toml              # プロジェクト設定
> ├── README.md                   # プロジェクト説明
> ├── Makefile                    # 開発タスク自動化
> ├── .github/
> │   └── workflows/
> │       ├── ci.yml             # CI/CD設定
> │       └── contract-check.yml # 契約検証
> │
> ├── contracts/                  # 契約定義
> │   ├── cli-contract.yaml      # CLI契約
> │   ├── fetch-contract.yaml    # Fetch機能契約
> │   └── README.md
> │
> ├── docs/                       # ドキュメント
> │   ├── architecture/          # アーキテクチャ決定記録
> │   │   └── decisions/
> │   │       ├── 001-use-wget.md
> │   │       └── 002-clean-architecture.md
> │   ├── api/                   # API仕様
> │   └── guides/                # 利用ガイド
> │
> ├── src/
> │   └── site2/
> │       ├── __init__.py
> │       ├── cli.py             # CLIエントリーポイント
> │       │
> │       ├── core/              # ビジネスロジック（外部依存なし）
> │       │   ├── __init__.py
> │       │   ├── domain/        # ドメインモデル
> │       │   │   ├── __init__.py
> │       │   │   ├── fetch_domain.py
> │       │   │   └── common.py
> │       │   ├── use_cases/     # ユースケース
> │       │   │   ├── __init__.py
> │       │   │   └── fetch_service.py
> │       │   └── ports/         # インターフェース定義
> │       │       ├── __init__.py
> │       │       ├── fetch_contracts.py
> │       │       └── repositories.py
> │       │
> │       ├── adapters/          # 外部システムとの接続
> │       │   ├── __init__.py
> │       │   ├── cli/           # CLI実装
> │       │   │   ├── __init__.py
> │       │   │   └── fetch_command.py
> │       │   ├── crawlers/      # クローラー実装
> │       │   │   ├── __init__.py
> │       │   │   └── wget_crawler.py
> │       │   └── storage/       # ストレージ実装
> │       │       ├── __init__.py
> │       │       └── file_repository.py
> │       │
> │       └── config/            # 設定
> │           ├── __init__.py
> │           └── settings.py
> │
> ├── tests/
> │   ├── __init__.py
> │   ├── conftest.py            # pytest設定
> │   ├── unit/                  # 単体テスト
> │   │   ├── core/
> │   │   │   ├── domain/
> │   │   │   │   └── test_fetch_domain.py
> │   │   │   └── use_cases/
> │   │   │       └── test_fetch_service.py
> │   │   └── adapters/
> │   │       ├── crawlers/
> │   │       │   └── test_wget_crawler.py
> │   │       └── storage/
> │   │           └── test_file_repository.py
> │   ├── integration/           # 統合テスト
> │   │   └── test_fetch_integration.py
> │   ├── e2e/                   # エンドツーエンドテスト
> │   │   └── test_cli_fetch.py
> │   └── fixtures/              # テストデータ
> │       └── sample_sites/
> │
> ├── features/                   # BDDシナリオ
> │   ├── fetch.feature
> │   └── steps/
> │       └── fetch_steps.py
> │
> └── scripts/                    # 開発支援スクリプト
>     ├── validate_contracts.py   # 契約検証
>     ├── generate_tests.py       # テスト生成
>     └── check_coverage.py       # カバレッジ確認
> ```
>
> ## レイヤー構造の説明
>
> ### 1. Core層（ビジネスロジック）
> - **domain/**: エンティティ、値オブジェクト、ドメインイベント
> - **use_cases/**: アプリケーションのユースケース
> - **ports/**: インターフェース定義（依存性逆転の原則）
>
> ### 2. Adapters層（外部システム連携）
> - **cli/**: コマンドラインインターフェース
> - **crawlers/**: Webクローラー実装
> - **storage/**: ファイルシステムアクセス
>
> ### 3. 契約とテスト
> - **contracts/**: すべての契約定義
> - **tests/**: レベル別のテスト
> - **features/**: BDDシナリオ
>
> ## 依存関係の方向
>
> ```
> CLI → UseCase → Domain
>  ↓        ↓
> Crawler  Repository
> ```
>
> - 内側（Domain）は外側に依存しない
> - 外側は内側のインターフェースに依存
> - 具象実装は実行時に注入される

## Step 6: Makefile で開発フローを自動化

> ```makefile
> # site2 開発タスク自動化
>
> .PHONY: help setup test lint format clean
>
> help: ## ヘルプを表示
> 	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
>
> setup: ## 開発環境をセットアップ
> 	rye sync
> 	rye run pre-commit install
>
> # --- 契約駆動開発 ---
> contract-validate: ## 契約の妥当性を検証
> 	python scripts/validate_contracts.py
>
> contract-generate-tests: ## 契約からテストを生成
> 	python scripts/generate_tests.py fetch
>
> contract-check: ## 実装が契約に準拠しているか確認
> 	python scripts/check_contract_compliance.py
>
> # --- テスト駆動開発 ---
> test-unit: ## 単体テストを実行
> 	rye run pytest tests/unit -v
>
> test-integration: ## 統合テストを実行
> 	rye run pytest tests/integration -v
>
> test-e2e: ## E2Eテストを実行
> 	rye run pytest tests/e2e -v
>
> test-bdd: ## BDDシナリオを実行
> 	rye run behave features/
>
> test: test-unit test-integration ## すべてのテストを実行
>
> test-watch: ## ファイル変更を監視してテストを自動実行
> 	rye run ptw tests/unit -- -v
>
> coverage: ## テストカバレッジを計測
> 	rye run pytest --cov=src/site2 --cov-report=html --cov-report=term
>
> # --- AI開発支援 ---
> ai-generate-impl: ## AIに実装を生成させる
> 	@echo "Generating implementation for fetch module..."
> 	@cat contracts/fetch-contract.yaml src/site2/core/ports/fetch_contracts.py | \
> 	  llm "Based on these contracts, implement the FetchService class following Clean Architecture principles"
>
> ai-review: ## AIにコードレビューを依頼
> 	@echo "Requesting AI code review..."
> 	@git diff --cached | llm "Review this code for: 1) Contract compliance 2) Clean Architecture 3) Error handling 4) Test coverage"
>
> # --- 開発フロー ---
> dev-fetch: ## fetch機能の開発フロー
> 	@echo "=== Fetch機能の開発フロー ==="
> 	@echo "1. 契約の検証"
> 	@make contract-validate
> 	@echo "\n2. テストの生成と実行（失敗することを確認）"
> 	@make test-unit || true
> 	@echo "\n3. 実装の生成（AIまたは手動）"
> 	@echo "   make ai-generate-impl"
> 	@echo "\n4. テストの実行（成功することを確認）"
> 	@echo "   make test-unit"
> 	@echo "\n5. 契約準拠の確認"
> 	@echo "   make contract-check"
>
> # --- コード品質 ---
> lint: ## コードのリント
> 	rye run ruff check src tests
> 	rye run mypy src
>
> format: ## コードのフォーマット
> 	rye run black src tests
> 	rye run isort src tests
>
> # --- ドキュメント ---
> docs-contracts: ## 契約からドキュメントを生成
> 	python scripts/generate_docs_from_contracts.py
>
> docs-serve: ## ドキュメントをローカルで表示
> 	mkdocs serve
>
> # --- クリーンアップ ---
> clean: ## 生成ファイルを削除
> 	find . -type d -name __pycache__ -exec rm -rf {} +
> 	find . -type f -name "*.pyc" -delete
> 	rm -rf .pytest_cache .coverage htmlcov .ruff_cache
>
> # --- 便利なコマンド ---
> repl: ## Python REPLを起動（プロジェクトをインポート済み）
> 	rye run ipython -i -c "from site2.core.domain.fetch_domain import *; from site2.core.ports.fetch_contracts import *"
>
> validate-all: contract-validate lint test ## すべての検証を実行
> ```

## Step 7: AI実装ガイドライン

AIに実装を依頼する際のガイドライン：

> ```markdown
> # AI実装ガイドライン - Fetch機能
>
> ## 1. AIへの実装依頼テンプレート
>
> > ```markdown
> > ## 実装依頼: [モジュール名]
> >
> > ### 契約定義
> > [contracts/fetch-contract.yaml の内容]
> > [src/site2/core/ports/fetch_contracts.py の内容]
> >
> > ### 実装要件
> > 1. 上記の契約に完全に準拠すること
> > 2. Clean Architectureの原則に従うこと
> > 3. 外部依存は抽象化すること
> > 4. エラーハンドリングを適切に行うこと
> > 5. ログを適切に出力すること
> >
> > ### 実装するクラス/関数
> > - クラス名: `FetchService`
> > - 実装場所: `src/site2/core/use_cases/fetch_service.py`
> > - 依存: `WebsiteCacheRepositoryProtocol`, `WebCrawlerProtocol`
> >
> > ### テストケース
> > 以下のテストがパスすること：
> > - `tests/unit/core/use_cases/test_fetch_service.py`
> >
> > ### 制約事項
> > - wgetコマンドは`subprocess`で呼び出すこと
> > - キャッシュディレクトリは設定可能にすること
> > - 並行ダウンロードは3接続まで
> > ```
>
> ## 2. 段階的な実装アプローチ
>
> ### Phase 1: 最小実装（MVP）
>
> > ```python
> > # AIへの指示例
> > """
> > FetchServiceの最小実装を作成してください：
> > 1. 単一ページのダウンロードのみ
> > 2. エラーハンドリングは基本的なもののみ
> > 3. テストがパスすることを優先
> > """
> > ```
>
> ### Phase 2: 機能拡張
>
> > ```python
> > # AIへの指示例
> > """
> > 以下の機能を追加してください：
> > 1. 再帰的なクロール（depth制御）
> > 2. 差分更新（If-Modified-Since）
> > 3. 進捗表示
> > """
> > ```
>
> ### Phase 3: 最適化
>
> > ```python
> > # AIへの指示例
> > """
> > 以下の最適化を行ってください：
> > 1. 並行ダウンロード
> > 2. メモリ効率の改善
> > 3. キャッシュ戦略の改善
> > """
> > ```
>
> ## 3. コードレビューチェックリスト
>
> AIが生成したコードをレビューする際のチェックリスト：
>
> - [ ] 契約（Contract）に準拠しているか
> - [ ] ドメインロジックに外部依存が混入していないか
> - [ ] エラーハンドリングが適切か
> - [ ] ログ出力が適切か
> - [ ] テストがすべてパスするか
> - [ ] 型ヒントが正しく付けられているか
> - [ ] docstringが適切か
>
> ## 4. よくある問題と対処法
>
> ### 問題1: 外部依存の直接利用
>
> > ```python
> > # ❌ 悪い例
> > class FetchService:
> >     def fetch(self, request):
> >         subprocess.run(['wget', ...])  # 直接外部コマンドを呼んでいる
> >
> > # ✅ 良い例
> > class FetchService:
> >     def __init__(self, crawler: WebCrawlerProtocol):
> >         self.crawler = crawler
> >
> >     def fetch(self, request):
> >         pages = self.crawler.crawl(...)  # 抽象に依存
> > ```
>
> ### 問題2: 契約違反
>
> > ```python
> > # ❌ 悪い例
> > def fetch(self, url: str):  # 契約はFetchRequestを要求
> >
> > # ✅ 良い例
> > def fetch(self, request: FetchRequest):  # 契約通り
> > ```
>
> ### 問題3: エラーの握りつぶし
> > ```python
> > # ❌ 悪い例
> > try:
> >     result = dangerous_operation()
> > except Exception:
> >     pass  # エラーを無視
> >
> > # ✅ 良い例
> > try:
> >     result = dangerous_operation()
> > except NetworkError as e:
> >     logger.error(f"Network error: {e}")
> >     raise  # 適切に再発生
> > ```
>
> ## 5. AI実装のワークフロー
>
> > ```mermaid
> > graph TD
> >     A[契約定義] --> B[テスト作成]
> >     B --> C[AI実装依頼]
> >     C --> D[コード生成]
> >     D --> E[自動テスト]
> >     E --> F{テスト成功?}
> >     F -->|No| G[AI修正依頼]
> >     G --> D
> >     F -->|Yes| H[契約準拠確認]
> >     H --> I[コードレビュー]
> >     I --> J[マージ]
> > ```
>
> ## 6. プロンプトエンジニアリング
>
> ### 効果的なプロンプトの例
>
> > ```markdown
> > # Context
> > You are implementing a web crawler service for the site2 project.
> > The project follows Clean Architecture and Contract-First Development.
> >
> > # Task
> > Implement the FetchService class that:
> > 1. Implements the FetchServiceProtocol interface
> > 2. Uses dependency injection for external dependencies
> > 3. Follows the single responsibility principle
> > 4. Has comprehensive error handling
> >
> > # Constraints
> > - Do not use external libraries except standard library
> > - Use type hints for all parameters and return values
> > - Include docstrings with pre/post conditions
> > - Log all important operations
> >
> > # Input
> > [契約定義をここに貼る]
> >
> > # Expected Output
> > Complete implementation of FetchService class
> > ```
>
> ## 7. 品質保証
>
> ### 自動チェック
> > ```bash
> > # 契約準拠の自動確認
> > make contract-check
> >
> > # 型チェック
> > make lint
> >
> > # テストカバレッジ
> > make coverage
> > ```
>
> ### 手動チェック
> 1. コードの可読性
> 2. 変数名の適切さ
> 3. コメントの質
> 4. エッジケースの考慮
> ```

## Step 8: 実際の開発フローの実行例

> ```markdown
> # Fetch機能の開発フロー実行例
>
> ## 1. 開発の開始
>
> ```bash
> > # リポジトリのセットアップ
> > git clone https://github.com/boarnasia/site2
> > cd site2
> >
> > # 開発環境のセットアップ
> > make setup
> >
> > # fetch機能の開発ブランチを作成
> > git checkout -b feature/fetch-implementation
> ```
>
> ## 2. 契約の確認と検証
>
> ```bash
> > # 契約の検証
> > make contract-validate
> >
> > # 出力例：
> > ✅ CLI contract validation passed
> > ✅ Fetch contract validation passed
> > ✅ All contracts are valid
> ```
>
> ## 3. テストの実行（最初は失敗）
>
> ```bash
> > # 単体テストの実行
> > make test-unit
> >
> > # 出力例：
> > ====== FAILURES ======
> > test_fetch_new_site - ModuleNotFoundError: No module named 'site2.core.use_cases'
> > test_website_url_valid - PASSED
> > test_crawl_depth_valid - PASSED
> > ... (実装がないため多くが失敗)
> ```
>
> ## 4. AIへの実装依頼
>
> ```bash
> > # 契約をAIに渡して実装を生成
> > cat << 'EOF' | pbcopy
> > Based on the following contracts, implement the FetchService class:
> >
> > ## Contracts
> > [contracts/fetch-contract.yaml の内容]
> > [src/site2/core/ports/fetch_contracts.py の内容]
> >
> > ## Requirements
> > 1. Follow Clean Architecture principles
> > 2. Use dependency injection
> > 3. Implement comprehensive error handling
> > 4. Add appropriate logging
> >
> > ## Implementation location
> > src/site2/core/use_cases/fetch_service.py
> >
> > Please provide a complete implementation.
> > EOF
> >
> > # クリップボードの内容をAIに渡す（手動またはCLIツール経由）
> ```
>
> ## 5. 生成されたコードの配置
>
> AIが生成したコードを適切な場所に配置：
>
> > ```bash
> > # ユースケースの実装
> > vim src/site2/core/use_cases/fetch_service.py
> >
> > # クローラーアダプターの実装
> > vim src/site2/adapters/crawlers/wget_crawler.py
> >
> > # リポジトリアダプターの実装
> > vim src/site2/adapters/storage/file_repository.py
> > ```
>
> ## 6. テストの再実行
>
> > ```bash
> > # 単体テストの実行
> > make test-unit
> >
> > # 出力例（実装後）：
> > ====== 45 passed in 2.34s ======
> > ```
>
> ## 7. 契約準拠の確認
>
> > ```bash
> > # 契約チェック
> > make contract-check
> >
> > # 出力例：
> > ✅ FetchService implements FetchServiceProtocol correctly
> > ✅ All methods match contract signatures
> > ✅ Error handling follows contract specifications
> > ```
>
> ## 8. 統合テストの作成と実行
>
> > ```bash
> > # 統合テストの作成
> > vim tests/integration/test_fetch_integration.py
> >
> > # 統合テストの実行
> > make test-integration
> > ```
>
> ## 9. BDDシナリオの実行
>
> > ```bash
> > # BDDテストの実行
> > make test-bdd
> >
> > # 出力例：
> > Feature: Webサイトのフェッチとキャッシュ
> >   Scenario: 新規サイトのフェッチ
> >     Given "https://example.com" はまだキャッシュされていない ... PASSED
> >     When コマンド "site2 fetch https://example.com" を実行する ... PASSED
> >     Then 終了コード 0 で正常終了する ... PASSED
> > ```
>
> ## 10. コードレビューとフィードバック
>
> > ```bash
> > # AIによるコードレビュー
> > git diff --cached | make ai-review
> >
> > # 出力例：
> > === AI Code Review ===
> > ✅ Contract Compliance: All methods match the defined contracts
> > ✅ Clean Architecture: Proper separation of concerns
> > ⚠️  Error Handling: Consider adding retry logic for network errors
> > ✅ Test Coverage: 92% coverage achieved
> > ```
>
> ## 11. 修正とリファクタリング
>
> フィードバックに基づいて修正：
>
> > ```python
> > # src/site2/core/use_cases/fetch_service.py
> > class FetchService:
> >     def __init__(self,
> >                  repository: WebsiteCacheRepositoryProtocol,
> >                  crawler: WebCrawlerProtocol,
> >                  retry_count: int = 3):
> >         self.repository = repository
> >         self.crawler = crawler
> >         self.retry_count = retry_count
> >
> >     def fetch(self, request: FetchRequest) -> FetchResult:
> >         # リトライロジックを追加
> >         for attempt in range(self.retry_count):
> >             try:
> >                 return self._do_fetch(request)
> >             except NetworkError as e:
> >                 if attempt == self.retry_count - 1:
> >                     raise
> >                 logger.warning(f"Attempt {attempt + 1} failed: {e}")
> > ```
>
> ## 12. 最終確認とコミット
>
> > ```bash
> > # すべてのチェックを実行
> > make validate-all
> >
> > # 出力例：
> > ✅ Contract validation: PASSED
> > ✅ Linting: PASSED
> > ✅ Unit tests: PASSED (45/45)
> > ✅ Integration tests: PASSED (12/12)
> > ✅ Coverage: 94%
> >
> > # コミット
> > git add .
> > git commit -m "feat: implement fetch functionality with Clean Architecture
> >
> > - Add FetchService use case
> > - Implement WgetCrawler adapter
> > - Add FileRepository for cache storage
> > - Include comprehensive error handling and retry logic
> > - Test coverage: 94%"
> > ```
>
> ## 開発のポイント
>
> ### 成功のカギ
> 1. **契約を先に定義**: 実装前に入出力を明確化
> 2. **テストを先に書く**: 期待する振る舞いを定義
> 3. **段階的な実装**: MVP → 機能追加 → 最適化
> 4. **継続的な検証**: 各ステップで契約準拠を確認
>
> ### よくある落とし穴
> 1. **契約を無視した実装**: 必ず契約に従う
> 2. **外部依存の直接利用**: 必ず抽象化する
> 3. **テストの後回し**: TDDを徹底する
> 4. **一度に全部実装**: 段階的に進める
>
> ## 次のステップ
>
> Fetch機能が完成したら、同様のフローで次の機能を実装：
>
> 1. Parser機能（HTMLからコンテンツ抽出）
> 2. Sorter機能（ドキュメントの順序決定）
> 3. Converter機能（Markdown/PDF変換）
> 4. Builder機能（最終出力の生成）
> ```

## まとめ

`fetch`機能の開発を通じて、以下の開発プラクティスを実践する準備が整いました：

1. **DDD（ドメイン駆動開発）**
   - ドメインモデルの定義（WebsiteURL、CachedPage、WebsiteCache）
   - 集約とエンティティの明確化
   - ドメインイベントの定義

2. **Contract-First Development**
   - 契約の事前定義（fetch_contracts.py）
   - 入出力の明確化
   - エラーケースの定義

3. **TDD（テスト駆動開発）**
   - テストを先に作成（test_fetch.py）
   - Red-Green-Refactorサイクル
   - 契約ベースのテスト

4. **BDD（振る舞い駆動開発）**
   - ユーザー視点のシナリオ定義（fetch_scenarios.feature）
   - 実際の使用例に基づくテスト

5. **Clean Architecture**
   - レイヤー分離（Core/Adapters）
   - 依存性逆転の原則
   - ポートとアダプターパターン

6. **AI協調開発**
   - 明確な契約に基づくAIへの実装依頼
   - 段階的な実装アプローチ
   - 自動検証による品質保証

これらのプラクティスを実際に手を動かして体験することで、理解が深まります。まずは`make dev-fetch`を実行して、開発フローを体験してみてください。
