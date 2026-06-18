# developの最新をmerge

PR作成後、現在のブランチにdevelopの最新をmergeします。

## 目的

- PR作成後、developに追加された変更を取り込む
- コンフリクトを早期に発見・解決する
- CI/CDでのテスト失敗を防ぐ

## 使用方法

```
/git:merge-develop
```

## 実行フロー

### 1. 事前チェック

**未コミット変更の確認**:
```bash
git status --porcelain
```

- 未コミットの変更がある場合:
  - ユーザーに通知
  - commit/stash/discardの選択肢を提示
  - ユーザーの判断を待つ

**現在のブランチ確認**:
```bash
git branch --show-current
```

- developブランチの場合:
  - エラー: "developブランチでは実行できません"
  - 別のブランチに切り替えるよう案内

### 2. developの最新を取得

```bash
git fetch origin develop
```

- fetch成功: 次のステップへ
- fetch失敗: エラーメッセージを表示し中断

### 3. mergeの実行

```bash
git merge origin/develop --no-edit
```

- merge成功: 自動でステップ4へ
- コンフリクト発生: 以下を実行
  1. コンフリクトファイル一覧を表示
  2. 解決方法を丁寧に案内:
     ```
     コンフリクトが発生しました。以下のファイルを確認してください：
     - path/to/conflicted/file1
     - path/to/conflicted/file2

     【解決手順】
     1. VS Codeなどでコンフリクトマーカーを確認
     2. 必要な変更を選択・編集
     3. `git add <解決したファイル>` で変更をステージング
     4. `git commit` でmerge commitを完了
     5. 再度このコマンドを実行してpush確認へ
     ```
  3. 処理を一時中断（ユーザーの手動解決を待つ）

### 4. push確認

merge成功後、ユーザーに確認:

```
developの最新がmergeされました。
リモートにpushしますか？ (y/n)
```

- `y` の場合: `git push origin <current-branch>`を実行
- `n` の場合: ローカルのみで完了（ユーザーが後で手動push可能）

### 5. 完了報告

```
✅ developの最新をmergeしました
✅ リモートにpushしました

【次のステップ】
- PRページでCI/CDの実行結果を確認
- コンフリクトが解決されているか確認
- レビュアーに最新状態を通知
```

## エラーハンドリング

### fetch失敗

```
❌ developブランチの取得に失敗しました

【原因】
- ネットワークエラー
- リモートリポジトリへのアクセス権限がない
- origin/developブランチが存在しない

【対処法】
1. ネットワーク接続を確認
2. `git remote -v` でリモート設定を確認
3. 手動で `git fetch origin develop` を実行して詳細を確認
```

### merge失敗（コンフリクト以外）

```
❌ mergeに失敗しました

【原因】
- 予期しないGitエラー
- ローカルリポジトリの状態が不正

【対処法】
1. `git status` で現在の状態を確認
2. 必要に応じて `git merge --abort` で中断
3. 手動で対処するか、チームに相談
```

### push失敗

```
❌ リモートへのpushに失敗しました

【原因】
- リモートブランチが先に進んでいる
- push権限がない

【対処法】
1. `git pull --rebase origin <branch>` で最新を取得
2. 再度pushを試行
3. 権限エラーの場合はリポジトリ管理者に確認
```

## 注意事項

- **developブランチでは実行不可**: 誤操作を防ぐため
- **未コミット変更がある場合**: 事前にcommitまたはstashを推奨
- **コンフリクト解決は手動**: 自動マージは危険なため、ユーザー判断を尊重
- **CI/CD確認必須**: merge後は必ずCIの実行結果を確認

## ベストプラクティス

1. **定期的なmerge**: developが大きく進む前に頻繁にmerge
2. **小さな変更**: PRのスコープを小さく保つとコンフリクトが減る
3. **レビュー前のmerge**: レビュー依頼前に最新のdevelopをmerge
4. **テスト実行**: merge後は必ずローカルでテストを実行

## カスタムコマンド共通仕様

@.claude/lib/common.md
