"""
HeuristicMainContentDetectorの単体テスト
"""

from unittest.mock import Mock
from bs4 import BeautifulSoup

from site2.adapters.detectors.heuristic_detector import HeuristicMainContentDetector
from site2.core.ports.detect_contracts import (
    MainContentDetectionResult,
)
from site2.core.domain.detect_domain import SelectorCandidate


class TestHeuristicMainContentDetector:
    """HeuristicMainContentDetectorの単体テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.mock_html_analyzer = Mock()
        self.detector = HeuristicMainContentDetector(self.mock_html_analyzer)

    def test_detect_main_content_semantic_selectors(self):
        """セマンティックセレクタによる検出テスト"""
        html_content = """
        <html>
            <body>
                <header>Header</header>
                <main>
                    <article>
                        <h1>Title</h1>
                        <p>Paragraph 1</p>
                        <p>Paragraph 2</p>
                        <p>Paragraph 3</p>
                    </article>
                </main>
                <footer>Footer</footer>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, "html.parser")

        result = self.detector.detect_main_content(soup)

        assert isinstance(result, MainContentDetectionResult)
        assert len(result.candidates) > 0
        assert result.confidence > 0.0

        # 最高スコアの候補を確認
        top_candidate = result.candidates[0]
        assert top_candidate.selector in ["main", "main article", "article"]
        assert top_candidate.score > 0.5

    def test_detect_main_content_with_id_and_class(self):
        """IDとクラスによる検出テスト"""
        html_content = """
        <html>
            <body>
                <div id="main-content">
                    <h1>Title</h1>
                    <p>Content paragraph 1</p>
                    <p>Content paragraph 2</p>
                    <p>Content paragraph 3</p>
                </div>
                <div class="sidebar">
                    <p>Sidebar content</p>
                </div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, "html.parser")

        result = self.detector.detect_main_content(soup)

        assert len(result.candidates) > 0

        # main-contentセレクタが検出されることを確認
        selectors = [c.selector for c in result.candidates]
        assert "#main-content" in selectors

    def test_detect_main_content_content_features(self):
        """コンテンツ特徴による検出テスト"""
        html_content = """
        <html>
            <body>
                <div class="content-area">
                    <h1>Article Title</h1>
                    <p>This is a long paragraph with substantial content that should be detected as main content.</p>
                    <p>Another paragraph with meaningful content.</p>
                    <p>Third paragraph to increase the paragraph count.</p>
                </div>
                <div class="ads">
                    <a href="#">Ad link</a>
                    <a href="#">Another ad</a>
                </div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, "html.parser")

        result = self.detector.detect_main_content(soup)

        assert len(result.candidates) > 0
        assert result.confidence > 0.0

        # content-areaが検出されることを確認
        selectors = [c.selector for c in result.candidates]
        assert ".content-area" in selectors

    def test_detect_main_content_exclusion_filter(self):
        """除外フィルタのテスト"""
        html_content = """
        <html>
            <body>
                <nav class="navigation">
                    <a href="#">Link 1</a>
                    <a href="#">Link 2</a>
                </nav>
                <main>
                    <h1>Main Content</h1>
                    <p>This is the main content.</p>
                    <p>More content here.</p>
                </main>
                <footer>
                    <p>Footer content</p>
                </footer>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, "html.parser")

        result = self.detector.detect_main_content(soup)

        # navやfooterが除外され、mainが選択されることを確認
        selectors = [c.selector for c in result.candidates]
        assert "main" in selectors
        assert "nav" not in selectors
        assert "footer" not in selectors

    def test_detect_main_content_empty_html(self):
        """空のHTMLの場合のテスト"""
        html_content = "<html><body></body></html>"
        soup = BeautifulSoup(html_content, "html.parser")

        result = self.detector.detect_main_content(soup)

        assert len(result.candidates) == 0
        assert result.confidence == 0.0
        assert result.primary_selector == ""

    def test_detect_main_content_low_quality_content(self):
        """低品質コンテンツの場合のテスト"""
        html_content = """
        <html>
            <body>
                <div class="content">
                    <p>Short</p>
                </div>
                <div class="ads">
                    <a href="#">Ad</a>
                    <a href="#">Ad</a>
                </div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, "html.parser")

        result = self.detector.detect_main_content(soup)

        # 低品質コンテンツは信頼度が低い、または除外される
        assert len(result.candidates) == 0 or result.confidence < 0.7

    def test_calculate_text_density(self):
        """テキスト密度計算のテスト"""
        # 高密度テキスト
        high_density_html = (
            "<p>This is a lot of text content without much HTML markup.</p>"
        )
        high_density_element = BeautifulSoup(high_density_html, "html.parser").find("p")
        high_density = self.detector._calculate_text_density(high_density_element)

        # 低密度テキスト（多くのHTML）
        low_density_html = """
        <div>
            <span><strong><em>Short</em></strong></span>
        </div>
        """
        low_density_element = BeautifulSoup(low_density_html, "html.parser").find("div")
        low_density = self.detector._calculate_text_density(low_density_element)

        assert high_density > low_density
        assert 0.0 <= high_density <= 1.0
        assert 0.0 <= low_density <= 1.0

    def test_build_selector(self):
        """セレクタ構築のテスト"""
        # ID付き要素
        id_html = '<div id="main-content">Content</div>'
        id_element = BeautifulSoup(id_html, "html.parser").find("div")
        id_selector = self.detector._build_selector(id_element)
        assert id_selector == "#main-content"

        # クラス付き要素
        class_html = '<div class="content primary">Content</div>'
        class_element = BeautifulSoup(class_html, "html.parser").find("div")
        class_selector = self.detector._build_selector(class_element)
        assert class_selector == ".content"

        # タグのみ
        tag_html = "<article>Content</article>"
        tag_element = BeautifulSoup(tag_html, "html.parser").find("article")
        tag_selector = self.detector._build_selector(tag_element)
        assert tag_selector == "article"

    def test_calculate_confidence(self):
        """信頼度計算のテスト"""
        # 高スコア候補
        high_score_candidates = [
            SelectorCandidate(
                selector="main", score=0.9, reasoning="High score", element_count=1
            ),
            SelectorCandidate(
                selector="article", score=0.8, reasoning="Medium score", element_count=1
            ),
        ]
        high_confidence = self.detector._calculate_confidence(high_score_candidates)

        # 低スコア候補
        low_score_candidates = [
            SelectorCandidate(
                selector="div", score=0.3, reasoning="Low score", element_count=1
            ),
        ]
        low_confidence = self.detector._calculate_confidence(low_score_candidates)

        # 候補なし
        no_candidates = []
        no_confidence = self.detector._calculate_confidence(no_candidates)

        assert high_confidence > low_confidence
        assert no_confidence == 0.0
        assert 0.0 <= high_confidence <= 1.0
        assert 0.0 <= low_confidence <= 1.0

    def test_detect_main_content_multiple_main_tags(self):
        """複数のmainタグがある場合のテスト"""
        html_content = """
        <html>
            <body>
                <main>
                    <p>First main content</p>
                </main>
                <main>
                    <p>Second main content</p>
                </main>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, "html.parser")

        result = self.detector.detect_main_content(soup)

        assert len(result.candidates) > 0
        assert result.candidates[0].selector == "main"
        assert result.candidates[0].element_count == 2  # 2つのmain要素

    def test_detect_main_content_complex_structure(self):
        """複雑な構造のHTMLテスト"""
        html_content = """
        <html>
            <body>
                <div class="wrapper">
                    <header>
                        <h1>Site Title</h1>
                        <nav>
                            <a href="#">Home</a>
                            <a href="#">About</a>
                        </nav>
                    </header>
                    <main>
                        <article class="post">
                            <h2>Article Title</h2>
                            <p>Article content paragraph 1.</p>
                            <p>Article content paragraph 2.</p>
                            <p>Article content paragraph 3.</p>
                        </article>
                        <aside class="sidebar">
                            <h3>Related</h3>
                            <p>Related content</p>
                        </aside>
                    </main>
                    <footer>
                        <p>Footer content</p>
                    </footer>
                </div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, "html.parser")

        result = self.detector.detect_main_content(soup)

        assert len(result.candidates) > 0
        assert result.confidence > 0.5

        # mainやarticleが上位候補に含まれることを確認
        top_selectors = [c.selector for c in result.candidates[:2]]
        assert any(
            selector in ["main", "article", "main article", ".post"]
            for selector in top_selectors
        )

    def test_detect_main_content_with_options(self):
        """オプション付きでの検出テスト"""
        options = {
            "enable_semantic_selectors": True,
            "enable_content_analysis": False,
            "enable_exclusion_filter": True,
            "min_text_density": 0.1,
            "min_paragraph_count": 3,
        }
        detector = HeuristicMainContentDetector(self.mock_html_analyzer, options)

        html_content = """
        <html>
            <body>
                <main>
                    <h1>Title</h1>
                    <p>Paragraph 1</p>
                    <p>Paragraph 2</p>
                    <p>Paragraph 3</p>
                </main>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, "html.parser")

        result = detector.detect_main_content(soup)

        assert len(result.candidates) > 0
        assert result.candidates[0].selector == "main"

    def test_detect_main_content_error_handling(self):
        """エラーハンドリングのテスト"""
        # 不正なHTMLでもエラーが発生しないことを確認
        invalid_html = "<html><body><div><p>Unclosed tags"
        soup = BeautifulSoup(invalid_html, "html.parser")

        result = self.detector.detect_main_content(soup)

        # エラーが発生せず、何らかの結果が返されることを確認
        assert isinstance(result, MainContentDetectionResult)
        assert isinstance(result.candidates, list)
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0
