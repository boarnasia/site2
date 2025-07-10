# Todo 06: Detect:Navサービスの実装

## 目的

HTMLファイルからナビゲーション要素を検出し、サイト構造を把握する。

## 背景

ナビゲーションには、サイトの論理的な構造が表現されている。この情報を抽出して、ドキュメントの順序決定に使用する。

## 成果物

1. **DetectNavService実装**
   - ナビゲーション要素の検出
   - リンク構造の解析

## 実装詳細

### ナビゲーション検出アルゴリズム

```python
class NavigationDetector:
    """ナビゲーション検出器"""

    # ナビゲーションの候補セレクタ
    NAV_SELECTORS = [
        "nav",
        "[role='navigation']",
        ".navigation",
        "#navigation",
        ".nav",
        "#nav",
        ".sidebar nav",
        ".menu",
        ".toc",  # Table of Contents
        "#toc",
    ]

    def detect(self, soup: BeautifulSoup) -> List[NavCandidate]:
        """
        ナビゲーション候補を検出

        1. 既知のセレクタをチェック
        2. リンクの密度を計算
        3. 構造的特徴を評価
        4. スコアリング
        """
        candidates = []

        for selector in self.NAV_SELECTORS:
            elements = soup.select(selector)
            for element in elements:
                candidate = self._evaluate_nav_candidate(element)
                if candidate.score > 0.5:  # 閾値
                    candidates.append(candidate)

        # ヒューリスティック検出
        candidates.extend(self._heuristic_detection(soup))

        return sorted(candidates, key=lambda x: x.score, reverse=True)
```

### ナビゲーション評価基準

```python
def _evaluate_nav_candidate(self, element: Tag) -> NavCandidate:
    """ナビゲーション候補を評価"""
    score = 0.0

    # 1. セマンティックな要素
    if element.name == 'nav':
        score += 1.0
    elif element.get('role') == 'navigation':
        score += 0.9

    # 2. リンクの特徴
    links = element.find_all('a')
    link_count = len(links)

    if link_count > 3:  # 最小リンク数
        score += 0.5

    # リンク密度（リンク数 / 全要素数）
    all_elements = len(element.find_all())
    link_density = link_count / all_elements if all_elements > 0 else 0

    if link_density > 0.5:
        score += 0.3

    # 3. リスト構造
    if element.find(['ul', 'ol']):
        score += 0.2

    # 4. 位置（ページ上部や左側にある可能性が高い）
    # CSSクラス名のヒント
    class_names = ' '.join(element.get('class', []))
    if any(hint in class_names for hint in ['header', 'top', 'sidebar']):
        score += 0.1

    return NavCandidate(
        element=element,
        selector=self._generate_selector(element),
        score=min(score, 1.0),
        link_count=link_count,
        links=self._extract_nav_links(element)
    )
```

### リンク構造の解析

```python
def _extract_nav_links(self, nav_element: Tag) -> List[NavLink]:
    """ナビゲーションからリンクを抽出"""
    links = []

    def extract_recursive(element: Tag, level: int = 0):
        # 直接の<a>タグ
        for a in element.find_all('a', recursive=False):
            link = NavLink(
                text=a.get_text(strip=True),
                href=a.get('href', ''),
                level=level
            )
            links.append(link)

        # ネストされたリスト
        for list_elem in element.find_all(['ul', 'ol'], recursive=False):
            for li in list_elem.find_all('li', recursive=False):
                # <li>内の<a>
                a = li.find('a', recursive=False)
                if a:
                    link = NavLink(
                        text=a.get_text(strip=True),
                        href=a.get('href', ''),
                        level=level + 1
                    )
                    links.append(link)

                # さらにネストされたリスト
                extract_recursive(li, level + 1)

    extract_recursive(nav_element)
    return links
```

### DetectNavService実装

```python
class DetectNavService:
    def __init__(self, parser: HTMLParserProtocol):
        self.parser = parser
        self.detector = NavigationDetector()

    def detect_nav(self, request: DetectNavRequest) -> DetectNavResult:
        # HTMLを解析
        soup = self.parser.parse(request.file_path)

        # ナビゲーション候補を検出
        candidates = self.detector.detect(soup)

        if not candidates:
            return DetectNavResult(
                file_path=request.file_path,
                selectors=[],
                confidence=0.0,
                primary_selector="",
                nav_links=[]
            )

        # 最良の候補
        best = candidates[0]

        return DetectNavResult(
            file_path=request.file_path,
            selectors=[c.selector for c in candidates[:3]],
            confidence=best.score,
            primary_selector=best.selector,
            nav_links=best.links
        )
```

## テスト要件

### テストケース

```python
def test_detect_semantic_nav():
    """<nav>要素の検出"""
    html = """
    <nav class="main-nav">
        <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/about">About</a></li>
            <li><a href="/contact">Contact</a></li>
        </ul>
    </nav>
    """
    result = service.detect_nav(request)
    assert result.primary_selector == "nav.main-nav"
    assert len(result.nav_links) == 3

def test_detect_nested_navigation():
    """ネストされたナビゲーション"""
    html = """
    <div class="navigation">
        <ul>
            <li><a href="/guide">Guide</a>
                <ul>
                    <li><a href="/guide/install">Install</a></li>
                    <li><a href="/guide/config">Config</a></li>
                </ul>
            </li>
        </ul>
    </div>
    """
    result = service.detect_nav(request)
    assert len(result.nav_links) == 3
    assert result.nav_links[0].level == 0
    assert result.nav_links[1].level == 1
```

## 実装のポイント

1. **複数のナビゲーション**
   - メインナビゲーション vs サイドバー
   - 優先順位の判定

2. **動的ナビゲーション**
   - JavaScriptで生成される場合の対処
   - フォールバック戦略

3. **相対URLの処理**
   - `href="/path"` → 絶対パスに変換
   - `href="#section"` → ページ内リンクの扱い

## 受け入れ基準

- [ ] 一般的なナビゲーションパターンを検出
- [ ] ネスト構造を正しく解析
- [ ] リンクのテキストとURLを抽出
- [ ] 信頼度スコアが適切

## 推定工数

3-4時間

## 依存関係

- [04. HTMLパーサーの実装](20250706-04-implement-html-parser.md)

## 次のタスク

→ [07. Detect:Orderサービスの実装](20250706-07-implement-detect-order.md)
