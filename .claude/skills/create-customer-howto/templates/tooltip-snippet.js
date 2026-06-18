// 吹き出し追加スニペット
// browser_evaluate で実行する
//
// 使用方法:
// 1. セレクタを対象要素に変更
// 2. tooltip.innerHTML のテキストを変更
// 3. 色を用途に合わせて変更（赤:#dc2626, 緑:#16a34a, 青:#2563eb）

() => {
  // 既存の吹き出しを削除
  document.querySelectorAll('.custom-tooltip').forEach(el => el.remove());

  const element = document.querySelector('セレクタをここに');
  if (element) {
    const rect = element.getBoundingClientRect();
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.innerHTML = '① ここをクリック';
    tooltip.style.cssText = `
      position: fixed;
      background: #dc2626;
      color: white;
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 14px;
      font-weight: bold;
      z-index: 9999;
      box-shadow: 0 4px 6px rgba(0,0,0,0.2);
      top: ${rect.top - 45}px;
      left: ${rect.left}px;
    `;
    const arrow = document.createElement('div');
    arrow.style.cssText = `
      position: absolute;
      top: 100%;
      left: 20px;
      border: 8px solid transparent;
      border-top-color: #dc2626;
    `;
    tooltip.appendChild(arrow);
    document.body.appendChild(tooltip);
  }
}
