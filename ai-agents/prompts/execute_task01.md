# タスク01 実行プロンプト

以下の内容をAIエージェントにコピー＆ペーストして実行を開始してください。

---

# タスク実行指示

## 役割設定
あなたはCommander（統括者）として、以下のタスクを管理してください。
必要に応じてWorker（作業者）の役割に切り替えて実装を行ってください。

## 実行するタスク
タスク01: 設計ドキュメントの完成
ai-agents/todos/20250706-01-complete-design-docs.md

## プロジェクト情報
- リポジトリ: https://github.com/boarnasia/site2
- ブランチ: 20250706-01-initial-work
- コンテキスト: AI_CODING_CONTEXT.md
- 参考: docs/design/pipeline_design.md

## 実行手順
1. タスクファイル（20250706-01-complete-design-docs.md）を読み込んで内容を理解
2. 既存の契約定義ファイルを確認：
   - src/site2/core/ports/fetch_contracts.py
   - src/site2/core/domain/fetch_domain.py
3. 不足している契約定義を特定
4. 実装計画を立案してCommanderとして報告
5. Workerとして各契約定義ファイルを作成
6. 作成したファイルの内容を検証
7. 完了報告を作成

## 具体的な成果物
以下のファイルを作成してください：

1. `src/site2/core/ports/detect_contracts.py`
   - DetectMainRequest/Result
   - DetectNavRequest/Result
   - DetectOrderRequest/Result
   - DetectServiceProtocol

2. `src/site2/core/ports/build_contracts.py`
   - BuildRequest/Result
   - BuildServiceProtocol
   - OutputFormat enum

3. `src/site2/core/ports/pipeline_contracts.py`
   - PipelineServiceProtocol
   - 統合用のデータ型

4. `src/site2/core/domain/detect_domain.py`（必要に応じて）
   - SelectorCandidate
   - NavLink
   - OrderedFile

5. `src/site2/core/domain/build_domain.py`（必要に応じて）
   - ExtractedContent
   - CombinedDocument

## 制約事項
- Clean Architectureの原則に従う
- すべてのProtocolにdocstringで事前条件・事後条件を記載
- 型ヒントを完全に付ける
- 既存のfetch_contracts.pyのスタイルに合わせる
- エラークラスも定義する

## 品質チェックリスト
- [ ] すべての契約に型ヒントがある
- [ ] docstringに事前条件・事後条件が明記されている
- [ ] validate()メソッドが実装されている（DTO）
- [ ] エラーケースが定義されている
- [ ] インポートが整理されている

開始してください。まず、Commanderとして現状を分析し、実装計画を提示してください。
