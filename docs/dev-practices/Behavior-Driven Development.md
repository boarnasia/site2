[TOC](/docs/TOC.md)

## Behavior-Driven Development (BDD) ガイド

このドキュメントは、私たちのチームが採用する開発プラクティスの一つである \*\*BDD（ビヘイビア駆動開発）**の目的と、具体的なツールとして**Behave (Python)\*\* の使い方をまとめたものです。

### 1\. BDDとは何か？ (What is BDD?)

**BDD (Behavior-Driven Development / ビヘイビア駆動開発)** は、開発者、QA、ビジネス担当者など、プロジェクトに関わる全ての人が**共通の言葉でソフトウェアの「振る舞い（Behavior）」を定義し、それを中心に開発を進める**ためのアジャイル開発プラクティスです。

#### 🎯 目的

  * **認識のズレを防ぐ**: 「ユーザーが〜した場合、〜となるべき」という具体的な振る舞いのシナリオを共有することで、仕様の曖昧さをなくし、手戻りを減らします。
  * **生きたドキュメント**: BDDのシナリオは、そのまま仕様書として機能します。そして、このシナリオは自動テストによって常に動作が保証されるため、「ドキュメントだけが古くなる」という問題を防ぎます。
  * **コラボレーションの促進**: 全員が同じ言葉（シナリオ）で会話することで、チーム全体のコミュニケーションが円滑になります。

#### 📜 Gherkin: 共通言語

BDDでは、**Gherkin（ガーキン）** という記法を使って、誰でも理解できる自然言語で振る舞いを記述します。

  * `Feature`: 機能のタイトル
  * `Scenario`: 具体的な振る舞いのシナリオ
  * `Given`: 前提条件、初期状態 (〜という状況で)
  * `When`: ユーザーのアクションやイベント (〜した時)
  * `Then`: 期待される結果 (〜となるべき)

-----

### 2\. BehaveによるBDDの実践 (How to use Behave)

**Behave**は、PythonでBDDを実践するためのフレームワークです。Gherkinで書かれたシナリオと、それを実行するPythonコードを紐付けて、自動テストを実現します。

#### 📂 ディレクトリ構造

Behaveは規約に基づいたディレクトリ構造を要求します。

```
project/
└── features/
    ├── example.feature      # 👈 Gherkinでシナリオを書くファイル
    └── steps/
        └── example_steps.py # 👈 シナリオを実装するPythonコード
```

#### ✍️ Step 1: シナリオを記述する (`.feature`ファイル)

まず、システムの振る舞いを`features/example.feature`に記述します。

```gherkin
# features/example.feature
Feature: ユーザー認証機能

  Scenario: 正常な認証情報によるログイン成功
    Given 登録済みのユーザー "test_user" が存在する
    When "test_user" がパスワード "correct_password" でログインを試みる
    Then ログイン結果は "成功" となるべき

  Scenario: 不正なパスワードによるログイン失敗
    Given 登録済みのユーザー "test_user" が存在する
    When "test_user" がパスワード "wrong_password" でログインを試みる
    Then ログイン結果は "失敗" となるべき
```

#### 🚀 Step 2: ステップ定義の雛形を生成する (`--dry-run`)

次に、ターミナルで以下のコマンドを実行します。

```bash
behave --dry-run
```

`--dry-run`オプションは、テストを**実行せずに**、未実装のステップに対応するPythonコードの**雛形（テンプレート）を生成**してくれます。これにより、手作業によるコピー＆ペーストやタイプミスを防ぎ、二度手間をなくします。

**出力結果:**

```
You can implement step definitions for undefined steps with these snippets:

@given(u'登録済みのユーザー "{user}" が存在する')
def step_impl(context, user):
    raise NotImplementedError(u'STEP: Given 登録済みのユーザー "test_user" が存在する')

@when(u'"{user}" がパスワード "{password}" でログインを試みる')
def step_impl(context, user, password):
    raise NotImplementedError(u'STEP: When "test_user" がパスワード "correct_password" でログインを試みる')

@then(u'ログイン結果は "{result}" となるべき')
def step_impl(context, result):
    raise NotImplementedError(u'STEP: Then ログイン結果は "成功" となるべき')
```

#### 🐍 Step 3: ステップを実装する (`_steps.py`ファイル)

`--dry-run`で生成された雛形を`features/steps/example_steps.py`に貼り付け、`raise NotImplementedError`の部分を実際のロジックに書き換えます。

```python
# features/steps/example_steps.py
from behave import given, when, then
# from my_app.authenticator import Authenticator # 実際の認証ロジックをインポート

@given('登録済みのユーザー "{user}" が存在する')
def step_given_user_exists(context, user):
    # テストの前提条件を準備する
    # context.authenticator = Authenticator()
    # print(f"前提: {user} が存在する")
    pass

@when('"{user}" がパスワード "{password}" でログインを試みる')
def step_when_login_attempt(context, user, password):
    # 実際のアプリケーションロジックを呼び出す
    # context.result = context.authenticator.login(user, password)
    # 以下はダミーの実装
    if password == "correct_password":
        context.result = "成功"
    else:
        context.result = "失敗"

@then('ログイン結果は "{expected_result}" となるべき')
def step_then_verify_result(context, expected_result):
    # 結果を検証する
    assert context.result == expected_result
```

  * **`context`オブジェクト**: ステップ間でデータ（例: ログイン結果）を受け渡すための一時的な入れ物です。
  * **関数名**: `step_impl`のままでも動作しますが、可読性のために具体的な名前（例: `step_given_user_exists`）を付けることを推奨します。

#### ✅ Step 4: テストを実行する

最後に、以下のコマンドでテストを実行します。

```bash
behave
```

Behaveが`.feature`ファイルと`steps`ディレクトリのコードを紐付け、シナリオ通りにシステムが振る舞うかを自動で検証します。

-----

### まとめ

BDDとBehaveを導入することで、私たちは以下の価値を得ます。

1.  **仕様の明確化**: 自然言語のシナリオで、作るべき機能の振る舞いを正確に定義します。
2.  **品質の向上**: シナリオは自動テストとして機能し、リファクタリングや機能追加時のデグレードを防ぎます。
3.  **開発効率の向上**: `--dry-run`のようなツールを活用し、仕様からテストコードへの変換を効率化します。

このプラクティスをチームで実践し、コミュニケーションが円滑で、品質の高いソフトウェアを効率的に開発していきましょう。
