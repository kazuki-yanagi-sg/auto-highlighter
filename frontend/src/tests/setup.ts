import "@testing-library/jest-dom";

// jsdom は PointerEvent を実装していないため、clientX/Y を運べる MouseEvent で代替する。
if (typeof window !== "undefined" && !("PointerEvent" in window)) {
  // @ts-expect-error テスト環境用の最小ポリフィル
  window.PointerEvent = window.MouseEvent;
}
if (!Element.prototype.setPointerCapture) {
  Element.prototype.setPointerCapture = () => {};
  Element.prototype.releasePointerCapture = () => {};
}
