import type { ReaderSettings } from "./useReaderSettings";

interface Props {
  settings: ReaderSettings;
  onChange: (patch: Partial<ReaderSettings>) => void;
  onClose: () => void;
}

const FONTS = [
  { label: "Newsreader（明朝系）", value: '"Newsreader", Georgia, serif' },
  { label: "ゴシック", value: '"Zen Kaku Gothic New", system-ui, sans-serif' },
];

const ACCENTS = ["#f0a338", "#e2714e", "#d9608f", "#7fae57"];

export function TweaksPanel({ settings, onChange, onClose }: Props) {
  return (
    <aside className="tweaks" aria-label="読書設定">
      <header className="tweaks-head">
        <span>Tweaks</span>
        <button onClick={onClose} aria-label="設定を閉じる">
          ×
        </button>
      </header>

      <div className="tweaks-row">
        <span className="tweaks-label">読書面</span>
        <div className="seg-toggle">
          <button
            className={settings.sheet === "paper" ? "on" : ""}
            onClick={() => onChange({ sheet: "paper" })}
          >
            紙
          </button>
          <button
            className={settings.sheet === "dark" ? "on" : ""}
            onClick={() => onChange({ sheet: "dark" })}
          >
            ダーク
          </button>
        </div>
      </div>

      <div className="tweaks-row">
        <label className="tweaks-label" htmlFor="tw-font">
          本文フォント
        </label>
        <select
          id="tw-font"
          value={settings.font}
          onChange={(e) => onChange({ font: e.target.value })}
        >
          {FONTS.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </select>
      </div>

      <div className="tweaks-row">
        <label className="tweaks-label" htmlFor="tw-size">
          本文サイズ <span className="tweaks-val">{settings.sizePx}px</span>
        </label>
        <input
          id="tw-size"
          type="range"
          min={15}
          max={28}
          step={1}
          value={settings.sizePx}
          onChange={(e) => onChange({ sizePx: Number(e.target.value) })}
        />
      </div>

      <div className="tweaks-row">
        <label className="tweaks-label" htmlFor="tw-mk">
          蛍光ペンの濃さ{" "}
          <span className="tweaks-val">{Math.round(settings.markerOpacity * 100)}%</span>
        </label>
        <input
          id="tw-mk"
          type="range"
          min={0.15}
          max={0.8}
          step={0.01}
          value={settings.markerOpacity}
          onChange={(e) => onChange({ markerOpacity: Number(e.target.value) })}
        />
      </div>

      <div className="tweaks-row">
        <span className="tweaks-label">テーマ色</span>
        <div className="swatches">
          {ACCENTS.map((a) => (
            <button
              key={a}
              className={`swatch ${settings.accent === a ? "on" : ""}`}
              style={{ background: a }}
              onClick={() => onChange({ accent: a })}
              aria-label={`テーマ色 ${a}`}
            />
          ))}
        </div>
      </div>
    </aside>
  );
}
