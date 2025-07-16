"""
ヒューリスティックベースのメインコンテンツ検出器
"""

from typing import List
from bs4 import BeautifulSoup, Tag
from loguru import logger

from ...core.ports.detect_contracts import (
    MainContentDetectorProtocol,
    MainContentDetectionResult,
    HeuristicDetectionError,
)
from ...core.domain.detect_domain import SelectorCandidate
from ...core.ports.parser_contracts import HTMLAnalyzerProtocol


class HeuristicMainContentDetector(MainContentDetectorProtocol):
    """
    ヒューリスティックベースのメインコンテンツ検出器
    BeautifulSoupとHTMLアナライザーを使用した検出アルゴリズム
    """

    # セマンティックセレクタの優先順位（高スコア順）
    SEMANTIC_SELECTORS = {
        "main": 100,
        "article": 90,
        "[role='main']": 95,
        "main article": 95,
        "div[role='main']": 90,
        ".main": 70,
        "#main": 80,
        ".content": 70,
        "#content": 80,
        ".main-content": 75,
        "#main-content": 85,
        ".article": 65,
        "#article": 75,
        ".post": 60,
        "#post": 70,
        ".entry": 60,
        "#entry": 70,
    }

    # 除外すべきセレクタ（これらの要素は避ける）
    EXCLUSION_SELECTORS = [
        "nav",
        "header",
        "footer",
        "aside",
        "sidebar",
        ".nav",
        ".header",
        ".footer",
        ".aside",
        ".sidebar",
        "#nav",
        "#header",
        "#footer",
        "#aside",
        "#sidebar",
        ".advertisement",
        ".ads",
        ".ad",
        ".banner",
        ".comments",
        ".comment",
        ".social",
        ".share",
        ".related",
        ".recommendation",
        ".sidebar-content",
    ]

    def __init__(self, html_analyzer: HTMLAnalyzerProtocol, options: dict = None):
        """
        Args:
            html_analyzer: HTMLアナライザー
            options: 検出オプション
        """
        self.html_analyzer = html_analyzer
        self.options = options or {}

        # オプションの設定
        self.enable_semantic = self.options.get("enable_semantic_selectors", True)
        self.enable_content_analysis = self.options.get("enable_content_analysis", True)
        self.enable_exclusion = self.options.get("enable_exclusion_filter", True)
        self.min_text_density = self.options.get("min_text_density", 0.05)
        self.min_paragraph_count = self.options.get("min_paragraph_count", 2)

    def detect_main_content(self, soup: BeautifulSoup) -> MainContentDetectionResult:
        """
        メインコンテンツを検出

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            MainContentDetectionResult: 検出結果

        Raises:
            HeuristicDetectionError: 検出処理に失敗した場合
        """
        try:
            logger.debug("Starting heuristic main content detection")

            candidates = []

            # 1. セマンティックセレクタによる検出
            if self.enable_semantic:
                semantic_candidates = self._detect_semantic_selectors(soup)
                candidates.extend(semantic_candidates)

            # 2. コンテンツ特徴による検出
            if self.enable_content_analysis:
                content_candidates = self._detect_content_features(soup)
                candidates.extend(content_candidates)

            # 3. 除外フィルタを適用
            if self.enable_exclusion:
                candidates = self._apply_exclusion_filter(candidates, soup)

            # 4. スコアでソート
            candidates.sort(key=lambda x: x.score, reverse=True)

            # 5. 上位3つの候補を選択
            top_candidates = candidates[:3]

            # 6. 信頼度を計算
            confidence = self._calculate_confidence(top_candidates)

            # 7. プライマリセレクタを決定
            primary_selector = top_candidates[0].selector if top_candidates else ""

            logger.debug(
                f"Heuristic detection completed. Found {len(top_candidates)} candidates"
            )

            return MainContentDetectionResult(
                candidates=top_candidates,
                confidence=confidence,
                primary_selector=primary_selector,
            )

        except Exception as e:
            logger.error(f"Heuristic detection failed: {str(e)}")
            raise HeuristicDetectionError(f"Heuristic detection failed: {str(e)}")

    def _detect_semantic_selectors(
        self, soup: BeautifulSoup
    ) -> List[SelectorCandidate]:
        """セマンティックセレクタによる検出"""
        candidates = []

        for selector, base_score in self.SEMANTIC_SELECTORS.items():
            elements = soup.select(selector)

            if elements:
                # 要素の内容を評価
                element = elements[0]  # 最初の要素を使用

                # テキスト密度を計算
                text_density = self._calculate_text_density(element)

                # 段落数を計算
                paragraph_count = len(element.find_all("p"))

                # 見出し数を計算
                heading_count = len(
                    element.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
                )

                # スコアを調整
                adjusted_score = base_score / 100.0  # 0-1の範囲に正規化

                # テキスト密度ボーナス
                if text_density > 0.1:
                    adjusted_score += 0.1

                # 段落数ボーナス
                if paragraph_count > 3:
                    adjusted_score += 0.1

                # 見出し数ボーナス
                if heading_count > 0:
                    adjusted_score += 0.05

                # スコアを0-1の範囲に制限
                adjusted_score = min(adjusted_score, 1.0)

                reasoning = f"セマンティックセレクタ '{selector}' (テキスト密度: {text_density:.2f}, 段落数: {paragraph_count}, 見出し数: {heading_count})"

                candidates.append(
                    SelectorCandidate(
                        selector=selector,
                        score=adjusted_score,
                        reasoning=reasoning,
                        element_count=len(elements),
                        metadata={
                            "text_density": text_density,
                            "paragraph_count": paragraph_count,
                            "heading_count": heading_count,
                            "element": element,
                        },
                    )
                )

        return candidates

    def _detect_content_features(self, soup: BeautifulSoup) -> List[SelectorCandidate]:
        """コンテンツ特徴による検出"""
        candidates = []

        # すべてのdiv要素を評価
        divs = soup.find_all("div")

        for div in divs:
            # IDまたはクラスがある要素のみを評価
            if not (div.get("id") or div.get("class")):
                continue

            # セレクタを構築
            selector = self._build_selector(div)

            # 既に評価済みのセレクタはスキップ
            if any(c.selector == selector for c in candidates):
                continue

            # テキスト密度を計算
            text_density = self._calculate_text_density(div)

            # 最小テキスト密度チェック
            if text_density < self.min_text_density:
                continue

            # 段落数を計算
            paragraph_count = len(div.find_all("p"))

            # 最小段落数チェック
            if paragraph_count < self.min_paragraph_count:
                continue

            # スコアを計算
            score = text_density * 0.5 + min(paragraph_count / 10, 0.3)

            reasoning = f"コンテンツ特徴 (テキスト密度: {text_density:.2f}, 段落数: {paragraph_count})"

            candidates.append(
                SelectorCandidate(
                    selector=selector,
                    score=score,
                    reasoning=reasoning,
                    element_count=1,
                    metadata={
                        "text_density": text_density,
                        "paragraph_count": paragraph_count,
                        "element": div,
                    },
                )
            )

        return candidates

    def _apply_exclusion_filter(
        self, candidates: List[SelectorCandidate], soup: BeautifulSoup
    ) -> List[SelectorCandidate]:
        """除外フィルタを適用"""
        filtered_candidates = []

        for candidate in candidates:
            # 除外セレクタチェック
            should_exclude = False
            element = candidate.metadata.get("element")

            for exclusion_selector in self.EXCLUSION_SELECTORS:
                # 要素が除外セレクタにマッチするかチェック
                if element and element.name:
                    # 要素名チェック
                    if exclusion_selector == element.name:
                        should_exclude = True
                        break

                    # クラス・IDチェック
                    if element.get("class"):
                        classes = " ".join(element.get("class", []))
                        if exclusion_selector.replace(".", "") in classes:
                            should_exclude = True
                            break

                    if element.get("id"):
                        element_id = element.get("id")
                        if exclusion_selector.replace("#", "") == element_id:
                            should_exclude = True
                            break

            if not should_exclude:
                filtered_candidates.append(candidate)

        return filtered_candidates

    def _calculate_text_density(self, element: Tag) -> float:
        """テキスト密度を計算（テキスト/HTML比）"""
        if not element:
            return 0.0

        # テキスト長
        text = element.get_text(strip=True)
        text_length = len(text)

        # HTML長
        html = str(element)
        html_length = len(html)

        if html_length == 0:
            return 0.0

        return text_length / html_length

    def _build_selector(self, element: Tag) -> str:
        """要素からセレクタを構築"""
        if not element:
            return ""

        # ID優先
        if element.get("id"):
            return f"#{element.get('id')}"

        # クラス次点
        if element.get("class"):
            classes = element.get("class")
            if classes:
                return f".{classes[0]}"

        # タグ名のみ
        return element.name or ""

    def _calculate_confidence(self, candidates: List[SelectorCandidate]) -> float:
        """信頼度を計算"""
        if not candidates:
            return 0.0

        # 最高スコアベースの信頼度
        max_score = candidates[0].score

        # 複数の候補がある場合は信頼度を上げる
        if len(candidates) > 1:
            confidence = max_score * 0.9 + 0.1
        else:
            confidence = max_score * 0.8

        return min(confidence, 1.0)
