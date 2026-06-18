---
name: create-video-howto
description: テロップ付き操作動画の手順書を作成する。Playwrightで画面操作を自動化し、DOMインジェクションでテロップと赤枠ハイライトを表示しながら動画を録画。「動画手順書」「操作動画」「ビデオチュートリアル」「テロップ付き手順」「動画マニュアル」などのキーワードで使用。
---

# テロップ付き操作動画の手順書作成スキル

Playwrightスタンドアロンスクリプトで、テロップと赤枠ハイライト付きの操作動画を自動生成するスキル。

## 技術的背景

Playwright MCP経由の動画録画は不可（プラグインシステムがargsを上書きするため）。
Node.jsからPlaywright APIを直接呼び出すスタンドアロンスクリプト方式のみが動作する。

---

## 視覚エフェクトの使い分け

| 操作タイプ | 赤枠ハイライト | テロップ | 例 |
|-----------|:------------:|:------:|-----|
| リンク・ボタンのクリック | ○ | - | サイドメニュー、送信ボタン |
| キーボード操作（F1等） | - | ○ | 「データ登録ボタンで入庫を登録します」 |
| 画面に見えない操作全般 | - | ○ | キーショートカット、API呼び出し待ち |
| シーンの大きな区切り | - | ○ | 「入庫実績を登録します」「在庫を確認します」 |
| フォーム入力 | - | - | 値の入力自体が画面に見える |

**原則: 画面を見れば分かる操作に説明は不要。見えない操作とシーン区切りだけテロップを出す。**

---

## フェーズ1: シナリオの認識合わせ（ユーザー承認必須）

### ステップ1-1: 画面構成の調査

シナリオ提示前に、関連する画面を調査する。

**調査方法:**
1. `client/messages/metadata/ja.json`で画面URL・画面名を確認
2. 必要に応じてExploreエージェントで画面構成を調査
3. 各画面でどんな操作ができるかを把握

### ステップ1-2: シナリオを表形式で提示

**操作の「意味の区切り」単位**でまとめる。1操作=1行ではなく、1つの目的=1行。

```markdown
| Step | テロップ | 操作内容 |
|------|---------|----------|
| 1 | ログインします | メールアドレス・パスワード入力 → ログインボタン |
| 2 | 入庫実績を登録します | サイドメニュー → 荷主検索 → 品番・数量入力 → F1で登録 |
| 3 | 在庫一覧で確認します | サイドメニュー → 荷主コード検索 → 在庫数確認 |
```

**NG例（細分化しすぎ）:**
```markdown
| 1 | ログイン画面を開きます | 画面表示 |
| 2 | メールアドレスを入力します | メアド入力 |
| 3 | パスワードを入力します | パスワード入力 |
| 4 | ログインボタンをクリック | ボタン押下 |
```
↑ これは4行ではなく「ログインします」の1行にまとめる。

**テロップルール:**
- UIDやシステムコードは使わない。ユーザーが理解できる表現にする
- テロップは短く。操作の「目的」を伝える

### ステップ1-3: ユーザー承認を得る

- ユーザーから「OK」等の承認コメントを得るまでシナリオを改善し続ける
- **承認なしで次のフェーズに進んではいけない**

---

## フェーズ2: シナリオのマークダウン化

### ステップ2-1: 出力ディレクトリ作成

```bash
TIMESTAMP=$(date +%Y%m%d%H%M%S)
SCENARIO_DIR=".tmp/videos/${TIMESTAMP}_{シナリオ名}"
mkdir -p "${SCENARIO_DIR}"
```

### ステップ2-2: シナリオファイルの作成

承認されたシナリオをマークダウンファイルとして保存:

```bash
# 保存先
${SCENARIO_DIR}/scenario.md
```

**内容:**
```markdown
# {シナリオタイトル}

## 概要
このシナリオでは〜を行います。

## 使用データ
| 項目 | 値 | 備考 |
|------|-----|------|
| 荷主 | （フェーズ3で埋める） | |
| 品番 | （フェーズ3で埋める） | |

## ステップ一覧
| Step | テロップ | 操作内容 | 使用データ |
|------|---------|----------|-----------|
| 1 | ログインします | メアド・パスワード入力 → ログイン | admin0@example.com |
| 2 | ... | ... | ... |

## 操作詳細
各ステップの具体的な操作手順（録画スクリプト生成用）:

### Step 1: ログインします
1. /login を開く
2. メールアドレス入力
3. パスワード入力
4. 「ログインする」クリック（赤枠ハイライト）

### Step 2: ...
```

---

## フェーズ3: データ構成確認

### ステップ3-1: DB接続情報の取得

```bash
cat api/.env | grep -E "POSTGRES_USER|POSTGRES_DB|POSTGRES_PORT"
```

**重要**: ポート番号は`.env`から取得すること（ハードコード禁止）

### ステップ3-2: シナリオに必要なデータの調査

```bash
docker compose exec -T db psql -U $POSTGRES_USER -d $POSTGRES_DB -p $POSTGRES_PORT -c "
  SELECT id, name, system_code FROM consignors WHERE system_code = '{荷主コード}';
"
```

必要に応じて品目データ、在庫データ等も確認:
```bash
docker compose exec -T db psql -U $POSTGRES_USER -d $POSTGRES_DB -p $POSTGRES_PORT -c "
  SELECT i.item_code, i.item_name FROM items i
  JOIN consignors c ON i.consignor_id = c.id
  WHERE c.system_code = '{荷主コード}'
  LIMIT 10;
"
```

### ステップ3-3: scenario.mdにデータを埋める

調査結果をもとに`scenario.md`の「使用データ」テーブルと各ステップの「使用データ」列を埋める。

### ステップ3-4: ファイルアップロードの確認

シナリオにファイルアップロードが含まれる場合:
- ユーザーからファイルを受け取っていなければ**必ず要求する**
- 受け取ったファイルは`${SCENARIO_DIR}/`に保存

---

## フェーズ4: 動画撮影

### ステップ4-1: Playwrightモジュールの解決

```bash
# npxキャッシュ内のplaywrightモジュールパスを取得
PLAYWRIGHT_PATH=$(find ~/.npm/_npx -name "playwright" -path "*/node_modules/playwright" -type d 2>/dev/null | head -1)
echo "${PLAYWRIGHT_PATH}/index.mjs"
```

モジュールが見つからない場合:
```bash
npx playwright@latest --version  # キャッシュを作成
```

### ステップ4-2: 録画スクリプトの生成

`scenario.md`の操作詳細をもとに、録画用Node.jsスクリプトを生成する。

**保存先:** `${SCENARIO_DIR}/record.mjs`

**テンプレート:** `.claude/skills/create-video-howto/templates/record-template.mjs`

**生成ルール:**
- 各操作をPlaywright APIで記述
- **クリック操作の前に`highlightElement(page, selector)`で赤枠表示** → クリック → `removeHighlight(page)`
- **キーボード操作やシーン区切りでは`injectCaption(page, text)`でテロップ表示**
- ページ遷移後は`waitForLoadState('networkidle')` + `waitForTimeout()`で安定を待つ
- テロップ表示後は`waitForTimeout(2000)`で読む時間を確保
- ハイライト表示後は`waitForTimeout(1500)`で視認時間を確保してからクリック
- `recordVideo`の`dir`はスクリプトと同じディレクトリを指定

### ステップ4-3: スクリプトの実行

```bash
node ${SCENARIO_DIR}/record.mjs
```

**エラー時の対応:**
- `Executable doesn't exist` → `channel: 'chrome'`を確認
- `Timeout exceeded` → セレクタを修正（`locator('a[href="..."]')`推奨）
- `Cannot find package` → ステップ4-1のパス解決を再確認

### ステップ4-4: 動画ファイルの整理

録画後、Playwrightが生成するランダムファイル名を分かりやすく変更:

```bash
# 最新のwebmファイルを特定してリネーム
mv ${SCENARIO_DIR}/*.webm ${SCENARIO_DIR}/{シナリオ名}.webm
```

---

## フェーズ5: 完成・確認

### ステップ5-1: 出力ディレクトリの案内

ユーザーに完成物の場所を案内:

```
完成しました。

出力ディレクトリ: .tmp/videos/{TIMESTAMP}_{シナリオ名}/
├── scenario.md    # シナリオ定義
├── record.mjs     # 録画スクリプト
└── {シナリオ名}.webm  # 操作動画
```

### ステップ5-2: 動画の再生

```bash
open ${SCENARIO_DIR}/{シナリオ名}.webm
```

---

## 録画スクリプトの技術仕様

### ブラウザ起動

```javascript
const browser = await chromium.launch({ headless: false, channel: 'chrome' });
const context = await browser.newContext({
  recordVideo: { dir: videoDir, size: { width: 1440, height: 900 } },
  viewport: { width: 1440, height: 900 },
});
const page = await context.newPage();
```

**重要: viewportサイズはmacOSの論理解像度（通常1440x900程度）以下にすること。**
画面より大きいviewportを指定するとブラウザウィンドウが収まらず、動画の下部が切れる。
`recordVideo.size`と`viewport`は必ず同じ値にする。

### テロップ注入関数

```javascript
async function injectCaption(page, text) {
  await page.evaluate((t) => {
    let el = document.getElementById('tutorial-caption');
    if (!el) {
      el = document.createElement('div');
      el.id = 'tutorial-caption';
      el.style.cssText =
        'position:fixed;bottom:80px;left:50%;transform:translateX(-50%);' +
        'background:rgba(0,0,0,0.85);color:white;padding:14px 28px;' +
        'font-size:24px;font-weight:bold;z-index:99999;border-radius:12px;' +
        'font-family:sans-serif;white-space:nowrap;' +
        'box-shadow:0 4px 12px rgba(0,0,0,0.3);';
      document.body.appendChild(el);
    }
    el.textContent = t;
    el.style.display = 'block';
  }, text);
}

async function hideCaption(page) {
  await page.evaluate(() => {
    const el = document.getElementById('tutorial-caption');
    if (el) el.style.display = 'none';
  });
}
```

### 赤枠ハイライト関数

```javascript
async function highlightElement(page, selector) {
  await page.evaluate((sel) => {
    const old = document.getElementById('tutorial-highlight');
    if (old) old.remove();

    const target = document.querySelector(sel);
    if (!target) return;

    const rect = target.getBoundingClientRect();
    const highlight = document.createElement('div');
    highlight.id = 'tutorial-highlight';
    highlight.style.cssText =
      'position:fixed;z-index:99998;pointer-events:none;' +
      'border:3px solid #FF4444;border-radius:6px;' +
      'box-shadow:0 0 0 4px rgba(255,68,68,0.3);' +
      'animation:highlight-pulse 0.8s ease-in-out infinite;';
    highlight.style.left = (rect.left - 4) + 'px';
    highlight.style.top = (rect.top - 4) + 'px';
    highlight.style.width = (rect.width + 8) + 'px';
    highlight.style.height = (rect.height + 8) + 'px';

    if (!document.getElementById('tutorial-highlight-style')) {
      const style = document.createElement('style');
      style.id = 'tutorial-highlight-style';
      style.textContent = '@keyframes highlight-pulse { 0%,100% { box-shadow:0 0 0 4px rgba(255,68,68,0.3); } 50% { box-shadow:0 0 0 8px rgba(255,68,68,0.5); } }';
      document.head.appendChild(style);
    }

    document.body.appendChild(highlight);
  }, selector);
}

async function removeHighlight(page) {
  await page.evaluate(() => {
    const el = document.getElementById('tutorial-highlight');
    if (el) el.remove();
  });
}
```

### 動画保存

```javascript
const videoPath = await page.video().path();
await context.close();  // これで動画が保存される
await browser.close();
```

### 操作パターン

```javascript
// クリック操作（赤枠ハイライト付き）
await highlightElement(page, 'a[href="/wm/receiving-records/new"]');
await page.waitForTimeout(1500);
await page.locator('a[href="/wm/receiving-records/new"]').click();
await removeHighlight(page);
await page.waitForLoadState('networkidle');
await page.waitForTimeout(2000);

// キーボード操作やボタンクリック（テロップ付き）
await injectCaption(page, '「データ登録」ボタンで入庫を登録します');
await page.waitForTimeout(2000);
await page.getByRole('button', { name: 'F1 データ登録' }).click();
await page.waitForTimeout(3000);
await hideCaption(page);

// シーンの区切り（テロップ付き）
await injectCaption(page, '在庫一覧で確認します');
await page.waitForTimeout(2000);
await hideCaption(page);

// ページ遷移（BASE_URL変数を使用）
await page.goto(`${BASE_URL}/login`);
await page.waitForLoadState('networkidle');
await page.waitForTimeout(2000);

// フォーム入力（エフェクトなし）
await page.getByPlaceholder('荷主コード').fill('31');
await page.waitForTimeout(1000);
```

---

## 既知の落とし穴と対策

### viewportサイズ

| 問題 | 原因 | 対策 |
|------|------|------|
| 動画の下部が切れる | viewportがmacOS画面の論理解像度より大きい | **1440x900以下**にする |
| テロップが見えない | `bottom`値が小さすぎて切れる | **`bottom:80px`以上**にする |
| F1ボタン等が見えない | viewportが小さすぎて横幅が足りない | **1440x900**が最適バランス |

### `page.evaluate()`内のセレクタ制約

`highlightElement`等の`page.evaluate()`内では**ネイティブCSS**のみ使用可能。Playwright拡張セレクタは使えない。

```javascript
// NG: :has-text() はPlaywright専用。document.querySelector()では SyntaxError
await highlightElement(page, 'button:has-text("F1 データ登録")');

// OK: ネイティブCSSセレクタのみ使用
await highlightElement(page, 'button[type="submit"]');
await highlightElement(page, 'a[href="/wm/inventories"]');
```

ハイライトできないボタン（テキストでしか特定できない等）は、ハイライトの代わりにテロップで説明する。

### AG Grid操作

AG Gridのスプレッドシートは独自のセル編集フローを持つ。

```javascript
// セレクタ: [role="gridcell"] input でグリッド内の編集中inputを取得
const cellInput = page.locator('[role="gridcell"] input').first();
await cellInput.fill('値');
await page.keyboard.press('Enter');  // 確定＆次セルへ自動フォーカス
```

**注意点:**
- `input[type="text"]` は**使用禁止** — グリッド外のinput（荷主コード等）にもマッチする
- `.ag-cell-editing input` は本プロジェクトのAG Gridバージョンでは動作しない
- 荷主検索後、1行目の品番セルが自動的に編集モードに入る
- `Enter`で値確定＆次セルへ自動フォーカス（品番→入庫数→入庫日→製造日の順）
- 日付セルにはデフォルト値（当日）が入っているため、`Enter`で確定するだけでよい
- **`Escape`は値をクリアするので使ってはいけない**

### トースト検知

```javascript
// NG: トーストのテキスト検知は不安定。表示タイミングやテキスト一致で失敗しやすい
await page.getByText('作成しました').waitFor({ timeout: 5000 });

// OK: 登録ボタンクリック後は単純にwaitForTimeoutで待つ
await page.getByRole('button', { name: 'F1 データ登録' }).click();
await page.waitForTimeout(3000);  // 登録処理の完了を待つ
```

トースト検知を成否判定のgateにしてはいけない。データは正常に登録されているのにトースト検知だけ失敗するケースがある。

### 複数回実行時の注意

録画スクリプトを複数回実行すると、同じディレクトリにwebmファイルが蓄積する。
リネーム前に古いwebmを削除すること:

```bash
# 古いwebmを全削除してからリネーム
rm -f ${SCENARIO_DIR}/*.webm  # 先に削除
node ${SCENARIO_DIR}/record.mjs
mv ${SCENARIO_DIR}/*.webm ${SCENARIO_DIR}/{シナリオ名}.webm
```

---

## チェックリスト

### フェーズ1: シナリオ認識合わせ
- [ ] 画面構成を調査したか
- [ ] 意味の区切り単位でシナリオを提示したか（細分化しすぎていないか）
- [ ] **ユーザーから承認を得たか（必須）**

### フェーズ2: シナリオのマークダウン化
- [ ] 出力ディレクトリを作成したか
- [ ] scenario.mdを作成したか

### フェーズ3: データ確認
- [ ] DB接続情報を`.env`から取得したか
- [ ] 必要なデータを調査したか
- [ ] scenario.mdに具体的なデータを埋めたか
- [ ] ファイルアップロードが必要な場合、ユーザーに要求したか

### フェーズ4: 動画撮影
- [ ] Playwrightモジュールのパスを解決したか
- [ ] 録画スクリプトを生成したか（赤枠ハイライト+テロップの使い分け）
- [ ] **viewportは1440x900以下か（macOS画面に収まるか）**
- [ ] スクリプトを実行して動画を生成したか
- [ ] 古いwebmファイルを削除してからリネームしたか

### フェーズ5: 完成
- [ ] 出力ディレクトリを案内したか
- [ ] **動画をブラウザで再生したか（必須）**
