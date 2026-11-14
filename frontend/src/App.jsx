import { useState, useRef } from "react";

// Keys match backend/classifier.py: "clear_water", "sediment", "algae".
// "pollution" is included for when the classifier learns to detect trash.
const CLASSES = {
  clear_water: {
    label: "Clear Water", icon: "✅", color: "#22c55e",
    tip: "Water appears relatively clean. A photo can't reveal chemical or bacterial contamination, so test before drinking.",
  },
  sediment: {
    label: "Sediment-Heavy Water", icon: "🟤", color: "#d97706",
    tip: "Brown or red tones suggest suspended soil or silt. Filtration is recommended.",
  },
  algae: {
    label: "Algae Contamination", icon: "🟢", color: "#65a30d",
    tip: "Green tint detected. Possible algal bloom. Avoid contact and do not consume.",
  },
  pollution: {
    label: "Pollution / Trash Detected", icon: "🗑️", color: "#dc2626",
    tip: "Debris or pollution visible. Consider reporting it to local authorities.",
  },
};

const fallback = (key) => ({
  label: key ?? "Unknown", icon: "❓", color: "#64748b",
  tip: "No recommendation available.",
});

const pct = (x) => (x == null ? "–" : `${Math.round(x * 100)}%`);

const scoreColor = (s) => (s >= 75 ? "#22c55e" : s >= 50 ? "#eab308" : "#ef4444");

const HISTORY_KEY = "aquavision-history";
const MAX_HISTORY = 12;
const BLANK = "data:image/gif;base64,R0lGODlhAQABAAAAACwAAAAAAQABAAA=";

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY)) ?? [];
  } catch {
    return [];
  }
}

function saveHistory(list) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(list));
  } catch {
    /* storage full or blocked: history just won't persist */
  }
}

// Shrink the photo to a small square thumbnail so history stays tiny.
function makeThumb(file) {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const size = 96;
      const canvas = document.createElement("canvas");
      canvas.width = size;
      canvas.height = size;
      const k = Math.max(size / img.width, size / img.height);
      const w = img.width * k, h = img.height * k;
      canvas.getContext("2d").drawImage(img, (size - w) / 2, (size - h) / 2, w, h);
      URL.revokeObjectURL(url);
      resolve(canvas.toDataURL("image/jpeg", 0.7));
    };
    img.onerror = () => { URL.revokeObjectURL(url); resolve(null); };
    img.src = url;
  });
}

function Gauge({ score }) {
  const r = 70, c = 2 * Math.PI * r;
  const color = scoreColor(score);
  return (
    <div className="gauge">
      <svg viewBox="0 0 180 180">
        <circle cx="90" cy="90" r={r} className="gauge-bg" />
        <circle
          cx="90" cy="90" r={r} className="gauge-fg" stroke={color}
          strokeDasharray={c}
          strokeDashoffset={c - (Math.min(score, 100) / 100) * c}
          transform="rotate(-90 90 90)"
        />
      </svg>
      <div className="gauge-text">
        <span className="gauge-num" style={{ color }}>{Math.round(score)}</span>
        <span className="gauge-sub">/ 100</span>
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [drag, setDrag] = useState(false);
  const inputRef = useRef();
  const [history, setHistory] = useState(loadHistory);
  const [viewingSaved, setViewingSaved] = useState(false);

  const pick = (f) => {
    if (!f) return;
    setError(null);
    setResult(null);
    setFile(f);
    // AVIF can't always be previewed by the browser; fall back gracefully.
    setPreview(URL.createObjectURL(f));
  };

  const analyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const body = new FormData();
      body.append("image", file);
      const res = await fetch("/upload", { method: "POST", body });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || `Server returned ${res.status}`);
      setResult(data);

      const entry = {
        id: Date.now(),
        time: new Date().toISOString(),
        name: file.name,
        thumb: await makeThumb(file),
        result: data,
      };
      const next = [entry, ...history].slice(0, MAX_HISTORY);
      setHistory(next);
      saveHistory(next);
    } catch (e) {
      setError(e.message === "Failed to fetch"
        ? "Can't reach the backend. Is Flask running on port 5000?"
        : e.message);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setFile(null); setPreview(null); setResult(null); setError(null);
    setViewingSaved(false);
  };

  const openEntry = (entry) => {
    setFile(null);
    setError(null);
    setResult(entry.result);
    setPreview(entry.thumb || BLANK);
    setViewingSaved(true);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const clearHistory = () => {
    setHistory([]);
    saveHistory([]);
  };

  const cls = result ? CLASSES[result.classification] ?? fallback(result.classification) : null;

  return (
    <main className="app">
      <header>
        <h1>💧 AquaVision</h1>
        <p>AI-powered water quality analysis from a single photo</p>
      </header>

      {!preview && (
        <div
          className={`drop ${drag ? "drag" : ""}`}
          onClick={() => inputRef.current.click()}
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files[0]); }}
        >
          <div className="drop-icon">📷</div>
          <strong>Drop a water photo here</strong>
          <span>or click to browse (JPG, PNG, WEBP, AVIF)</span>
          <input
            ref={inputRef} type="file" hidden
            accept=".png,.jpg,.jpeg,.webp,.avif,image/*"
            onChange={(e) => pick(e.target.files[0])}
          />
        </div>
      )}

      {preview && (
        <section className="card">
          <img src={preview} alt="Water sample" className={viewingSaved ? "preview saved" : "preview"} />
          {!result && (
            <div className="actions">
              <button className="primary" onClick={analyze} disabled={loading}>
                {loading ? "Analyzing…" : "Analyze Water"}
              </button>
              <button className="ghost" onClick={reset} disabled={loading}>
                Change photo
              </button>
            </div>
          )}
        </section>
      )}

      {error && <div className="error">{error}</div>}

      {result && (
        <section className="card report">
          <h2>Water Quality Report</h2>
          <Gauge score={result.score} />
          <div className="badge" style={{ background: cls.color + "22", color: cls.color }}>
            {cls.icon} {cls.label}
          </div>

          <div className="conf">
            <div className="conf-label">
              <span>Confidence</span><span>{Math.round(result.confidence)}%</span>
            </div>
            <div className="conf-bar">
              <div style={{ width: `${result.confidence}%`, background: cls.color }} />
            </div>
          </div>

          <div className="rec">
            <strong>Recommendation</strong>
            <p>{cls.tip}</p>
          </div>

          <details className="features">
            <summary>Computer vision features</summary>
            <div className="stat-grid">
              <Stat label="Green coverage" value={pct(result.green_frac)} />
              <Stat label="Blue coverage" value={pct(result.blue_frac)} />
              <Stat label="Brown coverage" value={pct(result.brown_frac)} />
              <Stat label="Color variety" value={result.hue_entropy} />
              <Stat label="Debris specks" value={result.specks} />
              <Stat label="Brightness" value={result.brightness} />
              <Stat label="Resolution" value={`${result.width}×${result.height}`} />
              <Stat label="Avg R" value={result.red} />
              <Stat label="Avg G" value={result.green} />
              <Stat label="Avg B" value={result.blue} />
            </div>
          </details>

          <button className="primary" onClick={reset}>Analyze another photo</button>
        </section>
      )}

      {history.length > 0 && (
        <section className="history">
          <div className="history-head">
            <h3>Recent scans</h3>
            <button className="ghost small" onClick={clearHistory}>Clear</button>
          </div>
          {history.map((e) => {
            const c = CLASSES[e.result.classification] ?? fallback(e.result.classification);
            return (
              <button className="hist-item" key={e.id} onClick={() => openEntry(e)}>
                {e.thumb
                  ? <img src={e.thumb} alt="" />
                  : <span className="hist-ph">💧</span>}
                <div className="hist-info">
                  <strong style={{ color: c.color }}>{c.icon} {c.label}</strong>
                  <span>
                    {e.name} ·{" "}
                    {new Date(e.time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
                <span className="hist-score" style={{ color: scoreColor(e.result.score) }}>
                  {e.result.score}
                </span>
              </button>
            );
          })}
        </section>
      )}
    </main>
  );
}