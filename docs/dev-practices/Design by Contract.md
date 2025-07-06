[TOC](/docs/TOC.md)

## 契約による設計 (Design by Contract / DbC) ガイド

このドキュメントは、ソフトウェアコンポーネントの品質と信頼性を高める設計アプローチである\*\*契約による設計（DbC）\*\*について、その目的、主要概念、そしてPythonによる具体的な実装例をまとめたものです。

### 1\. 契約による設計とは何か？

\*\*契約による設計（DbC）\*\*は、ソフトウェアの各要素（クラスや関数）が、お互いに「契約」を結んで動作するという考え方に基づいたソフトウェア設計手法です。

関数を呼び出す側（クライアント）と、呼び出される側（サプライヤー）の間で、それぞれの\*\*「責任と権利」\*\*を明確に定義します。この契約が守られることで、ソフトウェア全体の正しさが保証され、バグの早期発見やデバッグの容易化に繋がります。

-----

### 2\. 契約の3つの要素とPython実装例

契約は、主に「事前条件」「事後条件」「不変条件」の3つの要素で構成されます。ここでは、簡単な銀行口座(`BankAccount`)クラスを例に、デコレータを使った実装を見ていきましょう。

#### ① 事前条件 (Preconditions)

  * **内容**: メソッドが呼び出される**前に**満たされていなければならない条件。
  * **責任**: \*\*クライアント（呼び出し側）\*\*の責任です。
  * **例**: 出金額は正の数でなければならない。

##### Python実装例

`@requires`デコレータを作成し、関数の実行前に条件をチェックします。

```python
# --- デコレータの定義 ---
def requires(precondition):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # 事前条件をチェック
            if not precondition(self, *args, **kwargs):
                raise ValueError(f"事前条件違反: {func.__name__} - {precondition.__doc__}")
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

# --- クラスでの使用例 ---
class BankAccount:
    def __init__(self, balance=0):
        self.balance = balance

    @requires(lambda self, amount: amount > 0)
    def withdraw(self, amount: int):
        """出金額は0より大きくなければならない"""
        self.balance -= amount
```

この場合、`account.withdraw(-50)`のように事前条件に違反する呼び出しをすると、即座に`ValueError`が発生します。

-----

#### ② 事後条件 (Postconditions)

  * **内容**: メソッドの処理が完了した**後に**保証されなければならない条件。
  * **責任**: \*\*サプライヤー（メソッドの実装側）\*\*の責任です。
  * **例**: 出金後、口座残高が正しく減っている。

##### Python実装例

`@ensures`デコレータで、メソッド実行後の状態を検証します。実行前の値も利用できるように工夫します。

```python
# --- デコレータの定義 ---
def ensures(postcondition):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # 実行前の状態を保存
            old_balance = self.balance

            # 関数を実行
            result = func(self, *args, **kwargs)

            # 事後条件をチェック
            if not postcondition(self, result, old_balance):
                 raise RuntimeError(f"事後条件違反: {func.__name__} - {postcondition.__doc__}")
            return result
        return wrapper
    return decorator

# --- クラスでの使用例 ---
class BankAccount:
    def __init__(self, balance=0):
        self.balance = balance

    @ensures(lambda self, result, old_balance: self.balance == old_balance - result)
    def withdraw(self, amount: int) -> int:
        """残高が正しく更新されること"""
        # (仮にバグを混入させてみる)
        # self.balance -= amount - 10
        self.balance -= amount
        return amount # 実際に出金した額を返す
```

もし`withdraw`メソッドの実装にバグがあり、事後条件が満たされない場合、`RuntimeError`が発生して問題を即座に検知できます。

-----

#### ③ 不変条件 (Invariants)

  * **内容**: メソッドの実行前後で**常に**真でなければならない条件。クラスの状態の一貫性を保ちます。
  * **責任**: \*\*サプライヤー（クラスの実装側）\*\*の責任です。
  * **例**: 口座残高がマイナスになってはいけない。

##### Python実装例

クラスデコレータ`@invariant`で、状態を変更する可能性のある全ての公開メソッドの実行後に条件をチェックします。

```python
# --- デコレータの定義 ---
def invariant(condition):
    def class_decorator(cls):
        # クラスの公開メソッドをラップする
        for name, method in cls.__dict__.items():
            if callable(method) and not name.startswith('_'):
                setattr(cls, name, _check_invariant(method, condition))
        return cls

    def _check_invariant(method, condition):
        def wrapper(self, *args, **kwargs):
            result = method(self, *args, **kwargs)
            # 不変条件をチェック
            if not condition(self):
                raise RuntimeError(f"不変条件違反: {method.__name__}後 - {condition.__doc__}")
            return result
        return wrapper
    return class_decorator


# --- クラスでの使用例 ---
@invariant(lambda self: self.balance >= 0)
class BankAccount:
    """口座残高は常に0以上でなければならない"""
    def __init__(self, balance=0):
        self.balance = balance
        if not (self.balance >= 0): # コンストラクタでも不変条件を保証
             raise ValueError("初期残高がマイナスです")

    def withdraw(self, amount: int):
        if self.balance >= amount: # 事前チェック
            self.balance -= amount
```

この`BankAccount`クラスのインスタンスで、残高を超える出金処理などにより不変条件が破られると、`RuntimeError`が発生します。

-----

### 4\. 実践上の考慮点：本番環境でのパフォーマンス

これらの契約チェックは、開発時やテスト時には非常に有用ですが、本番環境ではパフォーマンスのオーバーヘッドになります。そのため、Pythonの最適化モード(`-O`オプション)ではチェックを無効化するのが一般的です。

デコレータを以下のように修正することで、これを実現できます。

```python
def requires(precondition):
    def decorator(func):
        # 最適化モードでは、チェックを行わず元の関数をそのまま返す
        if not __debug__:
            return func

        # (以降の実装は同じ...)
```

`__debug__`は、Pythonが`python -O my_app.py`のように最適化モードで実行された場合に`False`になる組み込み定数です。

### まとめ

契約による設計は、コンポーネント間の責任を明確にし、コードの信頼性を高めるための強力なアプローチです。Pythonのデコレータを使えば、この概念をコードに直接、かつエレガントに組み込むことができます。開発時には厳密な契約で品質を担保し、本番時にはそれを無効化してパフォーマンスを確保する、という使い分けが効果的です。
