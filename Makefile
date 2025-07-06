# site2 開発タスク自動化

.PHONY: help setup test lint format clean

help: ## ヘルプを表示
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## 開発環境をセットアップ
	rye sync
	rye run playwright install
	rye run pre-commit install

# --- 契約駆動開発 ---
contract-validate: ## 契約の妥当性を検証
#	python scripts/validate_contracts.py
	@echo "not implemented yet"

contract-generate-tests: ## 契約からテストを生成
#	python scripts/generate_tests.py fetch
	@echo "not implemented yet"

contract-check: ## 実装が契約に準拠しているか確認
#	python scripts/check_contract_compliance.py
	@echo "not implemented yet"

# --- テストデータ準備 ---
prepare-fixtures: ## テスト用のFixtureデータを準備
	./scripts/prepare_test_fixtures.sh

clean-fixtures: ## Fixtureデータをクリーン
	rm -rf tests/fixtures

# --- テスト駆動開発 ---
test-unit: ## 単体テストを実行
	rye run pytest tests/unit -v

test-integration: ## 統合テストを実行
	rye run pytest tests/integration -v

test-e2e: ## E2Eテストを実行
	rye run pytest tests/e2e -v

test-bdd: prepare-fixtures ## BDDテストを実行（Fixture準備込み）
	rye run pytest tests/features -v -m "not tutorial"

test-bdd-server: prepare-fixtures ## サーバーを使うBDDテストを実行
	rye run pytest tests/features/test_fetch_with_server.py -v -s

test-tutorial: ## チュートリアルBDDテストを実行
	rye run pytest tests/features/test_tutorial.py -v

test: test-unit test-integration test-bdd ## すべてのテストを実行

test-watch: ## ファイル変更を監視してテストを自動実行
	rye run ptw tests/unit -- -v

coverage: ## テストカバレッジを計測
	rye run pytest --cov=src/site2 --cov-report=html --cov-report=term

# --- AI開発支援 ---
ai-generate-impl: ## AIに実装を生成させる
	@echo "Generating implementation for fetch module..."
	@cat contracts/fetch-contract.yaml src/site2/core/ports/fetch_contracts.py | \
	  llm "Based on these contracts, implement the FetchService class following Clean Architecture principles"

ai-review: ## AIにコードレビューを依頼
	@echo "Requesting AI code review..."
	@git diff --cached | llm "Review this code for: 1) Contract compliance 2) Clean Architecture 3) Error handling 4) Test coverage"

# --- 開発フロー ---
dev-fetch: ## fetch機能の開発フロー
	@echo "=== Fetch機能の開発フロー ==="
	@echo "1. 契約の検証"
	@make contract-validate
	@echo "\n2. テストの生成と実行（失敗することを確認）"
	@make test-unit || true
	@echo "\n3. 実装の生成（AIまたは手動）"
	@echo "   make ai-generate-impl"
	@echo "\n4. テストの実行（成功することを確認）"
	@echo "   make test-unit"
	@echo "\n5. 契約準拠の確認"
	@echo "   make contract-check"

# --- コード品質 ---
pre-commit: ## pre-commitを実行してコード品質をチェック
	rye run pre-commit run --all-files

# --- ドキュメント ---
docs-contracts: ## 契約からドキュメントを生成
#	python scripts/generate_docs_from_contracts.py
	@echo "no implementation yet"

docs-serve: ## ドキュメントをローカルで表示
	mkdocs serve

# --- クリーンアップ ---
clean: ## 生成ファイルを削除
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .ruff_cache

# --- 便利なコマンド ---
repl: ## Python REPLを起動（プロジェクトをインポート済み）
	rye run ipython -i -c "from site2.core.domain.fetch_domain import *; from site2.core.ports.fetch_contracts import *"

validate-all: contract-validate pre-commit test ## すべての検証を実行
