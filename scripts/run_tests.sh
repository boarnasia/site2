#!/bin/bash
# テスト実行スクリプト

set -e

echo "🧪 Running site2 tests..."

# チュートリアルテストの実行
echo "📚 Running tutorial tests..."
rye run pytest tests/features/test_tutorial.py -v

# BDDテストの実行
echo "🥒 Running BDD tests..."
rye run pytest tests/features -v -m "not tutorial"

# 単体テストの実行
echo "🔬 Running unit tests..."
rye run pytest tests/unit -v

# カバレッジレポート
echo "📊 Generating coverage report..."
rye run pytest --cov=src/site2 --cov-report=term-missing --cov-report=html

echo "✅ All tests completed!"
echo "📁 Coverage report available at: htmlcov/index.html"
