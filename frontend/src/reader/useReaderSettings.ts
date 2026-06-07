import { useCallback, useEffect, useState } from "react";

export interface ReaderSettings {
  sheet: "paper" | "dark"; // 読書面の色
  font: string; // 本文フォント(CSS font-family)
  sizePx: number; // 本文サイズ
  markerOpacity: number; // 蛍光ペンの濃さ 0..1
  accent: string; // テーマ色(hex)
}

export const DEFAULT_SETTINGS: ReaderSettings = {
  sheet: "paper",
  font: '"Newsreader", Georgia, serif',
  sizePx: 20,
  markerOpacity: 0.42,
  accent: "#f0a338",
};

const KEY = "marker.reader.settings";

function load(): ReaderSettings {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? { ...DEFAULT_SETTINGS, ...JSON.parse(raw) } : DEFAULT_SETTINGS;
  } catch {
    return DEFAULT_SETTINGS;
  }
}

export function useReaderSettings(): [
  ReaderSettings,
  (patch: Partial<ReaderSettings>) => void,
] {
  const [settings, setSettings] = useState<ReaderSettings>(load);

  useEffect(() => {
    try {
      localStorage.setItem(KEY, JSON.stringify(settings));
    } catch {
      // 保存できなくても致命的ではない
    }
  }, [settings]);

  const update = useCallback((patch: Partial<ReaderSettings>) => {
    setSettings((prev) => ({ ...prev, ...patch }));
  }, []);

  return [settings, update];
}
