import pytest
from pytest_bdd import scenario, given, when, then, parsers


# シナリオのバインディング
@scenario("tutorial.feature", "behave基本機能")
def test_behave_basic():
    pass


@scenario("tutorial.feature", "加算機能のテスト")
def test_addition():
    pass


# ---------------------
# ステップ定義（状態共有用）


@pytest.fixture
def context():
    return {}


@given("behaveは使用可能")
def behave_is_ready():
    pass


@when("behaveを実行する")
def run_behave():
    pass  # ダミー処理


@then("テストは成功するはず")
def check_success():
    assert True


@given(parsers.parse("数値 {x:d} と {y:d} を入力する"))
def input_numbers(context, x, y):
    context["x"] = x
    context["y"] = y


@when("加算を実行します")
def perform_addition(context):
    context["result"] = context["x"] + context["y"]


@then(parsers.parse("結果は{expected:d}であるべき"))
def check_result(context, expected):
    assert context["result"] == expected
