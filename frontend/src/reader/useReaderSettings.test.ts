import { act, renderHook } from "@testing-library/react";
import { DEFAULT_SETTINGS, useReaderSettings } from "./useReaderSettings";

beforeEach(() => localStorage.clear());

test("既定値を返す", () => {
  const { result } = renderHook(() => useReaderSettings());
  expect(result.current[0]).toEqual(DEFAULT_SETTINGS);
});

test("更新すると反映され localStorage に保存される", () => {
  const { result } = renderHook(() => useReaderSettings());
  act(() => result.current[1]({ sheet: "dark", sizePx: 24 }));
  expect(result.current[0].sheet).toBe("dark");
  expect(result.current[0].sizePx).toBe(24);
  expect(JSON.parse(localStorage.getItem("sokudoku.reader.settings")!).sheet).toBe(
    "dark",
  );
});

test("保存済み設定を復元する", () => {
  localStorage.setItem(
    "sokudoku.reader.settings",
    JSON.stringify({ accent: "#e2714e" }),
  );
  const { result } = renderHook(() => useReaderSettings());
  expect(result.current[0].accent).toBe("#e2714e");
  // 欠けたキーは既定で補完
  expect(result.current[0].sizePx).toBe(DEFAULT_SETTINGS.sizePx);
});
