"""
Markdownifyの設定
"""

from typing import Dict, Any

# デフォルトのMarkdownify設定
DEFAULT_MARKDOWNIFY_CONFIG: Dict[str, Any] = {
    # 変換対象のタグのみ指定（stripとconvertは同時に使用不可）
    "convert": [
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",  # 見出し
        "p",
        "div",
        "span",  # テキスト要素
        "a",  # リンク
        "strong",
        "b",
        "em",
        "i",  # 強調
        "ul",
        "ol",
        "li",  # リスト
        "blockquote",  # 引用
        "code",
        "pre",  # コード
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",  # テーブル
        "img",  # 画像
        "hr",  # 水平線
        "br",  # 改行
    ],
    # 自動リンク変換
    "autolinks": True,
    # 見出しのスタイル（ATX: #形式、SETEXT: アンダーライン形式）
    "heading_style": "ATX",
    # コードブロックのデフォルト言語
    "default_title": True,
    # エスケープ文字の処理
    "escape_misc": False,
    # テキストの折り返し
    "wrap": True,
    "wrap_width": 80,
    # Markdownの拡張機能
    "bullets": "-",  # リストのマーカー
    "emphasis_mark": "*",  # 強調のマーカー
    "strong_mark": "**",  # 太字のマーカー
}

# 軽量版設定（最小限の変換のみ）
LIGHTWEIGHT_MARKDOWNIFY_CONFIG: Dict[str, Any] = {
    "convert": ["h1", "h2", "h3", "h4", "h5", "h6", "p", "a", "strong", "em"],
    "autolinks": True,
    "heading_style": "ATX",
    "escape_misc": False,
    "wrap": False,
}

# 詳細版設定（すべての要素を変換）
COMPREHENSIVE_MARKDOWNIFY_CONFIG: Dict[str, Any] = {
    **DEFAULT_MARKDOWNIFY_CONFIG,
    "convert": [
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "p",
        "div",
        "span",
        "section",
        "article",
        "a",
        "strong",
        "b",
        "em",
        "i",
        "u",
        "s",
        "mark",
        "ul",
        "ol",
        "li",
        "dl",
        "dt",
        "dd",
        "blockquote",
        "q",
        "cite",
        "code",
        "pre",
        "kbd",
        "samp",
        "var",
        "table",
        "thead",
        "tbody",
        "tfoot",
        "tr",
        "th",
        "td",
        "caption",
        "img",
        "figure",
        "figcaption",
        "hr",
        "br",
        "wbr",
        "sub",
        "sup",
        "small",
        "big",
        "abbr",
        "acronym",
        "address",
        "time",
    ],
    "wrap_width": 100,
}


def get_config_by_name(config_name: str) -> Dict[str, Any]:
    """
    設定名から設定を取得

    Args:
        config_name: 設定名 ("default", "lightweight", "comprehensive")

    Returns:
        Dict[str, Any]: Markdownify設定

    Raises:
        ValueError: 不正な設定名が指定された場合
    """
    configs = {
        "default": DEFAULT_MARKDOWNIFY_CONFIG,
        "lightweight": LIGHTWEIGHT_MARKDOWNIFY_CONFIG,
        "comprehensive": COMPREHENSIVE_MARKDOWNIFY_CONFIG,
    }

    if config_name not in configs:
        available_configs = ", ".join(configs.keys())
        raise ValueError(
            f"Unknown config name: {config_name}. Available: {available_configs}"
        )

    return configs[config_name].copy()


def merge_config(
    base_config: Dict[str, Any], custom_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    設定をマージ

    Args:
        base_config: ベース設定
        custom_config: カスタム設定

    Returns:
        Dict[str, Any]: マージされた設定
    """
    merged = base_config.copy()
    merged.update(custom_config)
    return merged


def validate_config(config: Dict[str, Any]) -> None:
    """
    設定の妥当性を検証

    Args:
        config: 検証する設定

    Raises:
        ValueError: 不正な設定値が含まれている場合
    """
    if "convert" in config and not isinstance(config["convert"], list):
        raise ValueError("'convert' must be a list of tag names")

    if "heading_style" in config and config["heading_style"] not in ["ATX", "SETEXT"]:
        raise ValueError("'heading_style' must be 'ATX' or 'SETEXT'")

    if "wrap_width" in config and not isinstance(config["wrap_width"], int):
        raise ValueError("'wrap_width' must be an integer")

    if "wrap_width" in config and config["wrap_width"] <= 0:
        raise ValueError("'wrap_width' must be greater than 0")
