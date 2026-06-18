# 特殊ケース

## 質問対応

- 推測禁止、WebSearch / 実コード確認で裏取り
- 実際にテスト実行して確認
- 検証プロセス: 現状確認 → 仮説 → 実証 → 反証 → 結論

## 作業完了時

```bash
sh project_check.sh -cl              # client lint
sh project_check.sh -al              # api lint
cd api && uv run pytest              # api test
git status
```

## 特殊プレフィックス

- **-q**: 質問のみ（コード修正なし）
- **-s**: セルフレビュー・リファクタ
- **-w**: PR をブラウザで開く

## biome.json / eslint.config.* 変更

- 必ずユーザーに相談
- linter ルール変更時
- オーバーライド設定変更時
