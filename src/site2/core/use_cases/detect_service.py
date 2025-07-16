"""
DetectService - メインコンテンツ・ナビゲーション・順序検出サービス
"""

from loguru import logger

from ..ports.detect_contracts import (
    DetectServiceProtocol,
    MainContentDetectorProtocol,
    DetectMainRequest,
    DetectMainResult,
    DetectNavRequest,
    DetectNavResult,
    DetectOrderRequest,
    DetectOrderResult,
    SelectorCandidate,
    NavLink,
    OrderedFile,
    DetectError,
)
from ..ports.parser_contracts import (
    HTMLParserProtocol,
    HTMLAnalyzerProtocol,
    ParseRequest,
    SelectorSearchRequest,
)


class DetectService(DetectServiceProtocol):
    """
    Detectサービスの実装
    メインコンテンツ、ナビゲーション、順序の検出を行う
    """

    def __init__(
        self,
        html_parser: HTMLParserProtocol,
        html_analyzer: HTMLAnalyzerProtocol,
        main_content_detector: MainContentDetectorProtocol,
    ):
        """
        Args:
            html_parser: HTMLパーサー
            html_analyzer: HTMLアナライザー
            main_content_detector: メインコンテンツ検出器
        """
        self.html_parser = html_parser
        self.html_analyzer = html_analyzer
        self.main_detector = main_content_detector

    def detect_main(self, request: DetectMainRequest) -> DetectMainResult:
        """
        メインコンテンツのセレクタを検出

        Args:
            request: 検出要求

        Returns:
            DetectMainResult: 検出結果

        Raises:
            DetectError: 検出処理に失敗した場合
        """
        logger.info(f"Starting main content detection for: {request.file_path}")

        try:
            # HTMLファイルをパース
            parse_request = ParseRequest(file_path=request.file_path)
            parse_result = self.html_parser.parse(parse_request)

            # メインコンテンツを検出
            detection_result = self.main_detector.detect_main_content(parse_result.soup)

            # 結果を構築
            candidates = []
            selectors = []

            for candidate in detection_result.candidates:
                candidates.append(
                    SelectorCandidate(
                        selector=candidate.selector,
                        score=candidate.score,
                        reasoning=candidate.reasoning,
                        element_count=candidate.element_count,
                    )
                )
                selectors.append(candidate.selector)

            # プライマリセレクタを決定
            primary_selector = (
                selectors[0] if selectors else "body"
            )  # デフォルト値を設定
            confidence = detection_result.confidence

            # selectorsが空の場合はbodyを追加
            if not selectors:
                selectors = ["body"]

            result = DetectMainResult(
                file_path=request.file_path,
                selectors=selectors,
                confidence=confidence,
                primary_selector=primary_selector,
                candidates=candidates,
            )

            logger.info(
                f"Main content detection completed. Confidence: {confidence:.2f}"
            )
            return result

        except Exception as e:
            logger.error(
                f"Main content detection failed for {request.file_path}: {str(e)}"
            )
            raise DetectError(f"Main content detection failed: {str(e)}")

    def detect_nav(self, request: DetectNavRequest) -> DetectNavResult:
        """
        ナビゲーションのセレクタを検出

        Args:
            request: 検出要求

        Returns:
            DetectNavResult: 検出結果

        Raises:
            DetectError: 検出処理に失敗した場合
        """
        logger.info(f"Starting navigation detection for: {request.file_path}")

        try:
            # HTMLファイルをパース
            parse_request = ParseRequest(file_path=request.file_path)
            parse_result = self.html_parser.parse(parse_request)

            # ナビゲーション検出（実装予定）
            # 現在はプレースホルダー実装
            nav_selectors = ["nav", "ul.nav", ".navigation", "#navigation"]
            nav_links = []

            # 各セレクタを試行
            found_selector = ""
            for selector in nav_selectors:
                search_request = SelectorSearchRequest(
                    soup=parse_result.soup,
                    selectors=[selector],
                    find_all=False,
                )
                search_result = self.html_parser.find_by_selectors(search_request)

                if search_result.elements:
                    found_selector = selector
                    # リンクを抽出
                    element = search_result.elements[0]
                    links = element.find_all("a", href=True)

                    for link in links:
                        href = link.get("href", "")
                        text = link.get_text(strip=True)
                        if text and href:
                            nav_links.append(
                                NavLink(
                                    text=text,
                                    href=href,
                                    level=0,
                                    is_external=href.startswith(
                                        ("http://", "https://")
                                    ),
                                )
                            )
                    break

            # 結果を構築
            selectors = (
                [found_selector] if found_selector else ["nav"]
            )  # デフォルト値を設定
            confidence = 0.8 if found_selector else 0.0
            primary_selector = (
                found_selector if found_selector else "nav"
            )  # デフォルト値を設定

            result = DetectNavResult(
                file_path=request.file_path,
                selectors=selectors,
                confidence=confidence,
                primary_selector=primary_selector,
                nav_links=nav_links,
            )

            logger.info(f"Navigation detection completed. Found {len(nav_links)} links")
            return result

        except Exception as e:
            logger.error(
                f"Navigation detection failed for {request.file_path}: {str(e)}"
            )
            raise DetectError(f"Navigation detection failed: {str(e)}")

    def detect_order(self, request: DetectOrderRequest) -> DetectOrderResult:
        """
        ドキュメントの順序を検出

        Args:
            request: 検出要求

        Returns:
            DetectOrderResult: 検出結果

        Raises:
            DetectError: 順序検出に失敗した場合
        """
        logger.info(f"Starting order detection for: {request.cache_directory}")

        try:
            # HTMLファイルを収集
            html_files = list(request.cache_directory.glob("**/*.html"))

            if not html_files:
                logger.warning(f"No HTML files found in {request.cache_directory}")
                return DetectOrderResult(
                    cache_directory=request.cache_directory,
                    ordered_files=[],
                    confidence=0.0,
                    method="alphabetical",
                )

            # 順序付きファイルを作成（現在はアルファベット順）
            ordered_files = []
            for i, file_path in enumerate(sorted(html_files)):
                # タイトルを抽出
                try:
                    parse_request = ParseRequest(file_path=file_path)
                    parse_result = self.html_parser.parse(parse_request)
                    metadata = self.html_analyzer.extract_metadata(parse_result.soup)
                    title = metadata.title or file_path.stem
                except Exception:
                    title = file_path.stem

                ordered_files.append(
                    OrderedFile(
                        file_path=file_path,
                        title=title,
                        order=i,
                        level=0,
                    )
                )

            result = DetectOrderResult(
                cache_directory=request.cache_directory,
                ordered_files=ordered_files,
                confidence=0.6,  # アルファベット順の信頼度
                method="alphabetical",
            )

            logger.info(
                f"Order detection completed. {len(ordered_files)} files ordered"
            )
            return result

        except Exception as e:
            logger.error(
                f"Order detection failed for {request.cache_directory}: {str(e)}"
            )
            raise DetectError(f"Order detection failed: {str(e)}")
