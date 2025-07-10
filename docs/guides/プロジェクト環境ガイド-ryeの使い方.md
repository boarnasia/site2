# プロジェクト環境ガイド

このドキュメントは、本プロジェクトの開発環境と作業手順について説明します。

## パッケージ管理システム

本プロジェクトでは **Rye** をパッケージ管理システムとして使用しています。
- Ryeは、Pythonのバージョン管理と依存関係管理を統合的に行うツールです
- `pyproject.toml` ファイルで依存関係を管理しています
- 仮想環境は `.venv` ディレクトリに自動的に作成されます

## 重要：Pythonコマンドの実行方法

### ❌ 間違った実行方法
```bash
python script.py
python -m module_name
pip install package_name
```

### ✅ 正しい実行方法
```bash
rye run python script.py
rye run python -m module_name
rye add package_name  # パッケージのインストール
rye sync  # 依存関係の同期
```

## 基本的なRyeコマンド

### パッケージ管理
```bash
# パッケージを追加
rye add package_name

# 開発用パッケージを追加
rye add --dev package_name

# パッケージを削除
rye remove package_name

# 依存関係を同期（requirements.lockファイルに基づいて環境を再現）
rye sync

# 依存関係を更新
rye lock --update-all
```

### Python実行
```bash
# Pythonスクリプトを実行
rye run python script.py

# Pythonインタラクティブシェルを起動
rye run python

# モジュールとして実行
rye run python -m module_name

# pytestを実行
rye run pytest

# その他のCLIツールを実行
rye run pre-commit --all-files
```

### プロジェクト管理
```bash
# Pythonバージョンを確認
rye show

# 使用可能なPythonバージョンを表示
rye toolchain list

# 特定のPythonバージョンに切り替え
rye pin python@3.11
```

## プロジェクト構造

```
project-root/
├── pyproject.toml      # プロジェクト設定と依存関係
├── requirements.lock   # ロックファイル（自動生成）
├── requirements-dev.lock # 開発用ロックファイル（自動生成）
├── .venv/             # 仮想環境（自動生成）
├── src/               # ソースコード
│   └── your_package/
├── tests/             # テストコード
└── scripts/           # ユーティリティスクリプト
```

## 作業を始める前に

1. **依存関係の同期を確認**
   ```bash
   rye sync
   ```

2. **Pythonバージョンの確認**
   ```bash
   rye show
   ```

## よくある作業パターン

### 新しいスクリプトを作成して実行
```bash
# スクリプトを作成
echo 'print("Hello, Rye!")' > test_script.py

# 実行
rye run python test_script.py
```

### テストの実行
```bash
# すべてのテストを実行
rye run pytest

# 特定のテストファイルを実行
rye run pytest tests/test_specific.py

# カバレッジ付きで実行
rye run pytest --cov=src
```

### コードフォーマット
```bash
# blackでフォーマット
rye run black src/ tests/

# isortでインポートを整理
rye run isort src/ tests/

# flake8でリント
rye run flake8 src/ tests/
```

## 環境変数

必要に応じて `.env` ファイルを使用して環境変数を設定できます：

```bash
# .env ファイルの例
DATABASE_URL=postgresql://localhost/mydb
API_KEY=your-secret-key
```

Ryeでの実行時に自動的に読み込まれます：
```bash
rye run python -c "import os; print(os.getenv('DATABASE_URL'))"
```

## トラブルシューティング

### 問題：`ModuleNotFoundError`
**解決策**: `rye sync` を実行して依存関係を同期

### 問題：コマンドが見つからない
**解決策**: `rye run` を使用してコマンドを実行

### 問題：パッケージのバージョン競合
**解決策**:
```bash
rye lock --update-all
rye sync
```

## 重要な注意事項

1. **常に `rye run` を使用**: Pythonやインストールされたパッケージのコマンドを実行する際は、必ず `rye run` プレフィックスを付けてください

2. **直接pipを使用しない**: パッケージのインストールには `rye add` を使用し、`pip install` は使用しないでください

3. **仮想環境の手動アクティベーションは不要**: Ryeが自動的に適切な環境でコマンドを実行します

4. **グローバルPythonとの混同を避ける**: システムにインストールされたPythonと混同しないよう、常にRye経由で実行してください

このガイドに従うことで、一貫した開発環境で作業できます。
