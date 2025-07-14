# site2 実装タスクリスト

## 概要

パイプライン全体を実装するためのタスクリストです。
各タスクは設計→テスト→実装の順で進めます。

## タスク一覧

### Phase 1: 基盤実装

- [x] [01. 設計ドキュメントの完成](todos/20250706-01-complete-design-docs.md)
- [x] [17. ドメインモデルのPydantic移行](todos/20250711-17-migrate-to-pydantic.md)
- [x] [18. ドメインイベントのテスト実装](todos/20250711-18-domain-events-test-task.md)
- [x] [19. 契約定義（Contracts）のPydantic移行](todos/20250712-19-migrate-contracts-to-pydantic.md)
- [x] [02. 共通インフラストラクチャの実装](todos/20250706-02-common-infrastructure.md)
- [ ] [20. パイプライン統合テストの実装](todos/20250713-20_pipeline_integration_test.md)
- [x] [21. パイプライン統合テストの修正とインターフェース設計の改善](todos/20250713-21_fix_pipeline_dataflow.md)
- [x] [22. インターフェース定義の統合と整理](todos/20250714-22_unify_interfaces.md)
- [ ] [03. Fetchサービスの実装](todos/20250706-03-implement-fetch-service.md)

### Phase 2: 検出機能の実装

- [ ] [04. HTMLパーサーの実装](todos/20250706-04-implement-html-parser.md)
- [ ] [05. Detect:Mainサービスの実装](todos/20250706-05-implement-detect-main.md)
- [ ] [06. Detect:Navサービスの実装](todos/20250706-06-implement-detect-nav.md)
- [ ] [07. Detect:Orderサービスの実装](todos/20250706-07-implement-detect-order.md)

### Phase 3: ビルド機能の実装

- [ ] [08. Markdownコンバーターの実装](todos/20250706-08-implement-markdown-converter.md)
- [ ] [09. PDFコンバーターの実装](todos/20250706-09-implement-pdf-converter.md)
- [ ] [10. Buildサービスの実装](todos/20250706-10-implement-build-service.md)

### Phase 4: 統合とCLI

- [ ] [11. Autoコマンドの実装](todos/20250706-11-implement-auto-command.md)
- [ ] [12. CLIとサービスの統合](todos/20250706-12-integrate-cli-services.md)
- [ ] [13. E2Eテストの実装](todos/20250706-13-implement-e2e-tests.md)

### Phase 5: 品質向上

- [ ] [14. エラーハンドリングの改善](todos/20250706-14-improve-error-handling.md)
- [ ] [15. パフォーマンス最適化](todos/20250706-15-performance-optimization.md)
- [ ] [16. ドキュメントの整備](todos/20250706-16-documentation.md)

## 進捗管理

各タスクの状態：
- [ ] 未着手
- [x] 完了
- [~] 作業中
- [!] ブロック中

## 注意事項

1. 各タスクは独立して実装可能なように設計
2. テストが先に存在することを確認してから実装
3. 契約（Protocol）に準拠した実装を行う
4. コードレビューを経てからマージ
