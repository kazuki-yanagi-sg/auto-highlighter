# fork agent と worktree の運用

fork が書き込み作業をするなら以下のパターンに乗せろ。worktree は `.claude/worktrees/<name>/` 配下に作る。

## パターン A: 親が worktree を作り fork に継承させる

- `git worktree add .claude/worktrees/<name> -b feature/<name> develop`
- `bash .claude/skills/setup-worktree/setup.sh "$(pwd)/.claude/worktrees/<name>"` で環境分離
- 同一セッションで `Agent`（isolation 指定なし）を呼ぶと fork は親の cwd を継承する
- 同じ worktree を複数 fork で触るな（並列度 1）

## パターン B: fork 自身が worktree を作る

- fork 内で `git worktree add .claude/worktrees/<name> -b feature/<name> develop`
- 直後に `setup-worktree` skill を呼べ（`.env` / docker stack / DB / port を一括 setup）
- fork 内で実装 → commit → push → PR まで完結
- 複数 fork を並列起動して独立タスクをこなす時に使う
