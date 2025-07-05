# 技術スタック

python3.12, rye

pyproject.toml に使用するパッケージを記述しています

# Commands
- rye run site2 --help
- rye run python
- rye run ipython
- rye run pytest tests
- rye run pre-commit run --all-files

# Agent 言語使用ルール

## 🎯 言語使用の原則

**Commander / Worker 共通:**

### 日本語を使用する場面
- ユーザーへのコミュニケーション
  - プログレスレポート
  - エラー報告
  - 完了通知
  - 質問や確認
  - 進捗状況の説明
- ユーザーもよむドキュメント
  - 技術仕様書・ドキュメント作成
  - コード・コメント・関数名
  - システム設計・技術解析

### 英語を使用する場面
- Agent 間のやり取り
  - Agent内部の思考プロセス
  - Agent間のタスクファイル・通信
  - API通信・プロンプトエンジニアリング

## 📝 実装ガイドライン

### ファイル作成時の言語選択
```
ai-agents/tasks/        → Japanese
ai-agents/reports/      → English (Agent間通信) + Japanese summary for user
ai-agents/bootprompts/  → Mixed (Instructions in Japanese, rules in English)
ai-agents/roles/        → Mixed (Description in Japanese, technical rules in English)
src/                    → Japanese (Code)
tests/                  → Japanese (Code)
examples/               → Japanese (Code)
docs/                   → Context-dependent (user-facing: Japanese, technical: English)
```

### レポート構造例
```markdown
# Technical Implementation Report (English)
[Detailed technical content in English]

## ユーザー向けサマリー (Japanese)
[User-friendly summary in Japanese]
```

### Bootprompt構造例
```markdown
あなたは [role_name] です。

**Language Rules (IMPORTANT):**
- Internal thinking: English
- User communication: Japanese (日本語)
- Technical files: Japanese
- Code comments: Japanese

[Additional instructions in Japanese]
```

## 💡 コミュニケーション最適化

1. **思考の効率性**: 英語での思考によりAgent性能を最大化
2. **ユーザビリティ**: 日本語報告によりユーザー理解を向上
3. **国際標準**: 技術文書は英語で作成し再利用性を確保
4. **一貫性**: 全Agentが同じ言語ルールを適用
5. **効率性**: 内部処理は英語、外部報告は日本語で明確に分離

# その他の重要事項

- ツール名は古い名残で site2pdf ですが最終的な出力目標は markdown に変更されているので、ツール名に引きずられないでください
- gemini api を使用するときはオーダー数が増えすぎないように最適化を行ってください
- 各Agentは必ず ai-agents/common.md を最初に読み込んでルールを確認してください
