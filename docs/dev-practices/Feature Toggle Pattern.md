[TOD](/docs/TOC.md)

## フィーチャートグル (Feature Toggle) ガイド

このドキュメントは、私たちのチームが採用する開発プラクティスである\*\*フィーチャートグル（別名: フィーチャーフラグ）\*\*について、その目的、メリット、そして具体的な実装方法をまとめたものです。

### 1\. フィーチャートグルとは何か？

**フィーチャートグル**は、アプリケーションのソースコードに**特定の機能のON/OFFを切り替える**ための分岐ロジックを埋め込む開発テクニックです。

設定ファイルや管理画面からこの「トグル（スイッチ）」を操作することで、アプリケーションを再デプロイすることなく、リアルタイムで特定の機能の有効/無効を制御できます。

#### 🎯 目的とメリット

  * **デプロイとリリースの分離**: コードは本番環境にデプロイ済みでも、機能（フィーチャー）はOFFにしておき、任意のタイミングでONにしてユーザーに公開（リリース）できます。
  * **安全な機能展開**: 新しい機能をまず社内ユーザーや一部のユーザーだけに公開し、問題がないことを確認してから全ユーザーに展開する、といった段階的なリリース（カナリアリリース）が可能です。
  * **迅速なロールバック**: 本番で公開した新機能に問題が見つかった場合、トグルをOFFにするだけで、瞬時にその機能を無効化できます。
  * **A/Bテスト**: 同じ機能の異なるバージョン（AパターンとBパターン）を、ユーザーグループごとに見せ分けるA/Bテストが容易になります。
  * **トランクベース開発の実現**: 未完成の機能もトグルでOFFにしておくことで、安心して`main`ブランチにマージでき、継続的インテグレーションを促進します。

-----

### 2\. Pythonによる実装パターン

実装方法は、プロジェクトの要件に応じて、シンプルなものから高機能なものまで様々です。

#### パターン1: 環境変数や設定ファイルによるシンプルな制御

小規模な機能や、開発環境でのみ使用するトグルの場合に適しています。

##### Python実装例 (環境変数)

環境変数 `FEATURE_AI_SUMMARY` の値によって、AIによる要約機能のON/OFFを切り替えます。

```python
import os

def get_summary(article_text: str) -> str:
    """記事の要約を生成する"""

    # 環境変数をチェックして機能を切り替え
    # "FEATURE_AI_SUMMARY=true" のような環境変数を探す
    use_ai_summary = os.getenv("FEATURE_AI_SUMMARY", "false").lower() in ("true", "1")

    if use_ai_summary:
        print("INFO: AI要約機能を使用します。")
        # return AISummaryExtractor(article_text).extract() # AIによる要約
        return "【AIによる要約】..."
    else:
        print("INFO: 標準の要約機能を使用します。")
        # return StandardSummaryExtractor(article_text).extract() # 標準の要約
        return "【標準の要約】..."

# --- 使い方 ---
# 環境変数を設定せずに実行: FEATURE_AI_SUMMARY=false
get_summary("...") 
# > INFO: 標準の要約機能を使用します。

# 環境変数を設定して実行: FEATURE_AI_SUMMARY=true
get_summary("...") 
# > INFO: AI要約機能を使用します。
```

  * **長所**: シンプルで、追加ライブラリが不要です。
  * **短所**: ON/OFFを切り替えるには、アプリケーションの再起動や環境変数の再設定が必要で、動的な制御はできません。

-----

#### パターン2: 専用サービスによる高度な制御

本番環境での動的な機能管理や、パーセンテージでの段階的なリリースなど、高度な制御が必要な場合に適しています。**LaunchDarkly**や**Flagsmith**といった外部サービスと、そのSDKを利用するのが一般的です。

##### Python実装例 (Flagsmith SDK)

管理画面からリアルタイムでON/OFFでき、特定のユーザーだけに機能を有効化します。

**1. ライブラリのインストール:**

```bash
pip install flagsmith
```

**2. コードの実装:**

```python
from flagsmith import Flagsmith

# サービスの環境キーでSDKを初期化
flagsmith = Flagsmith(environment_key="ser.your_environment_key_here")

def get_ai_powered_search_results(query: str, user_id: str):
    """
    AIによる検索機能が有効なユーザーかどうかを判定し、結果を返す
    """
    
    # ユーザー情報を識別子として渡す
    identity_flags = flagsmith.get_identity_flags(identifier=user_id)

    # "ai_powered_search" という名前のフラグが、このユーザーに対してONかチェック
    if identity_flags.is_feature_enabled("ai_powered_search"):
        print(f"INFO: ユーザー({user_id})はAI検索が有効です。")
        # return AI_search(query)
        return {"source": "AI", "results": [...]}
    else:
        print(f"INFO: ユーザー({user_id})は標準検索が有効です。")
        # return standard_search(query)
        return {"source": "Standard", "results": [...]}

# --- 使い方 ---
# user_aは管理画面でAI検索がONに設定されている
get_ai_powered_search_results("python", user_id="user_a")
# > INFO: ユーザー(user_a)はAI検索が有効です。

# user_bはOFFに設定されている
get_ai_powered_search_results("python", user_id="user_b")
# > INFO: ユーザー(user_b)は標準検索が有効です。
```

  * **長所**: 再デプロイ不要でリアルタイムなON/OFFが可能。ユーザー単位での制御や段階的リリースなど、柔軟な機能管理ができます。
  * **短所**: 外部サービスへの依存が発生します。

### まとめ

フィーチャートグルは、現代の迅速で安全なソフトウェア開発に不可欠なテクニックです。シンプルな機能には環境変数、本番環境での柔軟な機能管理には専用サービス、というように目的に応じて適切な実装パターンを選択し、開発サイクルを高速化していきましょう。
