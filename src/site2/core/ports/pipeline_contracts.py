"""
site2 パイプライン統合の契約定義（Contract-First Development）
"""

from typing import Protocol, List, Optional, Dict, Any, Union
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, ConfigDict, HttpUrl

from .fetch_contracts import FetchServiceProtocol
from .detect_contracts import DetectServiceProtocol
from .build_contracts import BuildServiceProtocol, OutputFormat
from ..domain.fetch_domain import CrawlDepth


# DTOs (Data Transfer Objects) - 外部とのやり取り用
class PipelineRequest(BaseModel):
    """パイプライン実行要求の契約"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    url: HttpUrl = Field(..., description="対象URL")
    format: OutputFormat = Field(..., description="出力フォーマット")
    output_path: Optional[Path] = Field(default=None, description="出力パス")
    depth: CrawlDepth = Field(
        default_factory=lambda: CrawlDepth(value=3), description="クロール深度"
    )
    force_refresh: bool = Field(default=False, description="強制更新フラグ")
    main_selector: Optional[str] = Field(default=None, description="メインセレクタ")
    nav_selector: Optional[str] = Field(
        default=None, description="ナビゲーションセレクタ"
    )
    options: Dict[str, Any] = Field(default_factory=dict, description="オプション")

    # HttpUrlで自動検証されるため、手動バリデーションは不要

    @field_validator("output_path")
    @classmethod
    def validate_output_path(cls, v: Optional[Path]) -> Optional[Path]:
        """出力パスの検証"""
        if v and not v.parent.exists():
            raise ValueError(f"Output directory must exist: {v.parent}")
        return v


class PipelineStepResult(BaseModel):
    """パイプラインステップの結果"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    step_name: str = Field(..., min_length=1, description="ステップ名")
    success: bool = Field(..., description="成功フラグ")
    duration_seconds: float = Field(..., ge=0, description="実行時間(秒)")
    output: Any = Field(default=None, description="出力")
    warnings: List[str] = Field(default_factory=list, description="警告一覧")
    errors: List[str] = Field(default_factory=list, description="エラー一覧")


class PipelineResult(BaseModel):
    """パイプライン実行結果の契約"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    request: PipelineRequest = Field(..., description="元のリクエスト")
    success: bool = Field(..., description="成功フラグ")
    final_output: Optional[Union[str, bytes]] = Field(
        default=None, description="最終出力"
    )
    output_path: Optional[Path] = Field(default=None, description="出力パス")
    total_duration_seconds: float = Field(
        default=0.0, ge=0, description="総実行時間(秒)"
    )
    steps: List[PipelineStepResult] = Field(
        default_factory=list, description="ステップ結果一覧"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="メタデータ")

    @field_validator("final_output")
    @classmethod
    def validate_final_output(
        cls, v: Optional[Union[str, bytes]], info
    ) -> Optional[Union[str, bytes]]:
        """最終出力の検証"""
        success = info.data.get("success", False)
        if success and v is None:
            raise ValueError("Must have output if successful")
        return v

    @field_validator("total_duration_seconds")
    @classmethod
    def validate_total_duration(cls, v: float, info) -> float:
        """総実行時間の検証"""
        steps = info.data.get("steps", [])
        if steps:
            step_total = sum(step.duration_seconds for step in steps)
            if step_total > v + 1.0:
                raise ValueError(
                    "Step duration sum cannot exceed total duration significantly"
                )
        return v


class AutoCommandRequest(BaseModel):
    """autoコマンドの要求"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    url: HttpUrl = Field(..., description="対象URL")
    format: OutputFormat = Field(
        default=OutputFormat.MARKDOWN, description="出力フォーマット"
    )
    output_path: Optional[Path] = Field(default=None, description="出力パス")

    # HttpUrlで自動検証されるため、手動バリデーションは不要


class AutoCommandResult(BaseModel):
    """autoコマンドの結果"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool = Field(..., description="成功フラグ")
    output_file: Optional[Path] = Field(default=None, description="出力ファイル")
    message: str = Field(default="", description="メッセージ")
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
