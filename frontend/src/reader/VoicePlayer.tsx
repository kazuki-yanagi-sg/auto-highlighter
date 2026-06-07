import { useEffect, useRef, useState } from "react";
import { MARKER_COLORS, MARKER_LABELS, type MarkerColor } from "../types";

interface Props {
  documentId: number;
}

function fmt(sec: number): string {
  if (!Number.isFinite(sec)) return "0:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

// 右下に浮くカスタム音声プレーヤー。生の <audio controls> は使わず自前UIで操作する。
// 色を選ぶと、その色のマーカー文だけをサーバが逐次合成→ストリーミング再生する。
export function VoicePlayer({ documentId }: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [color, setColor] = useState<MarkerColor | null>(null);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [current, setCurrent] = useState(0);
  const [duration, setDuration] = useState(0);

  // 色が変わったら読み込んで再生する。
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !color) return;
    audio.load?.();
    Promise.resolve(audio.play?.())
      .then(() => setPlaying(true))
      .catch(() => setPlaying(false));
  }, [color]);

  function pick(next: MarkerColor) {
    setError(null);
    setCurrent(0);
    setColor(next);
  }

  function toggle() {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) {
      audio.pause?.();
      setPlaying(false);
    } else {
      Promise.resolve(audio.play?.()).then(() => setPlaying(true)).catch(() => {});
    }
  }

  function seek(ratio: number) {
    const audio = audioRef.current;
    if (!audio || !duration) return;
    audio.currentTime = ratio * duration;
    setCurrent(audio.currentTime);
  }

  const ratio = duration ? current / duration : 0;

  return (
    <div className="voice-dock">
      <div className="voice-colors">
        {MARKER_COLORS.map((c) => (
          <button
            key={c}
            className={`voice-chip marker-${c} ${color === c ? "on" : ""}`}
            onClick={() => pick(c)}
          >
            {MARKER_LABELS[c]}
          </button>
        ))}
      </div>

      <div className="voice-controls">
        <button
          className="voice-play"
          onClick={toggle}
          disabled={!color}
          aria-label={playing ? "一時停止" : "再生"}
        >
          {playing ? "⏸" : "▶"}
        </button>
        <span className="voice-time">{fmt(current)}</span>
        <input
          className="voice-seek"
          type="range"
          min={0}
          max={1}
          step={0.001}
          value={ratio}
          onChange={(e) => seek(Number(e.target.value))}
          aria-label="シーク"
        />
        <span className="voice-time">{fmt(duration)}</span>
      </div>

      {error && <p className="voice-error">{error}</p>}

      <audio
        ref={audioRef}
        data-testid="audio"
        src={color ? `/api/documents/${documentId}/tts?color=${color}` : undefined}
        onTimeUpdate={(e) => {
          setCurrent(e.currentTarget.currentTime);
          setDuration(e.currentTarget.duration || 0);
        }}
        onEnded={() => setPlaying(false)}
        onError={() => {
          setError("音声を再生できません(該当なし/失敗)");
          setPlaying(false);
        }}
      />
    </div>
  );
}
