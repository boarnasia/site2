# Task 27 レビュー修正レポート

## 概要
クリーンアーキテクチャの原則に基づき、DetectService実装における4つの重要な問題を特定・修正しました。

## 修正内容

### 1. 機能重複の解消
**問題**:
- `src/site2/core/ports/detector_contracts.py`
- `src/site2/core/ports/detect_contracts.py`

同じ機能（MainContentDetectorProtocol）が2つのファイルに重複実装されていました。

**修正**:
- `detector_contracts.py`の機能を`detect_contracts.py`に統合
- `detector_contracts.py`を削除して一元化を実現
- インポート文を修正して統一されたコントラクトを参照

**効果**: Single Responsibility Principleの遵守、保守性の向上

### 2. ドメインとポートの分離
**問題**:
`src/site2/core/ports/detect_contracts.py`内で以下のドメインモデルが重複定義されていました：
- `SelectorCandidate`
- `NavLink`
- `OrderedFile`

**修正**:
- Ports層から重複するドメインモデルを削除
- `src/site2/core/domain/detect_domain.py`からのインポートに変更
- レイヤー間の責任を明確に分離

**効果**: Clean Architectureの依存関係ルール遵守、ドメインロジックの一元化

### 3. DIコンテナの依存関係修正
**問題**:
`Container`が`HeuristicMainContentDetector`を直接参照していました。

**修正**:
- `DetectorFactory.create`メソッドを使用した間接参照に変更
- 実装の詳細をAdapters層に隠蔽
- 将来的なAI検出器実装への拡張性を確保

**変更前**:
```python
main_content_detector = providers.Factory(HeuristicMainContentDetector, ...)
```

**変更後**:
```python
main_content_detector = providers.Factory(
    DetectorFactory.create,
    method="heuristic",
    html_analyzer=html_analyzer,
    options=providers.Dict(...)
)
```

**効果**: Dependency Inversion Principleの適用、拡張性の向上

### 4. プロトコル継承の明示化
**問題**:
`HeuristicMainContentDetector`が`MainContentDetectorProtocol`を明示的に継承していませんでした。

**修正**:
```python
class HeuristicMainContentDetector(MainContentDetectorProtocol):
```

**検証**:
- メソッドシグネチャの完全な一致を確認
- テスト実行による動作確認（13/13 passed）
- DIコンテナでの正常な依存注入を確認

**効果**: 型安全性の向上、Liskov Substitution Principleの遵守

## テスト結果
- HeuristicMainContentDetectorテスト: 13/13 通過
- Containersテスト: 10/10 通過
- detect関連テスト: 25/26 通過（1つの失敗は外部リンク判定の問題で今回の修正とは無関係）

## アーキテクチャへの影響
この修正により、以下のクリーンアーキテクチャ原則が適切に適用されました：

1. **依存性逆転原則（DIP）**: Use Case層がAdapter層の抽象に依存
2. **単一責任原則（SRP）**: 各コンポーネントが明確な責任を持つ
3. **開放閉鎖原則（OCP）**: 新しい検出器実装への拡張が容易
4. **リスコフ置換原則（LSP）**: プロトコル実装の置換可能性を保証

## 今後の展望
- AI検出器（Gemini API）実装時の拡張が容易
- ハイブリッド検出器の実装も同様のパターンで可能
- 型安全性と保守性が大幅に向上
