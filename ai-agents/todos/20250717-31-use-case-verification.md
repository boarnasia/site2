# Task 31: Use Case層のAdapter依存検証

## 概要
Use Case層（FetchService, DetectService等）がAdapter実装を直接参照していないか検証し、必要に応じて修正する。

## 背景
クリーンアーキテクチャでは、Use Case層はPorts（Protocol）のみに依存し、Adapter実装を直接参照してはいけない。現在の実装がこの原則に従っているか検証が必要。

## 検証対象
1. **FetchService** (`src/site2/core/use_cases/fetch_service.py`)
   - WebCrawlerProtocolのみを使用しているか
   - WebsiteCacheRepositoryProtocolのみを使用しているか

2. **DetectService** (`src/site2/core/use_cases/detect_service.py`)
   - HTMLParserProtocolのみを使用しているか
   - HTMLAnalyzerProtocolのみを使用しているか
   - MainContentDetectorProtocolのみを使用しているか

3. **BuildService** (`src/site2/core/use_cases/build_service.py`)
   - 実装時に同様の検証が必要

## 検証ポイント

### 1. インポート文の確認
```python
# 良い例
from ..ports.fetch_contracts import WebCrawlerProtocol

# 悪い例
from ...adapters.crawlers.wget_crawler import WgetCrawler
```

### 2. 型アノテーションの確認
```python
# 良い例
def __init__(self, crawler: WebCrawlerProtocol):

# 悪い例
def __init__(self, crawler: WgetCrawler):
```

### 3. 実装詳細への依存確認
- Adapter固有のメソッドを呼び出していないか
- Adapter固有の例外をキャッチしていないか
- Adapter固有の設定を参照していないか

## 修正が必要な場合の対応

### パターン1: 直接インポートの修正
```python
# Before
from ...adapters.crawlers.wget_crawler import WgetCrawler

# After
from ..ports.fetch_contracts import WebCrawlerProtocol
```

### パターン2: 型アノテーションの修正
```python
# Before
def __init__(self, crawler: WgetCrawler):

# After
def __init__(self, crawler: WebCrawlerProtocol):
```

### パターン3: 実装詳細の抽象化
Adapter固有の機能が必要な場合は、Protocolに追加するか、別のProtocolを定義する。

## 期待される効果
- **疎結合**: Use Case層とAdapter層の結合度が低下
- **テスタビリティ**: モック実装への差し替えが容易
- **保守性**: Adapter実装の変更がUse Case層に影響しない
- **拡張性**: 新しいAdapter実装の追加が容易

## 実装手順
1. 各Use Caseファイルのインポート文を確認
2. コンストラクタと型アノテーションを確認
3. メソッド内でAdapter固有の機能を使用していないか確認
4. 問題があれば修正
5. 型チェッカー（mypy）で検証
6. テスト実行で動作確認

## 検証コマンド
```bash
# インポートの検索
grep -r "from.*adapters" src/site2/core/use_cases/

# 型チェック
mypy src/site2/core/use_cases/

# テスト実行
pytest tests/unit/use_cases/
```

## 関連ファイル
- src/site2/core/use_cases/fetch_service.py
- src/site2/core/use_cases/detect_service.py
- src/site2/core/use_cases/build_service.py (実装時)

## 完了条件
- [ ] Use Case層にAdapter実装の直接インポートがない
- [ ] すべての依存関係がProtocol経由である
- [ ] Adapter固有の実装詳細に依存していない
- [ ] mypyでの型チェックがエラーなく通過する
- [ ] 既存のテストがすべて通過する
