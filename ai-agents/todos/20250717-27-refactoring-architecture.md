Task 27: DetectService アーキテクチャの改善とMainContentDetectorの分離

目的

クリーンアーキテクチャの原則に従い、MainContentDetectorを適切な層に配置し、DetectServ
iceの依存性注入を改善する。将来的なAI検出手法（Gemini等）への拡張性を確保する。

背景

現在の実装では以下の問題がある：
1. MainContentDetectorがcore/servicesに配置されている（アーキテクチャ違反）
2. DetectServiceでMainContentDetectorがハードコード（拡張性欠如）
3. AI検出手法への切り替えが困難

実装計画

1. Protocol定義の作成

src/site2/core/ports/detector_contracts.py
- MainContentDetectorProtocolを定義
- DetectionResult、DetectionCandidateなどのDTOを定義
- 複数の検出手法に対応できるインターフェース

2. アダプター層への実装移動

src/site2/adapters/detectors/
├── __init__.py
├── heuristic_detector.py      # 現在のMainContentDetector
├── base_detector.py           # 共通基底クラス
└── (将来) gemini_detector.py  # AI検出実装用

3. DetectServiceの依存性注入改善

- MainContentDetectorを外部から注入可能に変更
- コンストラクタにMainContentDetectorProtocolを追加
- 既存のロジックは維持

4. Container設定の更新

- main_content_detector プロバイダーを追加
- DetectServiceの依存関係を更新
- 設定による検出手法の切り替え準備

5. テストの更新

- 新しいアーキテクチャに対応
- プロトコルベースのモッキング
- アダプター層のテスト追加

6. 不要ファイルの削除

- src/site2/core/services/main_content_detector.pyを削除
- 対応するテストファイルの移動

実装ステップ

1. detector_contracts.py作成 - プロトコル定義
2. adapters/detectors/実装 - HeuristicDetectorクラス作成
3. DetectService修正 - 依存性注入対応
4. Container更新 - DI設定変更
5. テスト移動・更新 - 新アーキテクチャ対応
6. 旧ファイル削除 - クリーンアップ

期待される成果

- クリーンアーキテクチャ準拠
- AI検出手法への拡張容易性
- 設定による検出手法切り替え
- テストの保守性向上

推定工数: 2-3時間
