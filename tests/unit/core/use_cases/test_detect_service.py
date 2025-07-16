"""
DetectServiceの単体テスト
"""

import pytest
from unittest.mock import Mock
from pathlib import Path
from bs4 import BeautifulSoup
import tempfile
import os

from site2.core.use_cases.detect_service import DetectService
from site2.core.ports.detect_contracts import (
    DetectMainRequest,
    DetectMainResult,
    DetectNavRequest,
    DetectNavResult,
    DetectOrderRequest,
    DetectOrderResult,
    DetectError,
)
from site2.core.domain.detect_domain import Navigation, NavigationStructure
from site2.core.ports.parser_contracts import (
    ParseResult,
    SelectorSearchResult,
    HTMLMetadata,
)
from site2.core.ports.detect_contracts import (
    MainContentDetectionResult,
)
from site2.core.domain.detect_domain import SelectorCandidate


class TestDetectService:
    """DetectServiceの単体テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.mock_html_parser = Mock()
        self.mock_html_analyzer = Mock()
        self.mock_main_content_detector = Mock()
        self.service = DetectService(
            html_parser=self.mock_html_parser,
            html_analyzer=self.mock_html_analyzer,
            main_content_detector=self.mock_main_content_detector,
        )

    def test_detect_main_success(self):
        """メインコンテンツ検出の成功テスト"""
        # テスト用のHTMLファイルを作成
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write("<html><main>content</main></html>")
            test_file = Path(f.name)

        try:
            # モックの設定
            mock_soup = BeautifulSoup(
                "<html><main>content</main></html>", "html.parser"
            )
            self.mock_html_parser.parse.return_value = ParseResult(
                file_path=test_file,
                soup=mock_soup,
                encoding="utf-8",
                parse_time_seconds=0.1,
                warnings=[],
            )

            # MainContentDetectorの結果をモック
            mock_candidates = [
                SelectorCandidate(
                    selector="main",
                    score=0.9,
                    reasoning="セマンティックセレクタ 'main'",
                    element_count=1,
                    metadata={"element": mock_soup.find("main")},
                ),
                SelectorCandidate(
                    selector="article",
                    score=0.7,
                    reasoning="セマンティックセレクタ 'article'",
                    element_count=0,
                    metadata={"element": None},
                ),
            ]

            self.mock_main_content_detector.detect_main_content.return_value = (
                MainContentDetectionResult(
                    candidates=mock_candidates,
                    confidence=0.9,
                    primary_selector="main",
                )
            )

            # テスト実行
            request = DetectMainRequest(file_path=test_file)
            result = self.service.detect_main(request)

            # 結果の検証
            assert isinstance(result, DetectMainResult)
            assert result.file_path == test_file
            assert result.confidence == 0.9
            assert result.primary_selector == "main"
            assert len(result.selectors) == 2
            assert result.selectors[0] == "main"
            assert result.selectors[1] == "article"
            assert len(result.candidates) == 2
            assert result.candidates[0].selector == "main"
            assert result.candidates[0].score == 0.9

        finally:
            # テストファイルを削除
            os.unlink(test_file)

    def test_detect_main_parser_error(self):
        """パーサーエラーのテスト"""
        # テスト用のHTMLファイルを作成
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write("<html><main>content</main></html>")
            test_file = Path(f.name)

        try:
            # パーサーがエラーを発生させる
            self.mock_html_parser.parse.side_effect = Exception("Parse error")

            request = DetectMainRequest(file_path=test_file)

            with pytest.raises(DetectError) as exc_info:
                self.service.detect_main(request)

            assert "Main content detection failed" in str(exc_info.value)

        finally:
            # テストファイルを削除
            os.unlink(test_file)

    def test_detect_main_no_candidates(self):
        """候補が見つからない場合のテスト"""
        # テスト用のHTMLファイルを作成
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write("<html><body></body></html>")
            test_file = Path(f.name)

        try:
            # 空のHTML
            mock_soup = BeautifulSoup("<html><body></body></html>", "html.parser")
            self.mock_html_parser.parse.return_value = ParseResult(
                file_path=test_file,
                soup=mock_soup,
                encoding="utf-8",
                parse_time_seconds=0.1,
                warnings=[],
            )

            self.mock_main_content_detector.detect_main_content.return_value = (
                MainContentDetectionResult(
                    candidates=[],
                    confidence=0.0,
                    primary_selector="",
                )
            )

            request = DetectMainRequest(file_path=test_file)
            result = self.service.detect_main(request)

            assert result.confidence == 0.0
            assert result.primary_selector == "body"  # デフォルト値
            assert len(result.selectors) == 1  # bodyが追加される
            assert result.selectors[0] == "body"
            assert len(result.candidates) == 0

        finally:
            # テストファイルを削除
            os.unlink(test_file)

    def test_detect_nav_success(self):
        """ナビゲーション検出の成功テスト"""
        # テスト用のHTMLファイルを作成
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write('<html><nav><a href="/page1">Page 1</a></nav></html>')
            test_file = Path(f.name)

        try:
            # テスト用のHTML（nav要素あり）
            html_content = """
            <html>
                <body>
                    <nav>
                        <a href="/page1">Page 1</a>
                        <a href="/page2">Page 2</a>
                        <a href="https://external.com">External</a>
                    </nav>
                </body>
            </html>
            """
            mock_soup = BeautifulSoup(html_content, "html.parser")
            self.mock_html_parser.parse.return_value = ParseResult(
                file_path=test_file,
                soup=mock_soup,
                encoding="utf-8",
                parse_time_seconds=0.1,
                warnings=[],
            )

            # nav要素を検索
            nav_element = mock_soup.find("nav")
            self.mock_html_parser.find_by_selectors.return_value = SelectorSearchResult(
                matched_selector="nav",
                elements=[nav_element],
                search_method="first_match",
            )

            request = DetectNavRequest(file_path=test_file)
            result = self.service.detect_nav(request)

            assert isinstance(result, DetectNavResult)
            assert result.file_path == test_file
            assert result.confidence == 0.8
            assert result.primary_selector == "nav"
            assert len(result.selectors) == 1
            assert result.selectors[0] == "nav"
            assert len(result.nav_links) == 3

            # リンクの検証
            links = result.nav_links
            assert links[0].text == "Page 1"
            assert links[0].href == "/page1"
            assert not links[0].is_external

            assert links[2].text == "External"
            assert links[2].href == "https://external.com"
            assert not links[2].is_external

        finally:
            # テストファイルを削除
            os.unlink(test_file)

    def test_detect_nav_no_navigation(self):
        """ナビゲーションが見つからない場合のテスト"""
        # テスト用のHTMLファイルを作成
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write("<html><body><p>No navigation</p></body></html>")
            test_file = Path(f.name)

        try:
            # nav要素がないHTML
            mock_soup = BeautifulSoup(
                "<html><body><p>No navigation</p></body></html>", "html.parser"
            )
            self.mock_html_parser.parse.return_value = ParseResult(
                file_path=test_file,
                soup=mock_soup,
                encoding="utf-8",
                parse_time_seconds=0.1,
                warnings=[],
            )

            # セレクタ検索で何も見つからない
            self.mock_html_parser.find_by_selectors.return_value = SelectorSearchResult(
                matched_selector=None,
                elements=[],
                search_method="first_match",
            )

            request = DetectNavRequest(file_path=test_file)
            result = self.service.detect_nav(request)

            assert result.confidence == 0.0
            assert result.primary_selector == "nav"  # デフォルト値
            assert len(result.selectors) == 1  # navが追加される
            assert result.selectors[0] == "nav"
            assert len(result.nav_links) == 0

        finally:
            # テストファイルを削除
            os.unlink(test_file)

    def test_detect_order_success(self):
        """順序検出の成功テスト"""
        # テスト用のディレクトリを作成
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)

            # テスト用のHTMLファイルを作成
            (test_dir / "index.html").write_text(
                "<html><title>Home Page</title></html>"
            )
            (test_dir / "page1.html").write_text("<html><title>Page 1</title></html>")
            (test_dir / "page2.html").write_text("<html><title>Page 2</title></html>")

            # 各ファイルのパース結果をモック
            def mock_parse_side_effect(parse_request):
                file_path = parse_request.file_path
                if file_path.name == "index.html":
                    soup = BeautifulSoup(
                        "<html><title>Home Page</title></html>", "html.parser"
                    )
                elif file_path.name == "page1.html":
                    soup = BeautifulSoup(
                        "<html><title>Page 1</title></html>", "html.parser"
                    )
                else:
                    soup = BeautifulSoup(
                        "<html><title>Page 2</title></html>", "html.parser"
                    )

                return ParseResult(
                    file_path=file_path,
                    soup=soup,
                    encoding="utf-8",
                    parse_time_seconds=0.1,
                    warnings=[],
                )

            self.mock_html_parser.parse.side_effect = mock_parse_side_effect

            # メタデータ抽出のモック
            def mock_extract_metadata_side_effect(soup):
                title_tag = soup.find("title")
                title = title_tag.string if title_tag else None
                return HTMLMetadata(
                    title=title,
                    description=None,
                    keywords=None,
                    author=None,
                    language=None,
                    meta_tags={},
                    og_tags={},
                )

            self.mock_html_analyzer.extract_metadata.side_effect = (
                mock_extract_metadata_side_effect
            )

            # モックのNavigation
            mock_navigation = Navigation(
                selector="nav",
                structure=NavigationStructure(root_selector="nav", links=[]),
            )

            request = DetectOrderRequest(
                cache_directory=test_dir,
                navigation=mock_navigation,
            )
            result = self.service.detect_order(request)

            assert isinstance(result, DetectOrderResult)
            assert result.cache_directory == test_dir
            assert result.confidence == 0.6
            assert result.method == "alphabetical"
            assert len(result.ordered_files) == 3

            # ファイルがアルファベット順に並んでいることを確認
            files = result.ordered_files
            assert files[0].file_path.name == "index.html"
            assert files[0].title == "Home Page"
            assert files[0].order == 0

            assert files[1].file_path.name == "page1.html"
            assert files[1].title == "Page 1"
            assert files[1].order == 1

            assert files[2].file_path.name == "page2.html"
            assert files[2].title == "Page 2"
            assert files[2].order == 2

    def test_detect_order_no_files(self):
        """HTMLファイルがない場合のテスト"""
        # 空のディレクトリを作成
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)

            mock_navigation = Navigation(
                selector="nav",
                structure=NavigationStructure(root_selector="nav", links=[]),
            )
            request = DetectOrderRequest(
                cache_directory=test_dir,
                navigation=mock_navigation,
            )
            result = self.service.detect_order(request)

            assert result.confidence == 0.0
            assert result.method == "alphabetical"
            assert len(result.ordered_files) == 0

    def test_detect_order_parse_error(self):
        """パース中にエラーが発生した場合のテスト"""
        # テスト用のディレクトリを作成
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)

            # テスト用のHTMLファイルを作成
            (test_dir / "error.html").write_text("<html><title>Error</title></html>")

            # パースエラーが発生
            self.mock_html_parser.parse.side_effect = Exception("Parse error")

            mock_navigation = Navigation(
                selector="nav",
                structure=NavigationStructure(root_selector="nav", links=[]),
            )
            request = DetectOrderRequest(
                cache_directory=test_dir,
                navigation=mock_navigation,
            )
            result = self.service.detect_order(request)

            # エラーが発生してもファイル名をタイトルとして使用
            assert len(result.ordered_files) == 1
            assert result.ordered_files[0].title == "error"
