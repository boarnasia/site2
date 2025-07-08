# Todo 07: Detect:Orderサービスの実装

## 目的

ナビゲーション構造を解析して、ドキュメントの論理的な順序を検出する。

## 背景

Webサイトのナビゲーションには、ドキュメントの読み順が暗黙的に示されている。
この順序を検出して、適切な順番でドキュメントを結合する必要がある。

## 成果物

1. **DetectOrderService実装**
   - ナビゲーションからリンクを抽出
   - 階層構造の解析
   - 論理的順序の決定

## 実装詳細

### アルゴリズム

```python
class OrderDetector:
    """ドキュメント順序検出器"""

    def detect_from_navigation(
        self,
        nav_element: Tag,
        base_path: Path
    ) -> List[OrderedFile]:
        """
        ナビゲーションから順序を検出

        1. リンクを再帰的に抽出
        2. 階層レベルを判定
        3. 順序番号を割り当て
        """

    def build_hierarchy(self, links: List[NavLink]) -> OrderTree:
        """
        フラットなリンクリストから階層構造を構築

        - <ul>/<ol>のネストを解析
        - インデントレベルから推測
        - URL構造から推測
        """
```

### データ構造

```python
@dataclass
class NavLink:
    text: str
    href: str
    level: int  # 階層レベル
    parent: Optional['NavLink'] = None
    children: List['NavLink'] = field(default_factory=list)

@dataclass
class OrderedFile:
    order: int
    path: Path
    title: str
    level: int
    url: Optional[str]

class OrderTree:
    """順序付きファイルのツリー構造"""
    def __init__(self):
        self.root = NavLink("ROOT", "", -1)

    def flatten(self) -> List[OrderedFile]:
        """ツリーを深さ優先で平坦化"""
```

### 順序決定ロジック

1. **深さ優先探索**
   ```
   1. Introduction (level 0)
   2. Getting Started (level 0)
      3. Installation (level 1)
      4. Configuration (level 1)
   5. User Guide (level 0)
      6. Basic Usage (level 1)
      7. Advanced Usage (level 1)
   ```

2. **フォールバック戦略**
   - ナビゲーションが見つからない場合
   - ファイル名のアルファベット順
   - 番号プレフィックスを考慮

## テスト要件

### テストケース

```python
def test_detect_order_nested_navigation():
    """ネストされたナビゲーションでの順序検出"""
    html = """
    <nav>
        <ul>
            <li><a href="index.html">Home</a></li>
            <li>
                <a href="guide.html">Guide</a>
                <ul>
                    <li><a href="install.html">Install</a></li>
                    <li><a href="config.html">Config</a></li>
                </ul>
            </li>
        </ul>
    </nav>
    """

    result = service.detect_order(request)
    assert len(result.ordered_files) == 4
    assert result.ordered_files[0].title == "Home"
    assert result.ordered_files[1].title == "Guide"
    assert result.ordered_files[2].level == 1  # Installは子要素
```

## 実装のポイント

1. **相対パスの解決**
   - `href="../guide.html"` → 絶対パスに変換
   - キャッシュディレクトリ内のファイルと照合

2. **循環参照の処理**
   - 既に訪問したリンクをスキップ
   - 最大深度の制限

3. **欠落ファイルの処理**
   - リンクはあるがファイルがない場合
   - 警告を出してスキップ

## 受け入れ基準

- [ ] 階層構造を正しく認識
- [ ] 順序番号が連続している
- [ ] 循環参照を処理できる
- [ ] 1000ページ規模でも高速動作

## 推定工数

4-5時間

## 依存関係

- [06. Detect:Navサービスの実装](20250706-06-implement-detect-nav.md)

## 次のタスク

→ [08. Markdownコンバーターの実装](20250706-08-implement-markdown-converter.md)
