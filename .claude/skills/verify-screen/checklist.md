# verify-screen 観点チェックリスト

`verify-screen` skill が動作確認時に評価する 3 観点 (CRUD / レイアウト / 既存画面整合性)。skill 本体 (`SKILL.md`) から Read で取り込み、`template.html` の各観点セクションに評価結果を書き込む。

各観点は **項目 / 期待結果 / failure 検出条件** の 3 つ組で書け。レビュー時に「何をチェックすれば終わりか」を一意に決められる粒度に保て。

## §1 CRUD 観点

確認対象画面が CRUD を含む場合、以下 5 操作を**業務シナリオの順 (一覧 → 作成 → 参照 → 更新 → 削除) で全て実施しろ**。一覧で登録データが見えるところまで到達して初めて「CRUD 確認 OK」とせよ。

| # | 項目 | 期待結果 | failure 検出条件 |
|---|---|---|---|
| 1 | 一覧表示 | 一覧画面が初期 row + paging / sort / loading 完了状態で表示される | 一覧 fetch が 4xx-5xx / loading が永遠 / 空状態が出ない / row 値が空文字 |
| 2 | 登録 | 新規 form 送信後、dialog が閉じ、一覧 row が 1 件増えて登録値が表示される | `playwright-cli console` に error / `playwright-cli requests` に 4xx-5xx / dialog が閉じない / row が増えない |
| 3 | 詳細参照 | 登録 row を click → 詳細に遷移し登録値が読み出せる | network 4xx-5xx / 詳細が空 / 404 / loading のまま固まる |
| 4 | 更新 | 編集 form 送信後、編集値が一覧 row / 詳細に反映される | network 4xx-5xx / 表示値が編集前のまま / optimistic update が rollback |
| 5 | 削除 | 削除確認後、一覧から該当 row が消える (soft delete 仕様なら一覧 filter が未削除のみ) | network 4xx-5xx / row が残る / 「削除しました」表示後 reload で復活 |

各操作で `playwright-cli screenshot` を **節目ごとに複数枚** 取得し、ファイル名は `screenshots/<YYYYMMDDHHMMSS>-<NN>-<phase-slug>.png` (時系列ソート可能) に統一しろ。

## §2 レイアウト観点

「美しさ / 整い / 使いやすさ」を機械寄りの観点に落とせ。`playwright-cli snapshot` の dom 検査 + 目視 (キャプチャ) の両輪で評価しろ。

### screenshot 目視判定の手順 (必須)

machine snapshot (`playwright-cli snapshot` の YAML) だけでは **要素の重なり / clipping** を検出できない。snapshot は DOM 階層と aria しか見えないため、視覚的衝突は素通りする。screenshot を Read tool で **agent 自身が開いて目視判定する手順を必ず通せ**。

- 各シナリオで `playwright-cli screenshot` を取った直後、同じ PNG を `Read` tool で開け
- 開いた画像を以下 5 観点で目視判定し、異常があれば FAIL として report に明記しろ
  - **重なり (overlap)**: 異なる column / 隣接要素が物理的に重なる (checkbox と label / icon と文字 / 2 列 grid の右列が左列に侵入 等)
  - **clipping**: 要素が親 container からはみ出す / 切れて読めない
  - **領域はみ出し**: pane / card / dialog の境界線を子要素が突き抜ける
  - **折り返し破綻**: 想定外の多段折り返し / 半端な位置で改行
  - **操作要素の隠蔽**: button / checkbox が他要素の下に隠れる / click 不可領域に置かれる
- 「機能 (click / state) が正常 = レイアウト PASS」と判定するな (機能 PASS + レイアウト FAIL は両立する)

| 項目 | 期待結果 | failure 検出条件 |
|---|---|---|
| 余白 | section / card / table cell の padding と margin が一貫 | 隣接要素が密着 / 異常に空きすぎ / 同階層 card で padding がバラつく |
| 列幅 | table の column 幅が内容に対して適切 | text overflow `...` 多発 / 主要列が幅 50px 以下 / table が viewport を 1.5 倍以上はみ出す |
| 要素の重なり / clipping (目視) | 隣接要素が物理的に重ならない / clip されない / 領域からはみ出ない | screenshot 目視で checkbox と label が重なる / アイコンが文字に被る / 親 container を子が overflow |
| 操作導線 | 主要 action (登録 / 編集 / 削除) が右上 / row 末尾など慣習位置にある | 同種 action が画面ごとに違う位置 / scroll 下端で見えない / icon-only で意図不明 |
| 空状態 | データ 0 件時に空状態 component (説明 + 主要 action) が表示される | 真っ白 / loading のまま / error 表示のみで次の行動が分からない |
| ローディング | データ取得中に skeleton / spinner が出る | 取得中も真っ白で UI が固まる / skeleton が永遠に残る |
| エラー表示 | API 4xx-5xx 時に toast / alert で原因が伝わる | silent fail / 英語生メッセージが露出 |

## §3 既存画面整合性観点

新規 / 改修した画面が、既に存在する隣接画面と同じ世界観で並ぶことを確認しろ。

**比較対象画面の選定優先順位** (上位から順に見て該当が無ければ次へ):

1. **同ロール・同ドメイン**: 同じロール (`member` / `admin` / `manager`) の同ドメイン他画面 (一覧に対する編集 / 詳細)
2. **同ロール**: 同じロール配下の別ドメイン画面
3. **全社共通**: layout / sidebar / topbar / shared dialog (ロール横断の共通土台)

| 項目 | 期待結果 | failure 検出条件 |
|---|---|---|
| 余白整合 | 比較対象と section / card padding が同値で並ぶ | キャプチャ並べで 1 段ズレが目視できる |
| 配色整合 | primary / accent / destructive の使い方が比較対象と揃う | 同じ意味の action なのに色が違う / 主要 action が outline と default で揺れる |
| action ボタン配置 | 「新規」「保存」「削除」の位置が比較対象と揃う | 比較対象は右上だが本画面は左下 / row 内 vs row 外で揺れる |
| 列構成 | table 列 (checkbox / 主要属性 / 操作列) の順序 / 幅が揃う | 比較対象は左端 checkbox + 右端 actions だが本画面は逆 |
| 空状態表現 | 空状態の illustration / コピー / 主要 action が揃う | 比較対象は「最初の◯◯を作成」だが本画面はテキストのみ |

比較対象画面を選んだら、レポートに「比較対象: `<path>`」を明記しろ。各項目で具体的に何と並べたかを残せ。
