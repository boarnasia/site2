# Todo 05: Detect:Mainサービスの実装

## 目的

HTMLファイルからメインコンテンツ領域を検出するサービスを実装する。

## 背景

Webページには通常、ヘッダー、ナビゲーション、サイドバー、フッターなどの要素があるが、
ドキュメント変換においては、メインコンテンツのみを抽出する必要がある。

## 成果物

1. **DetectMainService実装**
   - `src/site2/core/use_cases/detect_use_case.py`
   - メインコンテンツ検出ロジック

2. **セレクタ検出アルゴリズム**
   - ヒューリスティックベースの検出
   - スコアリングシステム

## 実装詳細

### 検出アルゴリズム

```python
class MainContentDetector:
    """メインコンテンツ検出器"""

    # 優先度の高いセレクタ候補
    MAIN_SELECTORS = [
        "main",
        "article",
        "[role='main']",
        "#main",
        ".main",
        "#content",
        ".content",
        "#main-content",
        ".main-content",
    ]

    def detect(self, soup: BeautifulSoup) -> List[SelectorCandidate]:
        """
        検出アルゴリズム：
        1. 既知のセレクタをチェック
        2. テキスト密度を計算
        3. 位置とサイズを考慮
        4. スコアリングして順位付け
        """
```

### スコアリング基準

1. **セレクタの意味的重要度**
   - `<main>`: 100点
   - `<article>`: 90点
   - `role="main"`: 95点
   - IDセレクタ: 80点
   - クラスセレクタ: 70点

2. **コンテンツの特徴**
   - テキスト密度（テキスト/HTML比）
   - 段落（`<p>`）の数
   - 見出し（`<h1>-<h6>`）の存在
   - リンク密度（低い方が良い）

3. **位置とサイズ**
   - ビューポート内での位置
   - 要素の幅（広い方が良い）
   - 要素の高さ

### 実装例

```python
@dataclass
class SelectorCandidate:
    selector: str
    score: float
    element: Tag
    text_length: int
    text_density: float

class DetectMainService:
    def __init__(self, parser: HTMLParserProtocol):
        self.parser = parser
        self.detector = MainContentDetector()

    def detect_main(self, request: DetectMainRequest) -> DetectMainResult:
        # HTMLを解析
        soup = self.parser.parse(request.file_path)

        # 候補を検出
        candidates = self.detector.detect(soup)

        # スコア順にソート
        candidates.sort(key=lambda x: x.score, reverse=True)

        # 結果を構築
        return DetectMainResult(
            file_path=request.file_path,
            selectors=[c.selector for c in candidates[:3]],
            confidence=candidates[0].score / 100 if candidates else 0.0,
            primary_selector=candidates[0].selector if candidates else ""
        )
```

## テスト要件

### 単体テスト

- [ ] 典型的なブログ記事での検出
- [ ] ドキュメントサイトでの検出
- [ ] ニュースサイトでの検出
- [ ] セレクタが見つからない場合

### テストケース例

```python
def test_detect_main_blog_post():
    """ブログ記事でのメインコンテンツ検出"""
    html = """
    <body>
        <header>...</header>
        <nav>...</nav>
        <main>
            <article>
                <h1>Blog Title</h1>
                <p>Content...</p>
            </article>
        </main>
        <aside>...</aside>
    </body>
    """

    result = service.detect_main(DetectMainRequest(file_path))
    assert result.primary_selector == "main article"
    assert result.confidence > 0.9
```

## 実装のポイント

1. **複数候補の返却**
   - 最も可能性の高い3つを返す
   - ユーザーが選択できるように

2. **フォールバック戦略**
   - 既知のセレクタが見つからない場合
   - 最大のテキストブロックを選択

3. **除外すべき要素**
   - `<nav>`, `<header>`, `<footer>`
   - `<aside>`, `<sidebar>`
   - 広告やコメント欄

## 受け入れ基準

- [ ] 一般的なWebサイトで80%以上の精度
- [ ] 3つの候補セレクタを返す
- [ ] 信頼度スコアが適切
- [ ] 処理時間が1秒以内

## 推定工数

3-4時間

## 依存関係

- [04. HTMLパーサーの実装](20250706-04-implement-html-parser.md)

## 次のタスク

→ [06. Detect:Navサービスの実装](20250706-06-implement-detect-nav.md)
