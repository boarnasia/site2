"""
Playwrightの設定
"""

from typing import Dict, Any

# デフォルトのPlaywright PDF設定
DEFAULT_PLAYWRIGHT_PDF_CONFIG: Dict[str, Any] = {
    # PDF生成オプション
    "format": "A4",
    "print_background": True,
    "margin": {
        "top": "20mm",
        "right": "20mm",
        "bottom": "20mm",
        "left": "20mm",
    },
    "display_header_footer": False,
    "header_template": "",
    "footer_template": "",
    "prefer_css_page_size": True,
    "landscape": False,
    # ブラウザオプション
    "headless": True,
    "viewport": {"width": 1280, "height": 720},
    "timeout": 30000,  # 30秒
    # 待機設定
    "wait_for_load_state": "networkidle",
    "wait_for_timeout": 1000,  # 1秒
}

# 高品質PDF設定
HIGH_QUALITY_PDF_CONFIG: Dict[str, Any] = {
    **DEFAULT_PLAYWRIGHT_PDF_CONFIG,
    "format": "A4",
    "print_background": True,
    "margin": {
        "top": "15mm",
        "right": "15mm",
        "bottom": "15mm",
        "left": "15mm",
    },
    "prefer_css_page_size": True,
    "timeout": 60000,  # 60秒
}

# 軽量PDF設定
LIGHTWEIGHT_PDF_CONFIG: Dict[str, Any] = {
    **DEFAULT_PLAYWRIGHT_PDF_CONFIG,
    "print_background": False,
    "margin": {
        "top": "10mm",
        "right": "10mm",
        "bottom": "10mm",
        "left": "10mm",
    },
    "timeout": 15000,  # 15秒
}


def get_pdf_config_by_name(config_name: str) -> Dict[str, Any]:
    """
    設定名からPDF設定を取得

    Args:
        config_name: 設定名 ("default", "high_quality", "lightweight")

    Returns:
        Dict[str, Any]: Playwright PDF設定

    Raises:
        ValueError: 不正な設定名が指定された場合
    """
    configs = {
        "default": DEFAULT_PLAYWRIGHT_PDF_CONFIG,
        "high_quality": HIGH_QUALITY_PDF_CONFIG,
        "lightweight": LIGHTWEIGHT_PDF_CONFIG,
    }

    if config_name not in configs:
        available_configs = ", ".join(configs.keys())
        raise ValueError(
            f"Unknown config name: {config_name}. Available: {available_configs}"
        )

    return configs[config_name].copy()


def merge_pdf_config(
    base_config: Dict[str, Any], custom_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    PDF設定をマージ

    Args:
        base_config: ベース設定
        custom_config: カスタム設定

    Returns:
        Dict[str, Any]: マージされた設定
    """
    merged = base_config.copy()

    # marginの特別な処理
    if "margin" in custom_config and "margin" in merged:
        margin = merged["margin"].copy()
        margin.update(custom_config["margin"])
        custom_config = custom_config.copy()
        custom_config["margin"] = margin

    # viewportの特別な処理
    if "viewport" in custom_config and "viewport" in merged:
        viewport = merged["viewport"].copy()
        viewport.update(custom_config["viewport"])
        custom_config = custom_config.copy()
        custom_config["viewport"] = viewport

    merged.update(custom_config)
    return merged


def validate_pdf_config(config: Dict[str, Any]) -> None:
    """
    PDF設定の妥当性を検証

    Args:
        config: 検証する設定

    Raises:
        ValueError: 不正な設定値が含まれている場合
    """
    valid_formats = ["Letter", "Legal", "A4", "A3", "A2", "A1", "A0"]
    if "format" in config and config["format"] not in valid_formats:
        raise ValueError(f"'format' must be one of {valid_formats}")

    if "timeout" in config and not isinstance(config["timeout"], int):
        raise ValueError("'timeout' must be an integer")

    if "timeout" in config and config["timeout"] <= 0:
        raise ValueError("'timeout' must be greater than 0")

    if "margin" in config and not isinstance(config["margin"], dict):
        raise ValueError("'margin' must be a dictionary")

    if "viewport" in config and not isinstance(config["viewport"], dict):
        raise ValueError("'viewport' must be a dictionary")

    if "viewport" in config:
        viewport = config["viewport"]
        for key in ["width", "height"]:
            if key in viewport and not isinstance(viewport[key], int):
                raise ValueError(f"'viewport.{key}' must be an integer")
            if key in viewport and viewport[key] <= 0:
                raise ValueError(f"'viewport.{key}' must be greater than 0")
