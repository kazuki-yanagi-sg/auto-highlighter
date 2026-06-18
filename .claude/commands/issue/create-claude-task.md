---
allowed-tools: [Bash, Write, Read, Glob, MultiEdit]
description: claude-todosルールに基づいてタスクを体系的に管理
---

# タスク作成と管理

claude-todosディレクトリにTDDベースのタスク管理ファイルを作成・管理します。

## 引数の処理

引数: $ARGUMENTS

- 引数指定時: 引数で渡された要求を分析してタスクを作成
- 引数未指定時: 現在の会話コンテキストから依頼内容を分析してタスク作成

## 実行フロー

### フェーズ1: 構造分析とTree計画PR作成

1. **プロジェクト構造分析**: `tree`コマンドでプロジェクトの現在のディレクトリ構成を分析
   - `api/src/`配下の構造（models, routers, schemas, services等）
   - `client/src/components/`配下の構造（atoms, molecules, organisms, substances等）
   - 既存のファイル・ディレクトリのパターンを把握

2. **既存実装の参照**: 参考にする既存の実装ファイル（model/router/schema/component等）を確認
   - 分析した構造から適切な参考元ファイルを特定
   - 参考元ファイルの命名規則・配置パターンを確認

3. **構造テンプレート参照と必要に応じた修正**: 新規機能実装の場合、構造設計に活用
   - Frontend機能: `claude-todos/00_9010_frontend_structure_template.xml`を参照
   - Backend機能: `claude-todos/00_9020_backend_structure_template.xml`を参照
   - **テンプレートに不足や改善が必要な場合は、必ずステップ4で修正PRを作成する**

4. **構造テンプレート修正PR作成**（9010/9020に修正が必要な場合のみ）:
   - developブランチから`docs/update-structure-templates`ブランチを作成
   - 00_9010および00_9020を修正（不足している構造パターンを追加）
   - **重要**: 新規追加する構造には必ず`← new (参考元: xxx)`マーカーを追加
     - 例: `└── thread.tsx              ← new (参考元: ticket.tsx)`
   - 修正内容をコミット（例: `docs: 構造テンプレートを更新（チャット機能対応）`）
   - PRを作成してブラウザで開く（`gh pr view --web`）
   - **このPRがマージされるまで次のステップには進まない**

5. **XMLファイル作成**（構造テンプレートPRマージ後）: `claude-todos/00_9000_tree_plan_template.xml`をコピーして`XX_9000_tree_plan.xml`を作成
   - developブランチを最新化してから作業開始（`git checkout develop && git pull`）
   - テンプレートに従って依頼概要、想定タスク分割数、Tree構造を記載
   - 実際のプロジェクト構造に基づいてTree構造を作成（推測禁止）
   - 参考元ファイルと新規作成ファイルを区別して記載
   - 更新済みの9010/9020テンプレートを反映

6. **フェーズ1+2統合ブランチ作成**:
   - developブランチから`feature/claude-tasks-[依頼名]`ブランチを作成
   - `XX_9000_tree_plan.xml`をgit addでステージング
   - コミット（例: `docs: チャット機能のTree計画（01_9000）を作成`）
   - **フェーズ1のみのPRは作成せず、そのままフェーズ2に進む**

### フェーズ2: タスクファイル作成（フェーズ1と同じブランチで継続）

**重要**: フェーズ1で承認を得たXMLファイル（`XX_9000_tree_plan.xml`）のディレクトリ構成を基にタスクを作成する

1. **ルール確認**: claude-todos/README.md、00_0000_overview_template.xml、00_0010_task_template.xml、00_9999_task_instruction_template.xmlを全て読み込み
2. **現状確認**: claude-todosディレクトリの既存ファイルを確認し、次の依頼IDを決定
3. **XMLファイル参照**: `claude-todos/XX_9000_tree_plan.xml`を参照し、以下を確認:
   - 依頼概要（何を実装するか）
   - 想定タスク分割数（全体を何枚に分けるか）
   - Tree構造（どのファイルを作成するか、参考元は何か）
4. **依頼分析**: XMLファイルの内容に基づき、ゴールと成功条件を明確化
5. **TDD分解**: XMLファイルで計画したタスク分割数を踏まえ、テスト可能な単位でタスクを分割（振る舞い単位）
6. **ファイル生成**: 全体像ファイル（XX_0000）と個別タスクファイル（XX_0010〜）を作成
   - XX_0000ファイル内にTree構成への参照を記載: `詳細なファイル配置計画はXX_9000_tree_plan.xmlを参照`
7. **タスクマップ作成**: 依存関係を考慮した実行順序を設計
8. **指示書準備**: 00_9999_task_instruction_template.xmlをXX_9999_task_instruction.xmlとしてコピー
9. **指示書変数更新**: コピーした指示書ファイル内の以下の変数を必ず更新
   - `$TREE_PLAN`: `claude-todos/XX_9000_tree_plan.xml` → 作成したTree計画ファイル
   - `$OVERVIEW`: `claude-todos/XX_0000_[依頼名].xml` → 作成した全体像ファイル
   - `$CURRENT_TASK`: `claude-todos/XX_0010_[タスク名].xml` → 最初のタスクファイル
   - `$THIS_FILE`: `claude-todos/XX_9999_task_instruction.xml` → 指示書ファイル自身
10. **親ブランチ作成と指示**: 複数タスクを統合するための親ブランチを作成
    - **親ブランチ名をXX_0000ファイルに明記する**（例: `親ブランチ: feature/chat-function`）
    - **各タスク（XX_0010〜）にマージ対象の親ブランチ名を明記する**
    - developブランチから親ブランチを作成するコマンドを記載:

      ```bash
      git checkout develop
      git pull origin develop
      git checkout -b feature/chat-function
      git push -u origin feature/chat-function
      ```

    - ブランチ命名規則:
      - 親ブランチ: `feature/[機能名]`（例: `feature/chat-function`）
      - 子ブランチ: `feature/[機能名]-[タスク名]`（例: `feature/chat-function-models`）
11. **Git操作とPR作成**: タスクファイル作成完了後の手順
    - **フェーズ1と同じブランチで継続**: `feature/claude-tasks-[依頼名]`ブランチで作業
    - 作成したタスクファイル（XX_0000、XX_0010〜、XX_9999）をgit addでステージング
    - コミット（例: `docs: [依頼名]のタスクファイル作成（フェーズ2）`）
    - PR作成（フェーズ1+2統合PR、タイトル例: `docs: [依頼名]のタスク管理ファイル作成（フェーズ1+2統合）`）
    - ブラウザでPRを開く（`gh pr view --web`）
    - **このPRがマージされた後、実装フェーズに移行**

### フェーズ3: 実装フェーズ（タスク実行）

1. **親ブランチから作業開始**
   - XX_0000ファイルに記載された親ブランチに切り替え

   ```bash
   git checkout feature/chat-function  # XX_0000に記載された親ブランチ名
   git pull origin feature/chat-function
   ```

2. **各タスクの実装**（XX_0010, XX_0020...の順に実施）
   - **タスクファイル（XX_0010等）に記載された情報を確認**:
     - マージ対象の親ブランチ名（例: `feature/chat-function`）
     - 作業用の子ブランチ名（例: `feature/chat-function-models`）
   - 親ブランチから子ブランチを作成:

   ```bash
   git checkout feature/chat-function  # 親ブランチ（タスクファイルに記載）
   git pull origin feature/chat-function
   git checkout -b feature/chat-function-models  # 子ブランチ（タスクファイルに記載）
   ```

   - タスクを実装
   - 完了後、子ブランチを親ブランチへマージ:

   ```bash
   git push -u origin feature/chat-function-models
   gh pr create --base feature/chat-function --head feature/chat-function-models
   # PRレビュー後、親ブランチへマージ
   ```

   - 次のタスクは再度親ブランチから新しい子ブランチを作成

3. **全タスク完了後**
   - 親ブランチをdevelopにマージするPRを作成:

   ```bash
   git checkout feature/chat-function
   git pull origin feature/chat-function
   gh pr create --base develop --head feature/chat-function
   ```

   - 機能全体のレビューを受ける
   - マージ後、親ブランチと全ての子ブランチを削除

## 使用方法

- `/issue:create-claude-task` - 現在の会話から自動的にタスクを作成
- `/issue:create-claude-task "ユーザー管理機能"` - 指定した依頼名でタスク作成
- `/issue:create-claude-task "パフォーマンス改善 --tdd"` - TDD重視でタスク分解

## 注意事項

⚠️ **必須確認事項**:
- **構造テンプレート更新PR**: 9010/9020/9000に修正が必要な場合、フェーズ1の最初（ステップ1）で必ずPR作成
- **PRで語る**: ユーザーに「話を伺う」のではなく、PRを作成して具体的な変更内容を提示する
- **プロジェクト構造分析**: フェーズ1で必ず`tree`コマンドで現行のディレクトリ構成を分析
- **XMLファイル作成**: Tree構造は必ず`claude-todos/XX_9000_tree_plan.xml`に記載
- **ファイル命名規則**: Tree計画ファイルは9000系（XX_9000〜）を使用し、指示書（XX_9999）との間に配置
- **タスク分割計画**: XMLファイルに想定タスク分割数と各タスクの概要を明記
- **親ブランチ作成**: 複数タスクがある場合、必ず親ブランチを作成してから各タスクに取り組む
- **ブランチ戦略**: 各タスクは親ブランチから子ブランチを作成し、完了後に親ブランチへマージ
- claude-todos/README.mdの運用ルールに完全準拠
- テンプレートファイル（00_0000, 00_0010, 00_9999）は絶対に変更しない
- XX_9000_tree_plan.xmlは全てのタスク完了後も保持（実装の参考資料として）

## カスタムコマンド共通仕様

@.claude/lib/common.md
