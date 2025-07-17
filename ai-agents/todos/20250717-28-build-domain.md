# Task 28: Build契約のドメイン分離修正

## 概要
build_contracts.pyにおいて、ドメインモデルがPorts層に定義されているクリーンアーキテクチャ違反を修正する。

## 背景
Task27のレビューで発覚した問題と同様に、build_contracts.pyでもドメインとポートの分離が適切に行われていない。これはクリーンアーキテクチャの原則に違反し、レイヤー間の責任を曖昧にしている。

## 問題点
1. **ドメインモデルの誤配置**
   - OutputFormat (Enum)
   - ExtractedContent (BaseModel)
   - 各種エラークラス（BuildError, ConvertError等）
   これらがports層に定義されている

2. **循環インポートの回避策**
   - TYPE_CHECKINGを使用した循環インポート回避
   - 設計上の問題を示唆

## 修正内容

### 1. ドメインモデルファイルの作成
`src/site2/core/domain/build_domain.py`を作成し、以下を移動：
- OutputFormat (Enum)
- ExtractedContent (Pydantic BaseModel)
- BuildError及びその派生エラークラス

### 2. build_contracts.pyの修正
以下のみを残す：
- DTOs: BuildRequest, BuildResult, ConvertRequest, ConvertResult等
- Protocols: BuildServiceProtocol, MarkdownConverterProtocol, PDFConverterProtocol

### 3. インポートの修正
- build_domain.pyからドメインモデルをインポート
- TYPE_CHECKINGブロックを削除
- 依存関係を内側に向ける

## 期待される効果
- レイヤー間の責任が明確化
- 循環インポートのリスク排除
- Single Responsibility Principleの遵守

## 実装手順
1. build_domain.pyを作成
2. ドメインモデルを移動
3. build_contracts.pyからドメインモデルを削除
4. インポート文を修正
5. テスト実行で動作確認

## 関連ファイル
- src/site2/core/domain/build_domain.py (新規作成)
- src/site2/core/ports/build_contracts.py (修正)
- 関連するテストファイル

## 完了条件
- [ ] build_domain.pyが作成され、ドメインモデルが配置されている
- [ ] build_contracts.pyにはDTOとProtocolのみが残っている
- [ ] TYPE_CHECKINGによる循環インポート回避が削除されている
- [ ] すべてのテストが通過する
- [ ] インポートエラーが発生しない
