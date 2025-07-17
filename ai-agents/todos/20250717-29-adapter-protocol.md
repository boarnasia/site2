# Task 29: Adapter実装のProtocol継承明示化

## 概要
すべてのAdapter実装クラスが対応するProtocolを明示的に継承するよう修正する。

## 背景
Task27でHeuristicMainContentDetectorがProtocolを明示的に継承していない問題が発覚した。同様の問題が他のAdapter実装にも存在する可能性が高い。

## 問題点
以下のAdapter実装がProtocolを明示的に継承していない可能性：
1. FileRepository → WebsiteCacheRepositoryProtocol
2. WgetCrawler → WebCrawlerProtocol
3. BeautifulSoupParser → HTMLParserProtocol
4. BeautifulSoupAnalyzer → HTMLAnalyzerProtocol
5. ChardetDetector → EncodingDetectorProtocol
6. LLMPreprocessor → HTMLPreprocessorProtocol

## 修正内容

### 1. storage/file_repository.py
```python
from ...core.ports.fetch_contracts import WebsiteCacheRepositoryProtocol

class FileRepository(WebsiteCacheRepositoryProtocol):
    """ファイルベースのWebsiteキャッシュリポジトリ実装"""
```

### 2. crawlers/wget_crawler.py
```python
from ...core.ports.fetch_contracts import WebCrawlerProtocol

class WgetCrawler(WebCrawlerProtocol):
    """wgetを使用したWebクローラー実装"""
```

### 3. parsers/beautifulsoup_parser.py
```python
from ...core.ports.parser_contracts import (
    HTMLParserProtocol,
    HTMLAnalyzerProtocol,
    HTMLPreprocessorProtocol
)

class BeautifulSoupParser(HTMLParserProtocol):
    """BeautifulSoupベースのHTMLパーサー実装"""

class BeautifulSoupAnalyzer(HTMLAnalyzerProtocol):
    """BeautifulSoupベースのHTML解析実装"""

class LLMPreprocessor(HTMLPreprocessorProtocol):
    """LLM用HTMLプリプロセッサー実装"""
```

### 4. parsers/chardet_detector.py
```python
from ...core.ports.parser_contracts import EncodingDetectorProtocol

class ChardetDetector(EncodingDetectorProtocol):
    """chardetベースのエンコーディング検出実装"""
```

## 期待される効果
- **型安全性の向上**: Protocolで定義されたメソッドシグネチャの強制
- **LSPの遵守**: Liskov Substitution Principleの保証
- **IDE支援の向上**: 型チェックとオートコンプリート
- **保守性の向上**: インターフェースの変更時に実装漏れを防止

## 実装手順
1. 各Adapterファイルを開く
2. 対応するProtocolをインポート
3. クラス定義でProtocolを継承
4. メソッドシグネチャがProtocolと一致することを確認
5. 型チェッカー（mypy）で検証
6. テスト実行で動作確認

## 検証方法
```bash
# 型チェック
mypy src/site2/adapters/

# 単体テスト
pytest tests/unit/adapters/
```

## 関連ファイル
- src/site2/adapters/storage/file_repository.py
- src/site2/adapters/crawlers/wget_crawler.py
- src/site2/adapters/parsers/beautifulsoup_parser.py
- src/site2/adapters/parsers/chardet_detector.py

## 完了条件
- [ ] すべてのAdapter実装が対応するProtocolを継承している
- [ ] メソッドシグネチャがProtocolと完全に一致している
- [ ] mypyでの型チェックがエラーなく通過する
- [ ] 既存のテストがすべて通過する
- [ ] DIコンテナでの依存注入が正常に動作する
