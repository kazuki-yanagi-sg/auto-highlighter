---
allowed-tools: [Bash, Read]
description: カスタムコマンドの使用統計を表示する
---

# カスタムコマンド使用統計

カスタムコマンドの使用統計を表示します。

## 実行

統計情報を表示:

```bash
.claude/scripts/show-stats.sh
```

## 出力内容

- 総実行回数
- コマンド別使用回数
- 初回使用・最終使用日時
- TOP 5 最頻使用コマンド

## カスタムコマンド共通仕様

@.claude/lib/common.md
