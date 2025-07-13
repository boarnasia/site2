# Task 21: パイプライン統合テストの修正とインターフェース設計の改善

## 背景
Task 20（パイプライン統合テスト）で以下の重要な問題が発見された：
1. `detect_order`メソッドがNavigationデータを必要とする
2. `build_markdown`メソッドがDocumentOrderデータを必要とする
3. Protocol命名規則の不統一
4. データフロー設計の不整合

## 目的
- パイプラインのデータフローを正しく設計し直す
- インターフェース（Protocol）を適切に定義する
- 統合テストを完全に動作させる
- Task 3（詳細設計）への明確な引き継ぎ

## 実装内容

### 1. Protocol定義の修正
各サービスのインターフェースを以下のように修正：

```python
class IDetectService(Protocol):
    async def detect_main_content(self, html: str) -> MainContent:
        ...

    async def detect_navigation(self, html: str) -> Navigation:
        ...

    async def detect_order(
        self,
        cache_dir: Path,
        navigation: Navigation  # 追加
    ) -> DocumentOrder:
        ...

class IBuildService(Protocol):
    async def build_markdown(
        self,
        contents: List[MainContent],
        doc_order: DocumentOrder  # 追加
    ) -> MarkdownDocument:
        ...
```

### 2. データフロー設計の明確化
正しいパイプラインフロー：
```
1. Fetch → FetchResult（HTMLファイル群）
2. Detect:
   - detect_main_content(html) → MainContent（各ファイル）
   - detect_navigation(html) → Navigation（トップページ）
   - detect_order(cache_dir, navigation) → DocumentOrder
3. Build:
   - build_markdown(contents, doc_order) → MarkdownDocument
```

### 3. モックサービスの修正
- `MockDetectService.detect_order`：Navigationを受け取るように修正
- `MockBuildService.build_markdown`：DocumentOrderを受け取るように修正

### 4. 統合テストの修正
正しいデータフローに従ってテストを修正：
- navigationをdetect_orderに渡す
- doc_orderをbuild_markdownに渡す

### 5. レポートの整理
- `ai-agents/reports/task20.md`の問題点を反映
- `ai-agents/reports/task21.md`に修正内容を記録

## 成功基準
- [ ] Protocol定義が正しいデータフローを表現している
- [ ] モックサービスが新しいインターフェースに準拠
- [ ] 統合テストが完全に動作する
- [ ] データの受け渡しが明確で追跡可能
- [ ] Task 3への引き継ぎドキュメントが完成

## 注意事項
- Protocol命名は`I`プレフィックスで統一
- データフローは実際の使用シナリオに基づく
- 各サービスの責務を明確に分離
- エラーハンドリングパターンも統一

## 期待される成果物
1. 修正されたProtocol定義
2. 更新されたモックサービス
3. 正しく動作する統合テスト
4. データフロー設計ドキュメント
5. Task 3への引き継ぎレポート
