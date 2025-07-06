"""
site2 パイプライン統合の契約定義（Contract-First Development）
"""

from typing import Protocol, List, Optional, Dict, Any, Union
from pathlib import Path
from dataclasses import dataclass, field

from .fetch_contracts import FetchServiceProtocol
from .detect_contracts import DetectServiceProtocol
from .build_contracts import BuildServiceProtocol, OutputFormat


# DTOs (Data Transfer Objects) - 外部とのやり取り用
@dataclass
class PipelineRequest:
    """パイプライン実行要求の契約"""

    url: str
    format: OutputFormat
    output_path: Optional[Path] = None
    depth: int = 3
    force_refresh: bool = False
    main_selector: Optional[str] = None
    nav_selector: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """契約の事前条件を検証"""
        assert self.url.strip(), "URL cannot be empty"
        assert self.url.startswith(("http://", "https://")), (
            f"URL must be HTTP(S): {self.url}"
        )
        assert 0 <= self.depth <= 10, f"Depth must be 0-10: {self.depth}"

        # 出力パスが指定されている場合、親ディレクトリが存在することを確認
        if self.output_path:
            assert self.output_path.parent.exists(), (
                f"Output directory must exist: {self.output_path.parent}"
            )


@dataclass
class PipelineStepResult:
    """パイプラインステップの結果"""

    step_name: str
    success: bool
    duration_seconds: float
    output: Any = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    """パイプライン実行結果の契約"""

    request: PipelineRequest
    success: bool
    final_output: Optional[Union[str, bytes]] = None
    output_path: Optional[Path] = None
    total_duration_seconds: float = 0.0
    steps: List[PipelineStepResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """契約の事後条件を検証"""
        assert self.total_duration_seconds >= 0, "Duration must be non-negative"

        if self.success:
            assert self.final_output is not None, "Must have output if successful"

        # ステップごとの期間の合計は、総期間以下でなければならない
        step_total = sum(step.duration_seconds for step in self.steps)
        assert step_total <= self.total_duration_seconds + 1.0, (
            "Step duration sum cannot exceed total duration significantly"
        )


@dataclass
class AutoCommandRequest:
    """autoコマンドの要求"""

    url: str
    format: OutputFormat = OutputFormat.MARKDOWN
    output_path: Optional[Path] = None

    def validate(self) -> None:
        """契約の事前条件を検証"""
        assert self.url.strip(), "URL cannot be empty"
        assert self.url.startswith(("http://", "https://")), (
            f"URL must be HTTP(S): {self.url}"
        )


@dataclass
class AutoCommandResult:
    """autoコマンドの結果"""

    success: bool
    output_file: Optional[Path] = None
    message: str = ""
    error: Optional[str] = None

    def validate(self) -> None:
        """契約の事後条件を検証"""
        if self.success:
            assert self.output_file is not None, "Must have output file if successful"
            assert self.output_file.exists(), (
                f"Output file must exist: {self.output_file}"
            )
        else:
            assert self.error is not None, "Must have error message if failed"


# サービスインターフェース（ポート）
class PipelineServiceProtocol(Protocol):
    """パイプラインサービスの契約"""

    def execute(self, request: PipelineRequest) -> PipelineResult:
        """
        完全なパイプラインを実行

        実行ステップ:
        1. Fetch: Webサイトをクロールしてキャッシュ
        2. DetectMain: メインコンテンツセレクタを検出
        3. DetectNav: ナビゲーションセレクタを検出
        4. DetectOrder: ドキュメント順序を検出
        5. Build: 最終ドキュメントを生成

        事前条件:
        - request.url は有効なHTTP(S) URL
        - request.format は有効な出力フォーマット

        事後条件:
        - PipelineResultが返される
        - 成功時は final_output にコンテンツが含まれる
        - 各ステップの結果がstepsに記録される

        例外:
        - PipelineError: パイプライン実行に失敗
        - その他、各ステップの例外がそのまま伝播する場合がある
        """
        ...

    def execute_auto(self, request: AutoCommandRequest) -> AutoCommandResult:
        """
        autoコマンドを実行（簡易版パイプライン）

        事前条件:
        - request.url は有効なHTTP(S) URL

        事後条件:
        - AutoCommandResultが返される
        - 成功時はファイルが生成される

        例外:
        - PipelineError: 実行に失敗
        """
        ...


class PipelineConfigProtocol(Protocol):
    """パイプライン設定の契約"""

    def get_default_options(self, format: OutputFormat) -> Dict[str, Any]:
        """
        フォーマット別のデフォルトオプションを取得

        事前条件:
        - format は有効なOutputFormat

        事後条件:
        - 設定辞書が返される
        """
        ...

    def validate_options(
        self, options: Dict[str, Any], format: OutputFormat
    ) -> List[str]:
        """
        オプションを検証

        事前条件:
        - options は辞書
        - format は有効なOutputFormat

        事後条件:
        - 検証エラーのリストが返される（空の場合は問題なし）
        """
        ...


class PipelineServiceFactoryProtocol(Protocol):
    """パイプラインサービスファクトリーの契約"""

    def create_pipeline(
        self,
        fetch_service: FetchServiceProtocol,
        detect_service: DetectServiceProtocol,
        build_service: BuildServiceProtocol,
    ) -> PipelineServiceProtocol:
        """
        パイプラインサービスを作成

        事前条件:
        - 各サービスが有効なインスタンス

        事後条件:
        - 設定されたPipelineServiceが返される
        """
        ...


# エラー定義
class PipelineError(Exception):
    """パイプライン実行の基底エラー"""

    code: str = "PIPELINE_ERROR"


class PipelineStepError(PipelineError):
    """パイプラインステップエラー"""

    code: str = "PIPELINE_STEP_ERROR"

    def __init__(
        self, step_name: str, message: str, original_error: Optional[Exception] = None
    ):
        super().__init__(f"Step '{step_name}' failed: {message}")
        self.step_name = step_name
        self.original_error = original_error


class PipelineConfigError(PipelineError):
    """パイプライン設定エラー"""

    code: str = "PIPELINE_CONFIG_ERROR"


class PipelineTimeoutError(PipelineError):
    """パイプラインタイムアウトエラー"""

    code: str = "PIPELINE_TIMEOUT_ERROR"
