// テロップ+赤枠ハイライト付き操作動画 録画スクリプトテンプレート
// 使い方: scenario.md の操作詳細をもとに、{{STEPS}} 部分を生成する
//
// 置換変数:
//   {{PLAYWRIGHT_MODULE_PATH}} - npxキャッシュ内のplaywright/index.mjsのフルパス
//   {{VIDEO_DIR}}              - 動画出力ディレクトリのフルパス
//   {{BASE_URL}}               - アプリのベースURL（例: http://localhost:23100）
//   {{STEPS}}                  - ステップごとの操作コード

import { chromium } from '{{PLAYWRIGHT_MODULE_PATH}}';

const videoDir = '{{VIDEO_DIR}}';
const BASE_URL = '{{BASE_URL}}';

// --- テロップ: キーボード操作やシーン区切りで使用 ---
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

// --- 赤枠ハイライト: クリック対象要素を強調 ---
// 注意: selectorはネイティブCSSのみ使用可（:has-text()等のPlaywright拡張は不可）
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

(async () => {
  const browser = await chromium.launch({ headless: false, channel: 'chrome' });
  const context = await browser.newContext({
    recordVideo: { dir: videoDir, size: { width: 1440, height: 900 } },
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();

  // --- ここから自動生成ステップ ---
  {{STEPS}}
  // --- ここまで自動生成ステップ ---

  // 終了テロップ
  await injectCaption(page, '以上で操作手順は完了です');
  await page.waitForTimeout(3000);

  // 動画保存
  const videoPath = await page.video().path();
  await context.close();
  await browser.close();

  console.log(`Video saved to: ${videoPath}`);
})();
