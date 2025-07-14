"""
WgetCrawlerの実装

subprocessでwgetを使用してWebサイトをクローリング
"""

import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import tempfile

from loguru import logger

from ...core.domain.fetch_domain import WebsiteURL, WebsiteCache, CrawlDepth, CachedPage
from ...core.ports.fetch_contracts import WebCrawlerProtocol, NetworkError


class WgetCrawler(WebCrawlerProtocol):
    """wgetを使用したWebクローラーの実装"""

    def __init__(self, timeout: int = 300):
        """
        Args:
            timeout: wgetのタイムアウト秒数（デフォルト: 300秒）
        """
        self.timeout = timeout

    def crawl(
        self,
        url: WebsiteURL,
        depth: CrawlDepth,
        existing_cache: Optional[WebsiteCache] = None,
    ) -> List[CachedPage]:
        """
        wgetを使用してWebサイトをクロール

        Args:
            url: クロール対象のURL
            depth: クロール深度
            existing_cache: 既存のキャッシュ（差分更新用）

        Returns:
            List[CachedPage]: クロールされたページのリスト

        Raises:
            NetworkError: ネットワークエラーまたはwget実行エラー
        """
        logger.info(f"Starting wget crawl for {url} with depth {depth.value}")

        # 出力ディレクトリの準備
        output_dir = self._prepare_output_directory(url)

        # wgetコマンドの構築
        wget_command = self._build_wget_command(url, depth, output_dir, existing_cache)

        # wgetの実行
        try:
            logger.debug(f"Executing: {' '.join(wget_command)}")
            result = subprocess.run(
                wget_command, capture_output=True, text=True, timeout=self.timeout
            )

            if result.returncode != 0:
                stderr = result.stderr.strip()
                logger.error(
                    f"Wget failed with exit code {result.returncode}: {stderr}"
                )
                raise NetworkError(f"Wget failed: {stderr}")

        except subprocess.TimeoutExpired:
            logger.error(f"Wget timeout after {self.timeout} seconds")
            raise NetworkError(f"Wget timeout after {self.timeout} seconds")
        except Exception as e:
            logger.error(f"Failed to execute wget: {e}")
            raise NetworkError(f"Failed to execute wget: {e}") from e

        # クロールされたファイルを収集
        cached_pages = self._collect_cached_pages(url, output_dir)

        logger.info(f"Crawl completed: {len(cached_pages)} pages fetched")
        return cached_pages

    def _prepare_output_directory(self, url: WebsiteURL) -> Path:
        """出力ディレクトリの準備"""
        # 一時ディレクトリを作成（後でFetchServiceが正式な場所に移動）
        temp_dir = Path(tempfile.mkdtemp(prefix=f"wget_{url.domain}_"))
        logger.debug(f"Created temporary directory: {temp_dir}")
        return temp_dir

    def _build_wget_command(
        self,
        url: WebsiteURL,
        depth: CrawlDepth,
        output_dir: Path,
        existing_cache: Optional[WebsiteCache],
    ) -> List[str]:
        """wgetコマンドの構築"""
        command = [
            "wget",
            "-r",  # 再帰的ダウンロード
            "-l",
            str(depth.value),  # 深さ制限
            "-k",  # リンクをローカル用に変換
            "-E",  # 適切な拡張子を付ける
            "-np",  # 親ディレクトリを辿らない
            "-H",  # ホストをまたぐダウンロードを許可（ただし-Dで制限）
            "-D",
            url.domain,  # 指定ドメインのみに制限
            "-P",
            str(output_dir),  # 出力ディレクトリ
            "--no-check-certificate",  # SSL証明書の検証をスキップ（開発用）
            "--user-agent",
            "Mozilla/5.0 (compatible; site2/1.0)",
            "--wait",
            "0.5",  # サーバーへの負荷軽減
            "--random-wait",  # ランダムな待機時間
            "--quota",
            "100m",  # 最大ダウンロードサイズ
        ]

        # 既存キャッシュがある場合は差分更新モード
        if existing_cache:
            command.extend(["-N", "--timestamping"])  # タイムスタンプベースの更新

        command.append(str(url.value))

        return command

    def _collect_cached_pages(
        self, url: WebsiteURL, output_dir: Path
    ) -> List[CachedPage]:
        """クロールされたファイルを収集してCachedPageリストを作成"""
        cached_pages = []

        # HTMLファイルを検索
        html_files = list(output_dir.glob("**/*.html")) + list(
            output_dir.glob("**/*.htm")
        )

        for file_path in html_files:
            try:
                # ファイルサイズを取得
                size_bytes = file_path.stat().st_size

                # 相対パスを取得
                relative_path = file_path.relative_to(output_dir)

                # ページURLを構築
                page_url_str = self._construct_page_url(url, relative_path)
                page_url = WebsiteURL(value=page_url_str)

                # CachedPageを作成
                cached_page = CachedPage(
                    page_url=page_url,
                    local_path=file_path,
                    content_type=self._get_content_type(file_path),
                    size_bytes=size_bytes,
                    fetched_at=datetime.now(),
                )

                cached_pages.append(cached_page)

            except Exception as e:
                logger.warning(f"Failed to process file {file_path}: {e}")
                continue

        return cached_pages

    def _construct_page_url(self, base_url: WebsiteURL, relative_path: Path) -> str:
        """相対パスからページURLを構築"""
        # wgetが作成するディレクトリ構造から実際のURLを再構築
        # 例: example.com/path/to/page.html -> https://example.com/path/to/page.html

        parts = relative_path.parts
        if len(parts) > 0 and parts[0] == base_url.domain:
            # ドメイン部分を除去
            parts = parts[1:]

        # URLを再構築
        url_path = "/".join(parts)
        base_str = str(base_url.value).rstrip("/")

        if url_path:
            return f"{base_str}/{url_path}"
        return base_str

    def _get_content_type(self, file_path: Path) -> str:
        """ファイル拡張子からContent-Typeを推定"""
        extension = file_path.suffix.lower()

        content_type_map = {
            ".html": "text/html",
            ".htm": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".xml": "application/xml",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".pdf": "application/pdf",
            ".txt": "text/plain",
        }

        return content_type_map.get(extension, "application/octet-stream")
